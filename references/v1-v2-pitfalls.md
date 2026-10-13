# v1 → v2 陷阱对照（含官方校验器抓不到的盲区）

> 结论均来自 **本机 AutoHotkey v2.0.26 实测** + v2.0.26 源码核对。凡是标"实测"的，都跑过。
> 写脚本时对照本表自检，比事后调试便宜得多。

## 一、⚠️ 三个"官方校验器抓不到"的盲区（最危险）

这是本文件存在的首要理由。下面三件事，`AutoHotkey.exe /validate` **不会报错**，
但运行时会出问题或行为不符预期：

### 盲区 1：任何"名字 + 参数"的写法，只要名字不是已知函数，就只报警告（实测）

这是**覆盖最广、最危险**的盲区。AHK v2 允许把函数对象存在变量里再调用（`f := SomeFunc` 然后 `f()`），
所以解析器遇到"不认识的函数名带参数"时，会认为你在做**动态调用**，于是：

```ahk
StringReplace("abc", "a", "b")   ; ← v1 旧函数名
StrinReplace("abc", "a", "b")    ; ← 拼错的名字
NoSuchLabel()                    ; ← 根本不存在的函数
SetEnv x, 1                      ; ← v1 命令式（无逗号）
StringReplace s, a, b            ; ← v1 命令式（无逗号）
IfMsgBox Yes                     ; ← v1 语句
IfGreater x, 1                   ; ← v1 语句
Gosub SomeLabel                  ; ← v1 语句
```

以上**全部返回码 0**，只输出同一条警告（实测原文）：

```
bad.ahk (2) : ==> Warning: This global variable appears to never be assigned a value.
     Specifically: StringReplace
```

**运行时才崩**，而且崩的时候报的是"变量未赋值"，跟真正的毛病（函数名写错）看起来毫无关系。

> 📌 **判据**：只要校验输出里出现
> `This global variable appears to never be assigned a value.` +
> `Specifically: <某个名字>`，就去核对 `<某个名字>` 是不是写错了。
> **自检手段**：把那个名字拿到 `api-index.md` 里 Grep 一次。查不到 = 写错了。

👉 **对策**：`ahk_check.py` 的 `--api-check` 会替你做这件事 —— 它把脚本里所有"名字("调用点
跟 342 个内建函数表 + 脚本自定义函数比对，对不上的单独列出来（显示为 `💡 函数名待核`）。

### 对照：v1 语句带逗号 vs 不带逗号（实测结果不同）

| 写法 | 加载期结果 |
|---|---|
| `Gosub SomeLabel` | ⚠️ **静默通过**（仅警告） |
| `Gosub, SomeLabel` | ❌ `Function calls require a space or "(".` |
| `Goto SomeLabel` | ❌ `Label not found in current scope.` |
| `Goto, SomeLabel` | ❌ `Function calls require a space or "(".` |
| `SetEnv x, 1` | ⚠️ **静默通过**（仅警告） |
| `IfExist C:\Windows` | ❌ `Illegal character in expression.` |
| `IfExist, C:\Windows` | ❌ `Function calls require a space or "(".` |
| `IfMsgBox Yes` / `IfGreater x, 1` | ⚠️ **静默通过**（仅警告） |
| `Menu, Tray, Add` / `Gosub, x` | ❌ `Function calls require a space or "(".` |
| `#NoEnv` | ❌ `This line does not contain a recognized action.` |

**结论**：带逗号的 v1 写法基本都会被拦；**不带逗号的更危险，能静默过校验**。

### 对照：参数个数是会被抓的（这条能省很多调试）

```ahk
; 下面 5 行都会被加载期拦下（注释去掉即可复现）：
; v := StrLen()          → Too few parameters passed to function.   Specifically: StrLen
; v := Mod(1)            → Too few parameters passed to function.   Specifically: Mod
; v := StrLen(1, 2, 3)   → Too many parameters passed to function.  Specifically: StrLen
; Sleep()                → Too few parameters passed to function.   Specifically: Sleep
; FileCopy("a")          → Too few parameters passed to function.   Specifically: FileCopy

; 对照：参数"全部可选"的函数不会报这类错（WinMove 的 8 个参数都是可选的）
WinMove 0, 0
```

也就是说：**参数个数不对一定会在校验期拦下来**，不用等到运行。
（例外：`WinMove 0, 0` 能过，因为 WinMove 的参数全是可选的。）

### 盲区 2：点号 `.` 拼接在 v2.0 仍然能跑（实测）

```ahk
x := "a" . "b"     ; 实测输出 "ab"，校验通过，不报错
```
**但 `.` 在 v2.1 已被移除**，用户明确要求不用 v2.1 —— 留着它等于埋雷。

👉 **对策**：一律用空格隐式拼接 `"a" "b"`。`ahk_check.py` 的静态规则会替你抓这个。

### 盲区 3：中文乱码由编码引起，校验器看不出来（实测）

