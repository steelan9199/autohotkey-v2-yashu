---
name: autohotkey-v2-yashu
description: 用 AutoHotkey v2（仅 v2.0.x，排除 v1 与 v2.1）为 Windows 11 编写桌面自动化脚本——键盘鼠标模拟、全局热键与热字串、窗口/进程管理、剪贴板与文本处理、批量文件操作、定时任务、找图找色与截图、调用外部程序。当用户提到 AutoHotkey、ahk、ahk2、写个脚本自动操作电脑、全局快捷键、热键、热字串、模拟按键、自动点击、自动填表、窗口切换、激活窗口、剪贴板处理、批量重命名、监听文件夹、定时执行、开机自启脚本、找图找色、自动登录、游戏或办公自动化时使用。不含 GUI 界面开发，不写 v1 语法，不使用 v2.1 新特性。
disable-model-invocation: false
version: 1.1.0
---

# AutoHotkey v2 自动化脚本（Windows 11）

产出**能跑起来**的 `.ahk` 脚本，用来替代人工重复操作。本技能只覆盖 **v2.0.x**。

## 0. 铁律（动手前先读，违反任何一条即为交付失败）

| # | 铁律 | 原因 |
|---|---|---|
| 1 | **只写 v2.0.x 语法**。不写 v1（会直接报错），也不用 v2.1 新特性 | 用户明确排除 v1 与 v2.1；本机解释器就是 v2.0.26 |
| 2 | **不做界面**。只有 `MsgBox`/`InputBox`/`TrayTip` 这类轻量提示可用，禁止 `Gui()` 自定义窗口 | 用户要的是无人值守自动化 |
| 3 | **文件必须存成 UTF-8**（推荐带 BOM） | AHK v2 一律按 UTF-8 读脚本；存成 GBK/ANSI 中文会变乱码 |
| 4 | **每个函数名都要在 `references/api-index.md` 里查得到** | 342 个内建函数全表，查不到 = 写错了（v1 旧名或虚构） |
| 5 | **交付前必须跑校验且 0 错误** | 见下方工作流第 3 步，这是唯一能拦住"看着对、一跑就崩"的关卡 |
| 6 | **📏 体量红线：`SKILL.md` ≤10000 字符、每篇 `references/*.md` ≤30000 字符，超了必须拆分** | 常驻层每轮对话重发，是固定成本；`references/` 按需读。超限说明文档在膨胀，不调阈值 |
| 7 | **本技能是活文档——只留正确的知识**：进文档须过 G0~G4 五道门槛，证伪的删干净 | 门槛见 `references/自进化与维护.md` §二 收录判据。**G0 硬证据 = 本次会话亲自跑过并看到输出** |
| 8 | **🔧 取证充分就直接改，不必请示** | 卡住自进化的请示成本比改错更高。只有不可逆或会削弱安全网的动作才先问（见 §四 授权分级）；判断口径：**能不能靠 git 回滚 + 门禁拦住** |

## 1. 标准工作流（照做，别跳步）

```bash
PY="D:/software/uv/python/cpython-3.14.7-windows-x86_64-none/python.exe"   # 本机 Python
S="C:/Users/Administrator/.workbuddy/skills/autohotkey-v2-yashu"
```

