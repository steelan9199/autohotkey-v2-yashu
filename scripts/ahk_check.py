#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AutoHotkey v2 脚本校验器 —— 静态规则检查 + 官方解释器语法校验，全程零副作用、零弹窗。

设计依据（均为 AHK v2.0.26 本机实测 + 源码核对结论）：
  1. 官方校验开关：`AutoHotkey.exe /ErrorStdOut /validate <脚本>`，只加载不执行。
     返回码 0 = 通过；2 = 加载期错误（语法错误会写到 stderr，格式为 `文件 (行) : ==> 说明`）。
  2. **加载期「警告」类问题会绕过 /ErrorStdOut 去弹模态框**（源码 error.cpp 中
     `aErrorType != WARN` 的判断），会把自动化流程卡死。因此用包装脚本把
     `#Warn All, StdOut` 前置，把警告重定向到标准输出。
  3. 包装脚本写在目标脚本**同目录**，保证目标内部的相对 `#Include` 能正确解析。
  4. 任何分支都带超时强杀，绝不留下残留进程或卡住的弹窗。
  5. 官方校验抓不到两类 v1 遗留写法：`. ` 点号拼接（2.0 仍能跑）和 v1 旧函数名
     （只报警告不报错）。这些由本脚本的静态规则补上。

退出码：0 通过 / 1 有错误 / 2 仅警告且指定了 --strict / 3 环境或内部错误
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TARGET_VERSION = "2.0"

# ------------------------------------------------------------------ 解释器

CANDIDATES = [
    r"C:\Program Files\AutoHotkey\v2\AutoHotkey.exe",
    r"C:\Program Files (x86)\AutoHotkey\v2\AutoHotkey.exe",
    r"C:\Program Files\AutoHotkey\AutoHotkey.exe",
]


def get_exe_version(path: str) -> str:
    """用 Win32 版本 API 读 exe 文件版本，不启动进程、不弹窗。"""
    try:
        size = ctypes.windll.version.GetFileVersionInfoSizeW(path, None)
        if not size:
            return "?"
        buf = ctypes.create_string_buffer(size)
        if not ctypes.windll.version.GetFileVersionInfoW(path, 0, size, buf):
            return "?"
        r = ctypes.c_void_p()
        ln = ctypes.c_uint()
        if not ctypes.windll.version.VerQueryValueW(buf, "\\", ctypes.byref(r), ctypes.byref(ln)):
            return "?"
        # VS_FIXEDFILEINFO 前 4 个 DWORD 依次是：签名、结构版本、FileVersionMS、FileVersionLS
        f = ctypes.cast(r, ctypes.POINTER(ctypes.c_uint32 * 4)).contents
        ms, ls = f[2], f[3]
        return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"
    except Exception:
        return "?"


def find_ahk() -> str:
    env = os.environ.get("AHK_EXE")
    if env and Path(env).is_file():
        return env
    for c in CANDIDATES:
        if Path(c).is_file():
            return c
    for base in (
        os.environ.get("LOCALAPPDATA", "") + r"\Programs\AutoHotkey",
        os.environ.get("ProgramFiles", "") + r"\AutoHotkey",
    ):
        p = Path(base) / "v2" / "AutoHotkey.exe"
        if p.is_file():
            return str(p)
    w = shutil.which("AutoHotkey.exe") or shutil.which("AutoHotkey")
    if w:
        return w
    print("[致命] 找不到 AutoHotkey v2 解释器。请安装 v2，或设置环境变量 AHK_EXE 指向 AutoHotkey.exe。")
    raise SystemExit(3)


# ------------------------------------------------------------------ 规则表

