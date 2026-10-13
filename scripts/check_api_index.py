#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_api_index.py —— 文档函数名核对 + api-index 存在性实证（本技能的第二道防线）

做什么
------
A. 静态核对（默认）
   1. 从 references/api-index.md 抽出内建函数全集。
   2. 从 SKILL.md 与 references/*.md 的 ```ahk 代码块里抽出所有"被调用的名字"。
   3. 减去：api-index 里的名字、文档/脚本里自定义的函数名与类名、函数参数名、AHK 关键字。
   4. 剩下的就是**可疑名字**：v1 旧名、拼错的名字、或不存在的函数。

B. 存在性实证（--probe）
   把 api-index.md 里的每个名字生成一行存在性探针，交本机解释器真跑一遍，
   逐个确认"这个名字到底存不存在"。**api-index 声称的条数以探针结果为准**，
   不允许文档里写没跑过的数字。

为什么必须做
------------
AHK 官方校验器对"不认识的函数名带参数"只报警告不报错（见
references/v1-v2-pitfalls.md 第一节），写出 StringReplace(...) 这种 v1 旧名
它能放你过去，直到运行时才崩。所以文档里的示例也必须过这一关。

用法
----
    python scripts/check_api_index.py            # 静态核对
    python scripts/check_api_index.py --json     # 机器可读
    python scripts/check_api_index.py --probe    # 额外实跑存在性探针（约 1 秒）
退出码：0 = 通过；1 = 可疑名字 / 探针发现不存在的名字。
"""

from __future__ import annotations

import json
import pathlib
import re
import subprocess
import sys
import tempfile

SKILL_DIR = pathlib.Path(__file__).resolve().parent.parent
API_FILE = SKILL_DIR / "references" / "api-index.md"
DOC_GLOBS = ["SKILL.md", "references/*.md", "scripts/**/*.ahk"]

# AHK v2 语句/关键字/运算符——它们后面跟括号时会被误判成"函数调用"
KEYWORDS = {
    "if", "else", "while", "for", "loop", "switch", "case", "default", "until",
    "break", "continue", "return", "try", "catch", "finally", "throw", "goto",
    "global", "local", "static", "class", "super", "this", "new", "and", "or",
    "not", "is", "in", "contains", "unset", "true", "false", "byref", "as",
    "do",
}

CALL_RE = re.compile(r"(?<![.\w])([A-Za-z_][A-Za-z0-9_]*)\s*\(")
# 定义行：`Name(args) {` / `Name(args)` / `Name(args) => expr`
DEF_RE = re.compile(r"^\s*(?:static\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*\(([^()]*)\)\s*(?:\{|=>|$)")
CLASS_RE = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")

# 教学反例白名单：references/v1-v2-pitfalls.md 等文档**故意写出来**的 v1 旧名与
# 错误名（用来演示"校验器抓不到"的盲区）。它们不是文档自身的错误，
# 但也不该被静默忽略——命中时会在报告里单独列出，方便人工复核。
KNOWN_COUNTEREXAMPLES = {
    "StringReplace", "StringSplit", "StringLen", "StringLeft", "StringRight",
    "StringMid", "StringTrimLeft", "StringTrimRight", "StringLower", "StringUpper",
    "StringGetPos", "StringCaseSense", "FileReadLine", "IfExist", "IfWinExist",
    "IfWinActive", "SetEnv", "EnvAdd", "EnvSub", "Transform", "URLDownloadToFile",
    "ComObjCreate", "GuiControl", "GuiControlGet", "AutoTrim", "IfMsgBox",
    "IfGreater", "IfEqual", "GetPixelColor", "StrinReplace", "NoSuchLabel",
    "ErrorLevel",
}