**第 1 步 · 写脚本**到磁盘（默认目录 `D:\temp\`，用户可指定）。骨架直接抄第 3 节。

**第 2 步 · 查名字**：把脚本里用到的每个函数名，在 `references/api-index.md` 里核对一遍。
> 为什么必须手动查：AHK 官方校验器对**未定义的函数名只报警告不报错**（实测确认），
> 写出 `StringReplace(...)` 这种 v1 旧名它能放你过去，直到运行时才崩。

**第 3 步 · 校验（必做）**：

```bash
"$PY" "$S/scripts/ahk_check.py" "D:\temp\xx.ahk" --strict
```
- 输出 `✅ 通过：无错误、无警告` 才算过。有 ❌ 就按提示改，改完重跑，直到干净。
- `--strict` 会把警告也当失败，**建议一直带着**，因为多数警告恰恰是真 bug 的线索。
- 它同时做三件事：① 官方解释器语法校验（只加载不执行，零副作用）；
  ② 静态规则检查（专抓官方漏掉的 v1 遗留写法、点号拼接、中文编码问题）；
  ③ 函数名核对（把脚本里的调用点比对 342 个内建函数表，抓拼错和 v1 旧名）。
- 判读输出：`❌` = 必须修；`⚠️` = 建议修（`--strict` 下会判失败）；`💡` = 函数名待核，去 `api-index.md` 逐个确认。

**第 4 步 · 试跑（涉及键鼠/窗口操作时强烈建议）**：

```bash
"$PY" "$S/scripts/ahk_run.py" "D:\temp\xx.ahk" --timeout 6
```
真跑一遍，`try/catch` 兜住运行期错误（不会弹窗卡死），6 秒后自动收工。
看到 `❌ 运行期错误` 就按给出的文件与行号定位修复。

脚本若带命令行自测入口（见下方"自测入口"约定），参数直接跟在后面，
会出现在脚本的 `A_Args` 里：

```bash
"$PY" "$S/scripts/ahk_run.py" "D:\temp\xx.ahk" --timeout 6 test
```

**第 5 步 · 归档并登记（用户点单做的成品必走）**：
把脚本存进 `scripts/delivered/`，并在第 5 节台账里追加一行。
> 工作区/临时目录只算草稿。用户点单做出来的东西，**落到 `delivered/` 才算交付完成**。

**第 6 步 · 自进化（改了本技能的任何文档/脚本时必走）**：

```bash
node "$S/scripts/skill_audit.js"         # 门禁：断链 / 负向声明 / 体量 / 版本号 / 脚本校验
node "$S/push.js" "<改了什么>"            # 门禁 → 提交 → 推送 → 打 tag
```

1. 新证据（实测结论）按 `references/自进化与维护.md` §二 收录判据 决定收不收、收到哪一篇；
2. **每次改动必须递增 frontmatter 的 `version`**（规则见 §五 版本号规则）；
3. patch 级只落盘、不碰 git；minor/major 走 `push.js` 提交推送并打 tag（tag 是回滚落点）；
4. 改完**必须把新知识写回文档再收工** —— 不然这次会话踩的坑，下次还要再踩一遍。

## 2. 环境

| 项 | 值 |
|---|---|
| 解释器 | `C:\Program Files\AutoHotkey\v2\AutoHotkey.exe`（已装 **2.0.26**） |
| 运行脚本 | 双击 `.ahk` 文件，或命令行 `AutoHotkey.exe 脚本.ahk` |
| 停止脚本 | 右下角托盘图标 → 右键 → Exit；或在脚本里绑一个 `^!x::ExitApp()` |
| 开机自启 | 把 `.ahk`（或它的快捷方式）放进 `shell:startup` 目录 |
| 环境自检 | `"$PY" "$S/scripts/ahk_check.py" --doctor` |

## 3. 脚本骨架（照抄改内容）

```ahk
#Requires AutoHotkey v2.0        ; 必加：让 v1 解释器直接拒绝运行
#SingleInstance Force            ; 重复启动时替换旧实例，避免堆叠多个脚本
SendMode "Input"                 ; 最可靠的发送模式，兼容性最好
SetWorkingDir A_ScriptDir        ; 工作目录固定为脚本所在目录
; 常驻：有热键/热字串/定时器时脚本会自动常驻，无需额外操作（实测）
; 只有既没热键也没定时器的脚本才需要显式 Persistent(true)

; ---------- 配置区 ----------
targetWin := "ahk_exe notepad.exe"

; ---------- 热键区 ----------
^!s:: {                           ; Ctrl+Alt+S
    if !WinExist(targetWin) {
        TrayTip "窗口未找到", "请先打开记事本"
        return
    }
    WinActivate targetWin
    WinWaitActive targetWin, , 2
    SendText "自动化脚本已接管`n"  ; 文本用 SendText，避免被当成按键解析
}

^!x::ExitApp()                    ; 逃生热键：随时退出脚本
```

**关键约定**：
- 热键多语句一律用 `热键:: { ... }` 花括号块，别写连续 `return`。
- **文本内容一律用 `SendText`**，`Send` 会把 `!^#{}` 之类当特殊键解析（这是最常见的翻车点）。
- 涉及等待窗口/剪贴板时，别写死 `Sleep 2000`，用 `WinWaitActive`/`ClipWait` 带超时。

## 4. 高频语法（写之前扫一眼，全部经 v2.0.26 实测）