```ahk
FileAppend("中文测试ABC", "*")
```
| 文件编码 | 实测输出 |
|---|---|
| UTF-8 + BOM | `中文测试ABC` ✅ |
| UTF-8 无 BOM | `中文测试ABC` ✅ |
| **GBK / ANSI** | `����ABC` ❌ |

**原因**：源码 `globaldata.cpp: g_DefaultScriptCodepage = CP_UTF8` —— v2 一律按 UTF-8 读脚本。

👉 **对策**：写文件时显式用 `encoding="utf-8-sig"`。`ahk_check.py` 会检查并在非 UTF-8 时报错。

---

## 二、语法级对照（实测：左侧被官方校验器直接拒绝）

| v1 写法 | v2 正确写法 | 官方报错（实测） |
|---|---|---|
| `MsgBox, "hello"` | `MsgBox "hello"` 或 `MsgBox("hello")` | `Function calls require a space or "("` |
| `Send, "abc"` | `Send "abc"` / `SendText "abc"` | `Function calls require a space or "("` |
| `SetKeyDelay, 10, 50` | `SetKeyDelay 10, 50` | `Function calls require a space or "("` |
| `Loop, 5` | `Loop 5` | `Function calls require a space or "("` |
| `x = 1` | `x := 1` | `Syntax error. Did you mean ":="?` |
| `MsgBox, %x%` | `MsgBox x` | `Function calls require a space or "("` |
| `IfWinExist("x")` | `if WinExist("x")` | （⚠️ **不报错**，只警告 —— 见盲区 1） |
| `Gosub SomeLabel` | 改成函数调用 `SomeLabel()` | （⚠️ **不报错**，只警告） |
| `Gosub, SomeLabel` | 同上 | `Function calls require a space or "("` |
| `Goto SomeLabel` | 用函数/循环重构 | `Label not found in current scope.` |
| `MsgBox "a" .` | 删掉悬空的点号 | `Syntax error. Specifically: .` |
| `#NoEnv` | 直接删掉这一行 | `This line does not contain a recognized action.` |
| `#If WinActive("x")` | `#HotIf WinActive("x")` | `This line does not contain a recognized action.` |
| `StringLen s, n` | `n := StrLen(s)` | `Function calls require a space or "("` |
| `if ErrorLevel` | 改用返回值判断或 `try/catch` | （不报错，但 `ErrorLevel` 永远是空） |

### 允许的简化写法（很多人误以为非法，其实合法）

```ahk
MsgBox "hello"                       ; 单参数函数语句可省略括号 —— 合法
SetKeyDelay 10, 50                   ; 多参数也可省略括号 —— 合法
Loop 5 {
    OutputDebug A_Index              ; 循环体 —— 合法
}
```
规则是："函数调用语句 + 省略括号"，**只要不写成 v1 的 `名字, 参数`（名字后紧跟逗号）就行**。

---

## 三、v1 函数名 → v2 正确函数

这些名字**已逐个对照 v2.0.26 的 342 个内建函数全集核实**，确认在 v2 中不存在：

| v1 | v2 |
|---|---|
| `StringReplace` | `StrReplace` |
| `StringSplit` | `StrSplit` |
| `StringLen` | `StrLen` |
| `StringLeft` / `StringRight` / `StringMid` | `SubStr` |
| `StringTrimLeft` / `StringTrimRight` | `LTrim` / `RTrim` / `SubStr` |
| `StringLower` / `StringUpper` | `StrLower` / `StrUpper` |
| `StringGetPos` | `InStr` |
| `StringCaseSense` | （已移除）用 `StrCompare(a, b, CaseSense)` |
| `FileReadLine` | `FileRead` 或 `Loop Read` |
| `IfExist` / `IfWinExist` / `IfWinActive` | `FileExist` / `DirExist` / `WinExist` / `WinActive` |
| `SetEnv` / `EnvAdd` / `EnvSub` | `:=` / `+=` / `-=` |
| `Transform` | （已移除）按用途换函数 |
| `URLDownloadToFile` | `Download` |
| `ComObjCreate` | `ComObject` |
| `WinGet` | `WinGetTitle()` / `WinGetPos()` / `WinGetClass()` / `WinGetList()` |
| `ControlGet` | `ControlGetText()` / `ControlGetPos()` / `ControlGetFocus()` … |
| `GuiControl` / `GuiControlGet` | v2 的 Gui 对象方法（本 skill 不用界面） |
| `Menu` | `MenuBar` / `Menu` 对象 |
| `IfMsgBox` / `IfGreater` / `IfEqual` / … | （已移除）用表达式判断 |
| `AutoTrim` | （已移除）用 `Trim()` / `LTrim()` / `RTrim()` |

---

## 四、v1 指令 → v2 替代（v2 只剩 19 个指令，实测确认）

### v2.0.26 仅支持这 19 个指令

```
#Requires          #SingleInstance    #NoTrayIcon        #Warn
#Include           #IncludeAgain      #HotIf             #HotIfTimeout
#Hotstring         #InputLevel        #UseHook           #SuspendExempt
#ClipboardTimeout  #DllLoad           #ErrorStdOut       #MaxThreads
#MaxThreadsBuffer  #MaxThreadsPerHotkey                  #WinActivateForce
```