# v1 指令在 v2 中已被移除（改成函数或内置变量）—— 全部经源码核查确认
V1_DIRECTIVES = {
    "NoEnv": "v2 不再自动展开环境变量，直接删掉这一行",
    "Persistent": "改用函数 Persistent()",
    "KeyHistory": "改用函数 KeyHistory(0)（v2 没有 A_KeyHistory 变量）",
    "InstallKeybdHook": "改用函数 InstallKeybdHook()",
    "InstallMouseHook": "改用函数 InstallMouseHook()",
    "MaxHotkeysPerInterval": "改用内置变量 A_MaxHotkeysPerInterval",
    "HotkeyInterval": "改用内置变量 A_HotkeyInterval",
    "MenuMaskKey": "改用内置变量 A_MenuMaskKey",
    "DefaultMouseSpeed": "改用函数 SetDefaultMouseSpeed()",
    "HotkeyModifierTimeout": "改用内置变量 A_HotkeyModifierTimeout",
    "Delay": "改用 SetKeyDelay / SetMouseDelay / SetWinDelay",
    "If": "改用 #HotIf",
    "IfWinActive": "改用 #HotIf WinActive(...)",
    "CommentFlag": "v2 已移除（注释固定为分号）",
    "EscapeChar": "v2 已移除（反引号 ` 是唯一转义符）",
    "MaxMem": "v2 已移除",
    "AllowSameLineComments": "v2 已移除",
    "LTrim": "v2 已移除（改用 LTrim 函数）",
}

# v1 旧函数名 -> v2 正确写法。这些名字**已逐个对照 342 个 v2 内建函数全集核实过**，
# 确认在 v2 中不存在；否则会被官方校验器漏过（只报警告）。
V1_FUNCS = {
    "StringReplace": "StrReplace",
    "StringSplit": "StrSplit",
    "StringLen": "StrLen",
    "StringLeft": "SubStr",
    "StringRight": "SubStr",
    "StringMid": "SubStr",
    "StringTrimLeft": "LTrim / SubStr",
    "StringTrimRight": "RTrim",
    "StringLower": "StrLower",
    "StringUpper": "StrUpper",
    "StringGetPos": "InStr",
    "StringCaseSense": "StrCompare 的 CaseSense 参数",
    "IfWinExist": 'WinExist("...")',
    "IfWinActive": 'WinActive("...")',
    "IfExist": "FileExist / DirExist",
    "FileReadLine": "FileRead 或 Loop Read",
    "SetEnv": "普通赋值 :=",
    "EnvAdd": "+= 运算符",
    "EnvSub": "-= 运算符",
    "Transform": "v2 已移除，按用途改用对应函数",
    "URLDownloadToFile": "Download",
    "ComObjCreate": "ComObject",
    "WinGet": "WinGetTitle / WinGetPos / WinGetClass / WinGetList",
    "ControlGet": "ControlGetText / ControlGetPos / ...",
    "GuiControl": "v2 的 Gui 对象方法",
    "GuiControlGet": "v2 的 Gui 对象方法",
    "Menu": "MenuBar / Menu 对象",
}

# v1 的「语句型」关键字，在 v2 里已不存在
V1_STATEMENTS = [
    "IfExist", "IfNotExist", "IfWinExist", "IfWinNotExist", "IfWinActive", "IfWinNotActive",
    "IfMsgBox", "IfGreater", "IfGreaterOrEqual", "IfLess", "IfLessOrEqual", "IfEqual",
    "IfNotEqual", "IfInString", "IfNotInString", "IfBetween", "IfIs",
    "Gosub", "Goto", "SetEnv", "EnvAdd", "EnvSub", "AutoTrim",
]

# 真正会**阻塞**的模态窗口：脚本会停在那里等人点击（无人值守场景必须避免）
BLOCKING_DIALOGS = ("MsgBox", "InputBox", "FileSelect", "DirSelect")

# 会打开**信息窗口**的函数：不是模态，但无人值守时同样会把这条线程占住，
# 直到有人把窗口关掉（实测 ListLines() 无参调用即如此）
INFO_WINDOWS = ("ListLines", "ListVars", "ListHotkeys", "KeyHistory")

# 不是函数调用的关键字，出现在“名字(”形态里要排除
KEYWORDS = {
    "if", "else", "while", "for", "loop", "switch", "case", "default", "try", "catch",
    "finally", "return", "break", "continue", "throw", "global", "local", "static",
    "class", "new", "not", "and", "or", "is", "in", "until", "then", "goto", "gosub",
}