```ahk
x := 1                      ; 赋值用 :=（v1 的 x = 1 已失效）
s := "a" "b"                ; 字符串拼接用空格隐式连接（不要用 . 点号）
n := Mod(7, 2)              ; 取余必须用 Mod()，% 在 v2 里不能当运算符
if (x = 1) {                ; 判断用表达式（v1 的 if x = 1 已失效）
    y := 2                  ; ⚠️ 花括号里的内容必须换行写，不能挤在 { } 里
}
if WinExist("ahk_class Notepad")      ; 判断窗口用函数返回布尔
    WinActivate()
Loop 5 {                    ; 循环（v1 的 Loop, 5 逗号写法已失效）
    z := A_Index
}
for i, v in ["a", "b"] {
    OutputDebug v
}
m := Map("k", "v")
a := [1, 2, 3]
try {
    FileRead "D:\可能不存在的文件.txt"      ; 可能失败的调用一律套 try/catch
} catch as e {
    OutputDebug e.Message
}
SetKeyDelay 10, 50          ; 函数调用可省略括号（单个语句时）
Sleep 500
A_Clipboard := "文本"        ; A_Clipboard 是内置变量，v1 的 clipboard 已改名
str := Trim(A_Clipboard)
StrReplace(s, "a", "b")
RegExMatch(s, "\d+", &m)
ProcessExist("notepad.exe")
WinActivate "ahk_exe notepad.exe"
MouseClick "left", 100, 200
PixelSearch &x, &y, 0, 0, 500, 500, 0xFF0000
ImageSearch &x, &y, 0, 0, A_ScreenWidth, A_ScreenHeight, "*50 icon.png"
```

**七条必背的硬规则**（实测踩出来的，写错就是直接报错或埋雷）：

| 规则 | 错误写法 | 正确写法 |
|---|---|---|
| `%` 不能取余 | `c := 7 % 2` → `Missing ending "%"` | `c := Mod(7, 2)` |
| `{` 后必须换行 | `if (c) { y := 1 }` → `Unexpected "If"` | `{` 换行后逐行写内容 |
| 不能写单行空块 | `Loop 5 { }` → `Unexpected "Loop"` | `Loop 5 {` 换行 `}` |
| 变量名大小写不敏感 | 定义函数 `Add()` 后又写 `add := ...` → `This Func cannot be used as an output variable` | 换个名字 |
| **顶层变量别和函数内局部/参数同名** | 顶层 `plan := ...` + 函数内也有 `plan` | **会报 `local variable has the same name as a global variable`**，`--strict` 直接判失败 |
| **函数内"写"全局变量必须声明 `global`** | 直接 `x := "新值"` → 只改了局部，全局不变 | 函数内先写 `global x` 再赋值（**读**全局不用声明） |
| **写文件必须显式带编码** | `FileAppend(txt, f)` → 按 ANSI 写，中文乱码 | `FileAppend(txt, f, "UTF-8")` |

> 第 5 条是**实战里最容易犯**的一条：把配置写在顶层当全局变量，同时又让函数参数叫同一个名字。
> 解法：顶层只放真正需要跨函数共享的配置，其余全部收进函数里；命令行自测入口也包进函数（见下）。

要写的内容**不在上面**，就去 `references/syntax-cheatsheet.md` 按类别查。

### 自测入口约定（写脚本时强烈建议加）

给脚本留一个**命令行自测入口**：平时双击正常运行，带参数 `test` 时只跑验证逻辑、打印结果、立刻退出。
这样脚本的核心逻辑就能被 `ahk_run.py` 真跑一遍验证，而不是只做语法检查。

```ahk
; ---------- 自测入口 ----------
if (A_Args.Length && A_Args[1] = "test") {
    SelfTest()
}

DoWork(input) {
    return StrUpper(input)
}

SelfTest() {
    ; 用假数据/临时目录验证核心逻辑，不碰真实环境
    result := DoWork("样例输入")
    FileAppend "结果：" result, "*"
    ExitApp(0)
}

^!x::ExitApp()
```

要点：
- 自测逻辑**必须包进函数**（如 `SelfTest()`），否则它的局部变量会变成全局变量，污染整个脚本。
- 用 `FileAppend(..., "*")` 把结果写到标准输出，`ahk_run.py` 会原样回显。
- v2 里顶层语句在热键/函数定义之后**仍会执行**（v1 不会），所以自测入口放文件末尾也没问题。
- 对外部有副作用的操作（截图、改文件）在自测里要指向临时目录，别动用户的真实数据。

## 5. 交付脚本存档（`scripts/delivered/`）

**这个文件夹专门存放"用户点单、我做出来、已验证通过"的成品脚本** —— 用户日常直接双击用的东西都在这儿，不散落在磁盘各处。

| 目录 | 是什么 | 谁用 |
|---|---|---|
| `scripts/snippets/` | 通用独立片段（截图、找图找色的裸代码） | 我：写脚本时抄 |
| **`scripts/delivered/`** | **按用户具体需求定制的完整可跑脚本** | **用户：日常直接用** |
| 用户磁盘其他位置 | 草稿、临时验证件，不作归档 | — |