### 已移除的 v1 指令（写进脚本会直接报 `This line does not contain a recognized action.`）

| v1 指令 | v2 替代方式 |
|---|---|
| `#Persistent` | 函数 `Persistent()` |
| `#KeyHistory 0` | 函数 `KeyHistory(0)` 关闭；**没有** `A_KeyHistory` 变量（源码实测） |
| `#InstallKeybdHook` | 函数 `InstallKeybdHook()` |
| `#InstallMouseHook` | 函数 `InstallMouseHook()` |
| `#MaxHotkeysPerInterval 200` | 变量 `A_MaxHotkeysPerInterval := 200` |
| `#HotkeyInterval 1000` | 变量 `A_HotkeyInterval := 1000` |
| `#MenuMaskKey vkFF` | 变量 `A_MenuMaskKey := "vkFF"` |
| `#HotkeyModifierTimeout 100` | 变量 `A_HotkeyModifierTimeout := 100` |
| `#DefaultMouseSpeed 2` | 函数 `SetDefaultMouseSpeed(2)` |
| `#Delay 10` | `SetKeyDelay` / `SetMouseDelay` / `SetWinDelay` |
| `#NoEnv` | 删掉（v2 不再自动展开环境变量） |
| `#If` | `#HotIf` |
| `#CommentFlag` `#EscapeChar` `#MaxMem` `#AllowSameLineComments` | 已移除，无替代 |

### 这条是 v1→v2 最大的思维转变

> **v1 靠「指令」做全局配置，v2 靠「给变量赋值」或「调用函数」。**

```ahk
A_TitleMatchMode := 2        ; 相当于 v1 的 SetTitleMatchMode, 2
A_Clipboard := "文本"         ; 相当于 v1 的 clipboard = 文本
A_KeyDelay := 10             ; 相当于 v1 的 SetKeyDelay, 10
SetTimer MyFunc, 1000        ; 仍然是函数
```

> 可写的内置变量清单见 `api-index.md` 的「### 可写变量」一节（37 个，从源码 `g_BIV_A[]` 注册表导出）。

---

## 五、其他容易踩的差异

| 项 | v1 | v2 |
|---|---|---|
| 剪贴板变量 | `clipboard` | `A_Clipboard` |
| 错误处理 | `If ErrorLevel` | `try/catch as e` + 检查函数返回值 |
| 对象类型 | 只有 `Object()` | `Map()` / `Array()` / `Object()` 分工明确 |
| 数组下标 | 从 1 开始 | 从 **1** 开始（`arr[1]` 是第一个） |
| 表达式内取变量 | `%var%` | 直接写 `var`（`%var%` 仅用于字符串拼接的遗留场景，少用） |
| 函数定义 | `FuncName(a, b) { }` | 同左；另有箭头函数 `f := (x) => x * 2` |
| 类 | 不支持 | 完整支持 `class` |
| 热键块 | `热键::` + `return` | `热键:: { ... }` 花括号块，推荐 |
| 函数内全局变量 | 可直接读写全局变量 | **读**不用声明；**写**必须 `global`，否则静默创建同名局部变量（+警告） |
| 命令返回值 | `ErrorLevel` 全局变量 | 函数直接返回结果 |
| GUI | `Gui, Add, Button` | `Gui()` 对象（本 skill 不使用） |
| 正则 | `RegExMatch` 存在但语义旧 | `RegExMatch` / `RegExReplace` 返回匹配对象 |
| **自动执行段** | 止于第一个热键/`return`，其后的顶层语句**不执行** | **没有这个界线**：顶层语句按序全部执行，函数/热键/类定义被跳过 |
| **`SoundBeep` 参数顺序** | `SoundBeep, Frequency, Duration` | **反过来了**：`SoundBeep(Duration, Frequency)`（源码 `md_func_v(SoundBeep, (Duration), (Frequency))` 已核） |
| **字符串内双引号** | `"say ""hi"" now"`（双写转义） | **只能用反引号**：`` "say `"hi`" now" ``。用 `""` 实测报 `Missing space or operator before this.` |

### 关于"自动执行段"（实测）

v1 里热键后面的顶层代码是不会执行的；**v2 里会执行**。实测脚本：

```ahk
FileAppend "A ", "*"
Foo() {
    return 1
}
FileAppend "B ", "*"
^!z::ExitApp()
FileAppend "C", "*"
```

实测输出 `A B C` —— **函数定义和热键定义被跳过，但顶层语句一条不落全跑了**。

👉 实践含义：想写"命令行自测入口"，可以直接放在脚本末尾，
不用像 v1 那样特意挪到文件最前面：

```ahk
; 自测入口：放在文件末尾照样会被执行
if (A_Args.Length && A_Args[1] = "test") {
    FileAppend "进入自测模式", "*"
    ExitApp(0)
}
```