def load_api_names() -> set[str]:
    """从 references/api-index.md 读出全部已核验的内建函数名。"""
    api = Path(__file__).resolve().parent.parent / "references" / "api-index.md"
    if not api.is_file():
        return set()
    names = set()
    for line in api.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Za-z_]\w*)\(", line.strip())
        if m:
            names.add(m.group(1))
    return names


def collect_defined(lines: list[str]) -> set[str]:
    """收集脚本自己定义/赋值的名字，避免把用户自定义函数误判成写错。"""
    defined: set[str] = set()
    for idx, raw in enumerate(lines):
        code = _strip_comment(raw).strip()
        if not code:
            continue
        # 类定义： class Name {  /  class Name extends Base {
        m = re.match(r"^class\s+(\w+)", code)
        if m:
            defined.add(m.group(1))
        # 函数/方法定义：  Name(...) {  /  static Name(...) {  /  Name(...) => 表达式
        m = re.match(r"^(?:static\s+|class\s+)?(\w+)\s*\(", code)
        if m:
            if re.search(r"\)\s*\{\s*$", code) or re.search(r"\)\s*=>", code):
                defined.add(m.group(1))
            else:
                # Allman 风格：Name(...) 独占一行，下一行以 { 开头
                nxt = _strip_comment(lines[idx + 1]).strip() if idx + 1 < len(lines) else ""
                if nxt.startswith("{"):
                    defined.add(m.group(1))
        # 赋值目标： ident :=  /  ident +=  等（可能是函数对象）
        for a in re.finditer(r"(?:^|[,(\s])(\w+)\s*(?::=|\+=|-=|\.=)", code):
            defined.add(a.group(1))
        # 变量声明与标签
        m = re.match(r"^(?:global|local|static)\s+([\w,\s]+)$", code)
        if m:
            defined.update(x.strip() for x in m.group(1).split(","))
        m = re.match(r"^([\w.]+)\s*:$", code)
        if m:
            defined.add(m.group(1))
    return defined


def api_lint(text: str, api_names: set[str]) -> list[dict]:
    """把脚本里所有“名字(”调用点拿出来，比对权威函数表。
    查不到的名字极可能是 V1 旧名或编造的名字（官方校验器只报警告，抓不住）。"""
    if not api_names:
        return []
    lines = mask_multiline_strings(text.splitlines())
    defined = collect_defined(lines)
    hints, seen = [], set()
    for i, code in enumerate(lines, 1):
        if not code.strip() or code.lstrip().startswith("#"):
            continue
        for m in re.finditer(r"(?<![\w.$])([A-Za-z_]\w*)\s*\(", code):
            name = m.group(1)
            if name in api_names or name in defined or name in KEYWORDS or name in seen:
                continue
            seen.add(name)
            hints.append(dict(level="hint", line=i, rule="unknown-name",
                              msg=f"`{name}(` 不在 v2 内建函数表里，也不是本脚本定义的（函数/类/变量都没声明过）"
                                  f" —— 很可能是 V1 旧名或拼错，去 references/api-index.md 核对一次"))
    return hints



def _strip_comment(line: str) -> str:
    """去掉行尾注释；只在分号位于字符串之外时才截断。"""
    out, in_str, i = [], False, 0
    while i < len(line):
        ch = line[i]
        if ch == '"':
            in_str = not in_str
        elif ch == "`" and i + 1 < len(line):
            out.append(line[i:i + 2]); i += 2; continue
        elif ch == ";" and not in_str:
            break
        out.append(ch)
        i += 1
    return "".join(out)


def mask_multiline_strings(lines: list[str]) -> list[str]:
    """把 AHK 的**多行字符串字面量**内容行抹掉。

    写法长这样（开引号独占行尾，闭引号以 `)` 开头）：

        PS := "
        (
        Add-Type -AssemblyName System.Drawing
        [DllImport(\"user32.dll\")] ...
        )"

    里面的内容是 SQL / HTML / PowerShell 载荷，**不是 AHK 代码**。
    不抹掉的话，`FromImage(`、`PrintWindow(` 这类会全被当成"函数名写错"报出来（实测误报）。
    """
    out: list[str] = []
    in_block = False
    for raw in lines:
        code = _strip_comment(raw)
        if in_block:
            if code.lstrip().startswith(")"):
                in_block = False            # 闭引号行，恢复按代码解析
                out.append(code)
            else:
                out.append("")              # 字符串内容：整体忽略
            continue
        # 引号数为奇数 = 字符串跨行了，下一行起进入内容区
        if code.count('"') % 2 == 1:
            in_block = True
        out.append(code)
    return out


def static_lint(text: str) -> list[dict]:
    """静态规则检查：专门覆盖官方校验器抓不到的盲区。"""
    issues: list[dict] = []
    for i, code in enumerate(mask_multiline_strings(text.splitlines()), 1):
        code = code.strip()
        if not code:
            continue

        def add(level, rule, msg):
            issues.append(dict(level=level, line=i, rule=rule, msg=msg))

        # 1) v1 指令
        m = re.match(r"#(\w+)", code)
        if m and m.group(1) in V1_DIRECTIVES:
            add("error", "v1-directive",
                f"`#{m.group(1)}` 在 v2 中不存在 —— {V1_DIRECTIVES[m.group(1)]}")

        # 2) v1 命令式逗号语法：  MsgBox, "x"   /   Send, "x"
        m = re.match(r"([A-Za-z_]\w*)\s*,", code)
        if m:
            hint = V1_FUNCS.get(m.group(1), f"{m.group(1)}(...)")
            add("error", "v1-command-comma",
                f"v1 命令式写法 `{m.group(1)}, ...` —— v2 是函数，应写 `{hint}`")

        # 3) v1 单等号赋值
        if re.match(r"[A-Za-z_]\w*\s*=[^=]", code):
            add("error", "v1-assign", "v1 赋值 `x = 值` —— v2 必须写 `x := 值`")

        # 4) v1 旧函数名（官方校验器只会报警告，容易漏过）
        for old, new in V1_FUNCS.items():
            if re.search(rf"\b{old}\s*\(", code):
                add("error", "v1-function",
                    f"`{old}()` 不是 v2 函数 —— 改用 `{new}`")

        # 5) v1 语句关键字
        for kw in V1_STATEMENTS:
            if re.match(rf"{kw}\b", code):
                add("error", "v1-statement",
                    f"`{kw}` 是 v1 语句，v2 中不存在 —— 改用对应的函数写法")

        # 6) ErrorLevel 机制
        if re.search(r"\bErrorLevel\b", code):
            add("warn", "errorlevel",
                "v2 取消了 ErrorLevel 全局变量 —— 改为接收函数返回值，或用 try/catch 捕获异常")

        # 7) 点号拼接：v2.0 仍能跑，但已废弃（v2.1 移除），官方校验器抓不到。
        # 判据：一个"非空白的操作数" + 空白 + `.` + 空白 + 字符串字面量。
        # 这样既不会误判 `obj.Prop`（点号两边没有空格），也不会误判小数 `1.5`（后面不是引号）。
        if re.search(r"""[\w)\]"']\s+\.\s+["']""", code):
            add("warn", "dot-concat",
                '点号 `.` 是 v1 拼接符（v2.0 能跑但已废弃，v2.1 移除）—— '
                '改用空格隐式拼接：`"a" "b"`；要追加就写 `x := x "b"`')

        # 8) 会阻塞自动化的模态弹窗
        for c in BLOCKING_DIALOGS:
            if re.search(rf"\b{c}\s*[(\s]", code):
                add("warn", "blocking-dialog",
                    f"`{c}` 会弹出模态窗口，脚本会卡住等人工点击 —— 无人值守场景建议改用 "
                    f"TrayTip / OutputDebug / FileAppend 记录，或直接删掉")
                break

        # 8b) 会开信息窗口的调试函数（非模态，但同样会占住线程直到窗口被关掉）
        for c in INFO_WINDOWS:
            if re.search(rf"\b{c}\s*\(", code):
                add("warn", "info-window",
                    f"`{c}()` 会打开一个信息窗口并占住线程，直到有人关掉它 —— "
                    f"无人值守运行时会卡死；调试完记得删掉，或改用 FileAppend 写日志")
                break

        # 9) 自定义界面（本 skill 定位不需要）
        if re.search(r"\bGui\s*\(|\bGui\.", code):
            add("warn", "gui",
                "检测到自定义界面（Gui）—— 本 skill 定位为无人值守自动化，不需要界面")

    return issues


def encoding_lint(path: Path) -> list[dict]:
    """AHK v2 按 UTF-8 读脚本（源码 globaldata.cpp: g_DefaultScriptCodepage = CP_UTF8），
    非 UTF-8 文件里的中文会变成乱码。"""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return []
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return [dict(level="error", line=0, rule="encoding",
                     msg="文件不是 UTF-8 编码（疑似 GBK/ANSI）。AHK v2 一律按 UTF-8 读取脚本，"
                         "中文会变乱码 —— 请另存为 UTF-8（推荐带 BOM）")]
    return []


def requires_lint(text: str) -> list[dict]:
    if not re.search(r"^\s*#Requires\s+AutoHotkey\s+v2", text, re.M):
        return [dict(level="warn", line=0, rule="missing-requires",
                     msg="建议加上 `#Requires AutoHotkey v2.0`：能让 v1 解释器直接拒绝运行，"
                         "避免脚本被 v1 静默误跑（那样会出现一堆莫名其妙的语法错误）")]
    return []


# ------------------------------------------------------------------ 官方校验

ERR_RE = re.compile(r"^(?P<file>.+?) \((?P<line>\d+)\)\s*:\s*==>\s*(?P<msg>.+?)\s*$")


def _kill_tree(pid: int) -> None:
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                   capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)