**归档判据**（三条全中才进这里）：

1. 用户点名要的（给了明确需求，如"截 (15,163) → (160,193) 这块"）；
2. `ahk_check.py --strict` 结果为 `✅ 通过`；
3. 至少试跑过一次（`ahk_run.py`，带自测入口的用 `test` 参数）。

**台账**（每交付一个脚本追加一行，别漏）：

| 脚本 | 用途 | 用法 | 交付日期 |
|---|---|---|---|
| `shot_region.ahk` | 截取屏幕固定矩形区域（默认左上 (15,163) → 右下 (160,193)，145×30 像素），存为 PNG | 双击 = 截图一张；`Ctrl+Alt+R` 再截；`Ctrl+Alt+X` 退出。图片存脚本同目录 `screenshots\`，文件名 `region_年月日_时分秒.png`。改区域：改配置区的 `BOX := {x1: 15, y1: 163, x2: 160, y2: 193}` 那一行 | 2026-10-13 |
| `cmd_driver.ahk` | **命令文件驱动的桌面操作执行器**：把「每步新写一个脚本」变成「写一个纯文本命令文件」，支持 `activate / move / click / dblclick / wheel / type / typefile / key / sleep / shot / probe / log`，全程记日志 | `AutoHotkey.exe cmd_driver.ahk <命令文件> [目标窗口] [日志文件]`。命令文件存 UTF-8、一行一条、字段用 `\|` 分隔；`shot` 等产物文件落盘后再返回。加 `test` 参数 = 只验解析分发、不动键鼠。用法与三条调用侧坑见 `references/recipes.md §R29 命令文件驱动批量桌面操作` | 2026-10-16 |

**改动已有成品时**：留在原地改，改完重跑校验 + 试跑，再回来更新台账该行的"用法"（比如热键变了）。

## 6. 参考资料（按需读，别全读）

| 文件 | 什么时候读 |
|---|---|
| `references/api-index.md` | **每次都要**：核对函数名是否存在、参数个数与含义（342 函数 + 131 变量 + 36 内建类全集） |
| `references/v1-v2-pitfalls.md` | 担心写出 v1 写法时；含官方校验器**抓不到**的盲区清单 |
| `references/syntax-cheatsheet.md` | 需要语法细节：变量/函数/类/字符串/数组/正则/热键/指令 |
| `references/recipes.md` | 按场景抄配方：窗口、键鼠、剪贴板、文件、定时、截图找图、网络调用 |
| `references/errors.md` | 校验或试跑报错时，按错误消息反查根因 |
| **`references/自进化与维护.md`** | **改本技能前必读**。收录判据 G0~G4 / 删错门槛 / 授权分级 / 版本号 / push-tag-回滚 / 体量红线 |
| `scripts/snippets/*.ahk` | 可直接复制的独立片段（截图、找图找色等） |
| `scripts/delivered/*.ahk` | 已交付给用户的成品脚本台账（见第 5 节）。**新交付脚本先登记，再看这里有没有类似的可复用** |

**脚本**（`scripts/` 下）

| 文件 | 用途 |
|---|---|
| `ahk_check.py` | 校验脚本：官方加载期校验 + 静态规则 + 函数名核对。交付前必跑 |
| `ahk_run.py` | 试跑器：真跑一遍，`try/catch` 兜住运行期错误，超时自动收工 |
| **`check_api_index.py`** | **文档函数名核对 + api-index 存在性实证**。`--probe` 会生成探针实跑，逐个确认 377 个名字真实存在并区分函数/类 |
| **`skill_audit.js`** | **自进化门禁**：引用断链 / 负向声明 / 体量红线 / version 字段 / 所有 `.ahk` 过校验。改完必跑，任一红灯退出码 1 |
| **`push.js`** | 提交推送 + 打回滚 tag：`node push.js "<说明>"`。门禁不过拒绝推送 |

## 7. 交付时告诉用户什么

1. 脚本文件路径（成品应在 `scripts/delivered/`，不在临时目录）。
2. **一键启动方式**（双击 / 放进 `shell:startup` 开机自启）。
3. 用到哪些热键，**特别是逃生热键**（`Ctrl+Alt+X` 之类）。
4. 校验结果（`✅ 通过`）、以及是否试跑过。
5. 已知限制 / 需要用户手动配合的前置条件（例如"需要目标程序已打开"）。
6. 归档确认：已存进 `scripts/delivered/`，且已在第 5 节台账登记（告诉用户这一句，让他知道去主文档能查到）。
