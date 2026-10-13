#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AutoHotkey v2 受控试跑器 —— 真跑一遍脚本，但把运行期错误关进笼子。

解决的问题：
  * AHK 的**运行期错误永远走模态弹窗**，自动化流程会被卡死到天荒地老。
  * 解法：把目标脚本 `#Include` 进 `try { ... }` 里（v2 支持，已实测）。
    运行期异常被 catch 住 → 打印到标准输出 → 进程主动退出，全程无弹窗。
  * 同时 `#Warn All, StdOut` 把加载期警告也导向标准输出（否则一样会弹框）。
  * 外层再加超时强杀兜底：脚本驻留（注册了热键/定时器）时不会永远挂着。

退出码：0 脚本干净跑完或正常驻留 / 1 运行期错误 / 2 加载期错误 / 3 环境错误
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ahk_check import find_ahk, get_exe_version, _kill_tree, ERR_RE  # noqa: E402

TARGET_VERSION = "2.0"
SENTINEL = "AHK-RUNTIME-ERROR"

WRAPPER = """#Requires AutoHotkey v{ver}
#Warn All, StdOut
try
{{
    #Include "{target}"
}}
catch as __ahkrun_e
{{
    __ahkrun_s := "{sentinel}`n"
    __ahkrun_s := __ahkrun_s "type="    Type(__ahkrun_e)      "`n"
    __ahkrun_s := __ahkrun_s "what="    __ahkrun_e.What       "`n"
    __ahkrun_s := __ahkrun_s "message=" __ahkrun_e.Message    "`n"
    __ahkrun_s := __ahkrun_s "file="    __ahkrun_e.File       "`n"
    __ahkrun_s := __ahkrun_s "line="    __ahkrun_e.Line       "`n"
    __ahkrun_s := __ahkrun_s "extra="   __ahkrun_e.Extra      "`n"
    FileAppend(__ahkrun_s, "*")
    ExitApp(1)
}}
"""


def parse_runtime_error(text: str) -> dict | None:
    if SENTINEL not in text:
        return None
    tail = text.split(SENTINEL, 1)[1]
    info = {}
    for key in ("type", "what", "message", "file", "line", "extra"):
        m = re.search(rf"^{key}=(.*)$", tail, re.M)
        if m:
            info[key] = m.group(1).strip()
    return info


def decode_ahk(raw: bytes) -> str:
    """AHK 的两路输出编码不一样，得分别处理：
      * 报错文本受 /ErrorStdOut=UTF-8 控制 → UTF-8
      * 脚本里 `FileAppend(..., "*")` 写标准输出 → **系统 ANSI 码页**（简中是 GBK）
    所以先按 UTF-8 解，出现替换字符再按系统码页重解。
    """
    txt = raw.decode("utf-8", "replace")
    if "\ufffd" in txt:
        for enc in ("mbcs", "gbk", "cp936"):
            try:
                alt = raw.decode(enc)
            except (LookupError, UnicodeDecodeError):
                continue
            # 取"更少乱码"的那个
            if alt.count("\ufffd") < txt.count("\ufffd"):
                return alt
    return txt


def main() -> int:
    ap = argparse.ArgumentParser(
        description="AutoHotkey v2 受控试跑（try/catch 捕获运行期错误，无弹窗，超时强杀）")
    ap.add_argument("script", help="要试跑的 .ahk 文件")
    ap.add_argument("script_args", nargs="*",
                    help="传给脚本的参数，会出现在脚本的 A_Args 里。"
                         "用于跑脚本自带的 test 入口，例如 `ahk_run.py foo.ahk test`")
    ap.add_argument("--timeout", type=float, default=6.0,
                    help="最长观察秒数（默认 6）。超时说明脚本在正常驻留，会被强制结束")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    target = Path(args.script)
    if not target.is_file():
        print(f"[致命] 文件不存在：{target}")
        return 3
    target = target.resolve()
    ahk = find_ahk()
    ver = get_exe_version(ahk)

    wrap = None
    for d in (target.parent, Path(tempfile.gettempdir())):
        cand = d / f".ahkrun_{os.getpid()}_{target.stem}.ahk"
        try:
            cand.write_text(
                WRAPPER.format(ver=TARGET_VERSION, target=target, sentinel=SENTINEL),
                encoding="utf-8-sig", newline="",
            )
            wrap = cand
            break
        except OSError:
            continue
    if wrap is None:
        print("[致命] 无法写入试跑包装脚本")
        return 3

    started = time.time()
    out = err = ""
    try:
        p = subprocess.Popen(
            # /ErrorStdOut=UTF-8：让加载期报错按 UTF-8 输出，保留中文原始信息
            # script_args 追加在最后，脚本内用 A_Args[1] 即可读到
            [ahk, "/ErrorStdOut=UTF-8", str(wrap), *args.script_args],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(target.parent),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        try:
            o, e = p.communicate(timeout=args.timeout)
            rc, resident = p.returncode, False
        except subprocess.TimeoutExpired:
            _kill_tree(p.pid)
            o, e = p.communicate()
            rc, resident = None, True
        out = decode_ahk(o)
        err = decode_ahk(e)
    finally:
        try:
            wrap.unlink()
        except OSError:
            pass

    elapsed = round(time.time() - started, 2)
    rt = parse_runtime_error(out)
    load_err = [
        dict(line=int(m.group("line")), msg=m.group("msg").strip(),
             detail=(err.splitlines()[i + 1].split("Specifically:", 1)[1].strip()
                     if i + 1 < len(err.splitlines()) and "Specifically:" in err.splitlines()[i + 1] else ""))
        for i, ln in enumerate(err.splitlines()) if (m := ERR_RE.match(ln.strip()))
    ]
    clean_out = "\n".join(l for l in out.splitlines() if l.strip() and l.strip() != SENTINEL
                          and not re.match(r"^(type|what|message|file|line|extra)=", l.strip()))

    if rt:
        status, code = "runtime-error", 1
    elif load_err:
        status, code = "load-error", 2
    elif resident:
        status, code = "resident", 0
    else:
        status, code = "completed", 0

    if args.json:
        print(json.dumps(dict(script=str(target), status=status, exit_code=rc,
                              elapsed_s=elapsed, runtime_error=rt, load_errors=load_err,
                              stdout=clean_out, stderr=err.strip()),
                         ensure_ascii=False, indent=2))
    else:
        label = {"completed": "✅ 脚本跑完自行退出",
                 "resident": f"✅ 脚本仍在驻留（正常：注册了热键/定时器），已在 {args.timeout}s 后终止",
                 "runtime-error": "❌ 运行期错误",
                 "load-error": "❌ 加载期错误（语法/指令问题）"}[status]
        print(f"试跑 {target}\n解释器 v{ver}   用时 {elapsed}s   退出码 {rc}")
        print(f"  {label}")
        if rt:
            print(f"      类型：{rt.get('type') or '?'}")
            if rt.get("what"):
                print(f"      出错于：{rt['what']}")
            print(f"      信息：{rt.get('message', '?')}")
            print(f"      位置：{rt.get('file', '?')} 第 {rt.get('line', '?')} 行")
            if rt.get("extra"):
                print(f"      附加：{rt['extra']}")
        for e_ in load_err:
            print(f"      ❌ L{e_['line']} {e_['msg']}")
        if clean_out:
            print("  —— 脚本输出 ——")
            for line in clean_out.splitlines():
                print(f"    {line}")
        if err.strip() and not load_err:
            print(f"  —— stderr ——\n    {err.strip()}")

    return code


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