def run_validate(ahk: str, target: Path, timeout: int = 30) -> dict:
    """包装脚本 + /ErrorStdOut /validate，做官方语法校验（不执行脚本）。"""
    target = target.resolve()
    wrap = None
    for d in (target.parent, Path(tempfile.gettempdir())):
        cand = d / f".ahkcheck_{os.getpid()}_{target.stem}.ahk"
        try:
            cand.write_text(
                f"#Requires AutoHotkey v{TARGET_VERSION}\r\n"
                "#Warn All, StdOut\r\n"
                f'#Include "{target}"\r\n',
                encoding="utf-8-sig", newline="",
            )
            wrap = cand
            break
        except OSError:
            continue
    if wrap is None:
        return dict(status="internal-error", detail="无法写入包装脚本（目标目录与临时目录都不可写）")

    try:
        p = subprocess.Popen(
            # /ErrorStdOut=UTF-8 让报错信息按 UTF-8 写；默认按系统 ANSI(GBK) 写，
            # 回显含中文的出错行时会变成乱码（实测）。
            [ahk, "/ErrorStdOut=UTF-8", "/validate", str(wrap)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            cwd=str(target.parent),
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        try:
            out, err = p.communicate(timeout=timeout)
            rc = p.returncode
        except subprocess.TimeoutExpired:
            _kill_tree(p.pid)
            p.communicate()
            return dict(status="timeout",
                        detail=f"校验超时（{timeout}s）：通常是有模态窗口在等待点击，已强制终止进程")
        return dict(status="ok" if rc == 0 else "failed", rc=rc,
                    stdout=out.decode("utf-8", "replace").strip(),
                    stderr=err.decode("utf-8", "replace").strip())
    finally:
        try:
            wrap.unlink()
        except OSError:
            pass


def parse_official(raw: str) -> list[dict]:
    """解析 `文件 (行) : ==> 说明` 形式的官方报错/警告。"""
    issues, lines = [], raw.splitlines()
    for i, ln in enumerate(lines):
        m = ERR_RE.match(ln.strip())
        if not m:
            continue
        is_warn = "Warning:" in m.group("msg")
        detail = ""
        if i + 1 < len(lines) and "Specifically:" in lines[i + 1]:
            detail = lines[i + 1].split("Specifically:", 1)[1].strip()
        issues.append(dict(
            level="warning" if is_warn else "error",
            line=int(m.group("line")),
            rule="ahk-official",
            msg=m.group("msg").replace("Warning: ", "").strip(),
            detail=detail,
        ))
    return issues


# ------------------------------------------------------------------ main

def main() -> int:
    ap = argparse.ArgumentParser(
        description="AutoHotkey v2 脚本校验器（静态检查 + 官方解释器校验，无弹窗、无副作用）")
    ap.add_argument("script", nargs="?", help="要校验的 .ahk 文件")
    ap.add_argument("--strict", action="store_true", help="把警告也视为失败（推荐用于交付前把关）")
    ap.add_argument("--no-lint", action="store_true", help="只跑官方校验，跳过静态规则")
    ap.add_argument("--no-api-check", action="store_true",
                    help="跳过“函数名是否在权威函数表里”的核对")
    ap.add_argument("--json", action="store_true", help="输出 JSON（便于程序消费）")
    ap.add_argument("--timeout", type=int, default=30, help="官方校验超时秒数，默认 30")
    ap.add_argument("--doctor", action="store_true", help="只检查环境：解释器路径、版本、自检")
    args = ap.parse_args()

    ahk = find_ahk()
    ver = get_exe_version(ahk)

    if args.doctor:
        tmp = Path(tempfile.gettempdir()) / f".ahkdoc_{os.getpid()}.ahk"
        tmp.write_text(f"#Requires AutoHotkey v{TARGET_VERSION}\r\nx := 1\r\n",
                       encoding="utf-8-sig", newline="")
        r = run_validate(ahk, tmp, timeout=args.timeout)
        tmp.unlink(missing_ok=True)
        print(f"解释器 : {ahk}")
        print(f"版本   : {ver}")
        print(f"自检   : {r['status']}" + (f"  ({r.get('detail', '')})" if r["status"] != "ok" else "  ✅"))
        if not ver.startswith("2.0"):
            print(f"⚠️  本 skill 只覆盖 v2.0.x 语法（当前 {ver}）。"
                  f"若为 2.1.x，部分写法（如 `.` 拼接、`_` 部分参数）行为不同，需另行核对。")
        return 0 if r["status"] == "ok" else 3

    if not args.script:
        ap.error("需要给出 .ahk 文件路径（或使用 --doctor）")
    target = Path(args.script)
    if not target.is_file():
        print(f"[致命] 文件不存在：{target}")
        return 3

    text = target.read_text(encoding="utf-8", errors="replace")
    issues: list[dict] = []
    if not args.no_lint:
        issues += encoding_lint(target)
        issues += requires_lint(text)
        issues += static_lint(text)
        if not args.no_api_check:
            issues += api_lint(text, load_api_names())

    official_raw = ""
    if not any(i["rule"] == "encoding" for i in issues):
        res = run_validate(ahk, target, timeout=args.timeout)
        if res["status"] in ("timeout", "internal-error"):
            issues.append(dict(level="error", line=0, rule="ahk-" + res["status"],
                               msg=res.get("detail", "未知内部错误")))
        else:
            official_raw = "\n".join(x for x in (res.get("stderr"), res.get("stdout")) if x)
            issues += parse_official(official_raw)

    errors = [i for i in issues if i["level"] == "error"]
    warns = [i for i in issues if i["level"] == "warn" or i["level"] == "warning"]
    hints = [i for i in issues if i["level"] == "hint"]
    ok = not errors and not (args.strict and warns)

    if args.json:
        print(json.dumps(dict(script=str(target), ahk=ahk, version=ver, ok=ok,
                              errors=errors, warnings=warns, hints=hints,
                              official_output=official_raw),
                         ensure_ascii=False, indent=2))
    else:
        print(f"校验 {target}\n解释器 v{ver}  ({ahk})")
        if not issues:
            print("  ✅ 通过：无错误、无警告")
        for i in errors:
            loc = f"L{i['line']}" if i["line"] else "文件"
            print(f"  ❌ [{loc}] {i['msg']}")
            if i.get("detail"):
                print(f"           具体：{i['detail']}")
        for i in warns:
            loc = f"L{i['line']}" if i["line"] else "文件"
            print(f"  ⚠️  [{loc}] {i['msg']}")
        for i in hints:
            print(f"  💡 [L{i['line']}] {i['msg']}")
        print(f"  —— 错误 {len(errors)} 项，警告 {len(warns)} 项，函数名待核 {len(hints)} 项")
        if errors:
            print("  ❌ 带错误的脚本不要交付，修完重新校验。")
        elif hints:
            print("  💡 函数名待核项请去 references/api-index.md 逐一确认后再交付。")

    if errors:
        return 1
    if warns and args.strict:
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