def api_function_names() -> list[str]:
    """api-index.md 的函数行形如 `Abs(1~1 个参数)`。返回去重后的名字列表。"""
    text = API_FILE.read_text(encoding="utf-8")
    names: list[str] = []
    for line in text.splitlines():
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\(", line.strip())
        if m and m.group(1) not in names:
            names.append(m.group(1))
    return names


def ahk_blocks(text: str) -> list[str]:
    return re.findall(r"```ahk\n(.*?)```", text, re.S)


def clean_params(raw: str) -> set[str]:
    out: set[str] = set()
    for part in raw.split(","):
        p = part.strip().lstrip("&").rstrip("*").strip()
        p = p.split(":=")[0].strip()
        if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", p):
            out.add(p)
    return out


def strip_embedded_blocks(text: str) -> list[str]:
    """去掉 AHK 内嵌的多行字符串（本技能的截图脚本里塞着整段 PowerShell/C#）。

    格式是：
        VAR := "
        (
        ...这里不是 AHK 代码...
        )"
    不剔除的话，PowerShell 里的 [Drawing.Bitmap]::FromImage( 之类会被当成 AHK 调用。
    """
    kept: list[str] = []
    inside = False
    for line in text.splitlines():
        stripped = line.rstrip()
        if not inside:
            if re.search(r':=\s*"\s*$', stripped) or re.search(r':=\s*\(\s*$', stripped):
                inside = True
                continue
            kept.append(line)
        else:
            if re.match(r'^\s*\)"?\s*$', stripped):
                inside = False
    return kept


def scan_sources() -> tuple[dict[str, list[str]], set[str]]:
    """返回 (被调用的名字 -> [来源:行], 本技能自定义的函数/类/参数名集合)"""
    local_known: set[str] = set()
    calls: dict[str, list[str]] = {}

    for pattern in DOC_GLOBS:
        for path in sorted(SKILL_DIR.glob(pattern)):
            if path.name == "api-index.md":
                continue
            text = path.read_text(encoding="utf-8")
            sources: list[tuple[str, list[str]]] = []
            if path.suffix == ".ahk":
                sources.append((path.name, strip_embedded_blocks(text)))
            else:
                for idx, block in enumerate(ahk_blocks(text), 1):
                    sources.append((f"{path.name}", strip_embedded_blocks(block)))
            for label, lines in sources:
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith(";"):
                        continue
                    m = DEF_RE.match(line)
                    if m:
                        local_known.add(m.group(1))
                        local_known |= clean_params(m.group(2))
                    m2 = CLASS_RE.match(line)
                    if m2:
                        local_known.add(m2.group(1))
                    for name in CALL_RE.findall(line):
                        calls.setdefault(name, []).append(f"{label}:{i}")

    return calls, local_known


AHK_EXE = pathlib.Path(r"C:\Program Files\AutoHotkey\v2\AutoHotkey.exe")
PROBE_FILE = pathlib.Path(tempfile.gettempdir()) / "ahk_api_probe.ahk"


def write_probe(names: list[str], path: pathlib.Path) -> None:
    """每块 6 行：探测名字是否存在，并记下它是函数(F)还是类(C)。"""
    lines = ["#Requires AutoHotkey v2.0", "#SingleInstance Force", 'Missing := ""', 'Res := ""']
    for n in names:
        lines += [
            "try {",
            f"\tx := {n}",
            f'\tRes := Res "{n}=" (Type(x) = "Func" ? "F" : "C") "|"',
            "} catch {",
            f'\tMissing := Missing " {n}"',
            "}",
        ]
    lines += ['FileAppend "RESULT:" Res "`nMISSING:" Missing, "*"', "ExitApp"]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def loads_clean(path: pathlib.Path) -> bool:
    """官方校验：只加载不执行。返回码 0 = 通过（不存在的名字只会报警告，不影响返回码）。"""
    if not AHK_EXE.exists():
        raise RuntimeError(f"找不到解释器：{AHK_EXE}")
    r = subprocess.run(
        [str(AHK_EXE), "/ErrorStdOut", "/validate", str(path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    return r.returncode == 0


def split_load_breakers(names: list[str]) -> list[str]:
    """二分找出会让整份探针在**加载期**就报错的名字。

    这类名字不是"不存在"，恰恰相反——它们被解析器当成语法关键字（实测如 `IsSet`），
    `x := IsSet` 会报 `Missing "("`。它们必须从探针里剔除，否则会带崩整份脚本。
    """
    breakers: list[str] = []

    def probe_group(group: list[str]) -> bool:
        if not group:
            return True
        write_probe(group, PROBE_FILE)
        return loads_clean(PROBE_FILE)

    def bisect(group: list[str]) -> None:
        if len(group) == 1:
            breakers.append(group[0])
            return
        mid = len(group) // 2
        left, right = group[:mid], group[mid:]
        if not probe_group(left):
            bisect(left)
        if not probe_group(right):
            bisect(right)

    if not probe_group(names):
        bisect(names)
    return breakers


def run_probe(names: list[str]) -> tuple[list[str], list[str], dict[str, str]]:
    """返回 (确实不存在的名字, 语法关键字型名字, {名字: F 函数 / C 类})"""
    breakers = split_load_breakers(names)
    usable = [n for n in names if n not in breakers]
    if not usable:
        return [], breakers, {}

    write_probe(usable, PROBE_FILE)
    runner = SKILL_DIR / "scripts" / "ahk_run.py"
    proc = subprocess.run(
        [sys.executable, str(runner), str(PROBE_FILE), "--timeout", "60"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    m = re.search(r"MISSING:(.*)", out)
    if not m:
        raise RuntimeError(f"探针没有回传结果，原始输出：\n{out}")
    kinds: dict[str, str] = {}
    for item in re.search(r"RESULT:(.*)", out).group(1).split("|"):
        if "=" in item:
            name, kind = item.rsplit("=", 1)
            kinds[name.strip()] = kind
    return m.group(1).split(), breakers, kinds


def main() -> int:
    as_json = "--json" in sys.argv
    do_probe = "--probe" in sys.argv
    if not API_FILE.exists():
        print(f"❌ 找不到 {API_FILE}")
        return 1

    api = api_function_names()
    calls, local_known = scan_sources()
    unknown = {n: w for n, w in calls.items() if n not in set(api) | local_known | KEYWORDS}
    suspicious = {n: w for n, w in unknown.items() if n not in KNOWN_COUNTEREXAMPLES}
    counterexamples = {n: w for n, w in unknown.items() if n in KNOWN_COUNTEREXAMPLES}

    missing: list[str] = []
    breakers: list[str] = []
    kinds: dict[str, str] = {}
    if do_probe:
        missing, breakers, kinds = run_probe(api)

    if as_json:
        print(json.dumps({
            "api_listed": len(api),
            "api_functions": sum(1 for v in kinds.values() if v == "F"),
            "api_classes": sum(1 for v in kinds.values() if v == "C"),
            "api_probed_missing": missing,
            "api_keyword_like": breakers,
            "suspicious": {k: sorted(set(v))[:5] for k, v in sorted(suspicious.items())},
        }, ensure_ascii=False, indent=2))
    else:
        print(f"api-index 列出的名字：{len(api)} 个")
        if do_probe:
            nf = sum(1 for v in kinds.values() if v == "F")
            nc = sum(1 for v in kinds.values() if v == "C")
            print(f"存在性探针：实际存在 {len(api) - len(missing)} 个"
                  + (f"，不存在的 {len(missing)} 个：{', '.join(missing)}" if missing else "，全部存在 ✅"))
            print(f"           其中函数 {nf} 个、类 {nc} 个"
                  + (f"（另有 {len(breakers)} 个语法关键字型：{', '.join(breakers)}）" if breakers else ""))
        if suspicious:
            print(f"\n❌ 可疑名字 {len(suspicious)} 个（不在内建表、也非本技能自定义）：")
            for name, where in sorted(suspicious.items()):
                print(f"   {name:<28} 出现于 {', '.join(sorted(set(where))[:4])}")
        else:
            print("\n✅ 文档与脚本里的函数名全部有据可查。")
        if counterexamples:
            print(f"ℹ️ 另命中教学反例白名单 {len(counterexamples)} 个"
                  f"（文档故意写的 v1 旧名/错误名，非缺陷）：{', '.join(sorted(counterexamples))}")

    return 1 if (suspicious or missing) else 0

if __name__ == "__main__":
    sys.exit(main())
