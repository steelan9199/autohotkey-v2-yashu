# AutoHotkey v2 配方库（29 个现成场景）

> 29 个配方，五类：**窗口/进程/调度**、**键鼠/热键/热字串**、**剪贴板/文本/文件**、
> **截图/找图找色/网络**、**命令行驱动的批量操作**。
>
> 每个配方都是**能独立运行的完整脚本**，已逐块通过官方 v2.0.26 编译器校验。
> 抄用方法：整块复制 → 改 **配置区**（`; ← 改这里` 标注的地方）→ 存成 UTF-8 的 `.ahk` → 跑一遍校验。
>
> **统一约定**：每个脚本都带 `^!x::ExitApp()` 逃生热键（`Ctrl+Alt+X` 退出）。
> 热键里 `^`=Ctrl、`!`=Alt、`+`=Shift、`#`=Win。
> 例外：R23 / R28 引入了截图片段，而片段自身已定义 `^!x`，不要再定义第二遍。

## 目录

| # | 配方 | # | 配方 |
|---|---|---|---|
| R1 | 一键唤起或启动程序 | R15 | 固定操作序列宏 |
| R2 | 窗口置顶开关 | R16 | 剪贴板清洗 |
| R3 | 一键左右分屏 | R17 | 多剪贴板历史 |
| R4 | 结束指定进程 | R18 | 选中文字 → 搜索 |
| R5 | 定时器：周期任务 | R19 | 批量重命名 |
| R6 | 定时关机 / 取消 | R20 | 文件夹监听 |
| R7 | 只在特定程序生效的热键 | R21 | 批量文本替换 |
| R8 | 开机自启开关 | R22 | CSV / 日志逐行处理 |
| R9 | 进程守护 | R23 | 截图（全屏/区域/窗口） |
| R10 | 键位改绑 | R24 | 找色点击 |
| R11 | 连点器 | R25 | 找图点击 |
| R12 | 一键输入常用文本 | R26 | 调用 HTTP 接口取 JSON |
| R13 | 热字串：邮箱/日期/签名 | R27 | 下载文件 |
| R14 | 滚轮与鼠标侧键 | R28 | 定时截图存档 |
| R29 | 命令文件驱动批量操作 | — | — |

---

## 通用注意事项（先看这 6 条，能省掉大半返工）

| # | 规则 | 说明 |
|---|---|---|
| 1 | **配置区集中放顶部** | 路径、窗口标识、时间间隔都提到脚本开头，之后改参数不用翻代码 |
| 2 | **窗口标识优先用 `ahk_exe`** | 如 `"ahk_exe notepad.exe"`；标题会随文档名变化，不稳 |
| 3 | **等窗口/剪贴板要带超时** | `WinWaitActive ... , , 3`、`ClipWait(1)`。写死 `Sleep 5000` 又慢又不稳 |
| 4 | **文本一律 `SendText`** | `Send` 会把 `!^#{}` 当特殊键解析，这是最常见的翻车点 |
| 5 | **可能失败的调用套 `try/catch`** | v2 出错默认弹模态框并卡死脚本，`try/catch` 是唯一的笼子 |
| 6 | **不用 `MsgBox` 做反馈** | 它是模态的，无人值守时会卡住等人点。用 `TrayTip`（非阻塞气泡） |

> 截图、找图找色都要求先设 `CoordMode "Pixel"` / `CoordMode "Mouse"` 为 `"Screen"`，
> 否则坐标是相对当前窗口的，换个窗口就点偏。

---

# 一、窗口 / 进程 / 系统调度

## R1 · 一键唤起或启动程序

最有用的一个：按 `Ctrl+Alt+1/2/3` 直接跳到对应程序；没开就启动。
优于普通热键的地方 —— **窗口已存在时它是"切换"，不会重复开一堆实例**。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force
SetWorkingDir A_ScriptDir

; ---------- 配置区 ----------
Apps := Map(
    "^!1", Map("win", "ahk_exe Code.exe",    "exe", "Code.exe"),
    "^!2", Map("win", "ahk_exe chrome.exe",  "exe", "chrome.exe"),
    "^!3", Map("win", "ahk_exe notepad.exe", "exe", "notepad.exe")
)

; ---------- 注册（不用一条条写热键）----------
for key, cfg in Apps
    Hotkey key, Launch.Bind(cfg)

Launch(cfg, *) {
    if WinExist(cfg["win"]) {
        WinActivate cfg["win"]
        WinWaitActive cfg["win"], , 3
        return
    }
    Run cfg["exe"]
}

^!x::ExitApp()
```

**要点**：`Launch.Bind(cfg)` 把配置绑进回调，避免为每个程序写一份重复代码。
`Launch(cfg, *)` 里的 `*` 用来吞掉 AHK 自动传进来的热键名参数。

## R2 · 窗口置顶开关

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

^!t:: {
    hwnd := WinExist("A")            ; "A" = 当前活动窗口
    if !hwnd
        return
    ex := WinGetExStyle("ahk_id " hwnd)
    on := !(ex & 0x8)                ; 0x8 = WS_EX_TOPMOST
    WinSetAlwaysOnTop on, "ahk_id " hwnd
    TrayTip on ? "已置顶" : "已取消置顶", "窗口置顶"
}

^!x::ExitApp()
```

## R3 · 一键左右分屏

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

^!Left:: {
    hwnd := WinExist("A")
    if !hwnd
        return
    WinRestore "ahk_id " hwnd        ; 最大化状态下无法移动，先还原
    WinMove 0, 0, A_ScreenWidth // 2, A_ScreenHeight, "ahk_id " hwnd
}

^!Right:: {
    hwnd := WinExist("A")
    if !hwnd
        return
    WinRestore "ahk_id " hwnd
    w := A_ScreenWidth // 2
    WinMove w, 0, A_ScreenWidth - w, A_ScreenHeight, "ahk_id " hwnd
}

^!x::ExitApp()
```

> 多显示器时 `WinMove` 的坐标是虚拟桌面绝对坐标，第二块屏的 X 可能是 1920 甚至负数。
> 想知道当前屏幕范围，用 `MonitorGet` / `MonitorGetWorkArea`（见 `api-index.md`）。

## R4 · 结束指定进程

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

Target := "notepad.exe"              ; ← 改这里

^!k:: {
    global Target
    pid := ProcessExist(Target)
    if !pid {
        TrayTip "没有在运行", Target
        return
    }
    ProcessClose pid
    ; 给点时间收尾；仍存在说明关不掉（可能是托盘程序或权限不足）
    ProcessWaitClose pid, 5
    TrayTip ProcessExist(Target) ? "关闭失败（试试管理员权限）" : "已关闭", Target
}

^!x::ExitApp()
```

## R5 · 定时器：周期任务

`SetTimer` 是让脚本"后台常驻干活"的标准手段。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

; ---------- 配置区 ----------
IntervalMin := 30                    ; ← 每多少分钟跑一次
LogFile := A_ScriptDir "\heartbeat.log"

SetTimer Heartbeat, IntervalMin * 60 * 1000
Heartbeat()                          ; 启动时先跑一次
Heartbeat() {
    global LogFile
    stamp := FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss")
    FileAppend stamp " 心跳`n", LogFile, "UTF-8"
}

^!x::ExitApp()
```

> **`SetTimer` 的第一个参数是函数对象**，直接写函数名（不加引号、不加括号）。
> 停掉定时器：`SetTimer Heartbeat, 0`。
> 临时停用整个脚本：`Pause(-1)`；`Suspend()` 只停热键、不停定时器。

## R6 · 定时关机 / 取消

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

DelaySec := 60                       ; ← 改这里

^!F9:: {
    global DelaySec
    Run A_ComSpec ' /c shutdown /s /t ' DelaySec ' /c "自动化脚本触发"', , "Hide"
    TrayTip DelaySec " 秒后关机，Ctrl+Alt+F10 取消", "关机"
}

^!F10::Run A_ComSpec " /c shutdown /a", , "Hide"

^!x::ExitApp()
```

其它常用开关（`Shutdown` 函数的 Flags 位掩码）：`1`=关机 `2`=重启 `4`=休眠 `8`=待机，
`Shutdown(1 | 4)` 表示关机并断电。

## R7 · 只在特定程序生效的热键

用 `#HotIf` 做上下文隔离。**每个条件段必须以空 `#HotIf` 收尾**，否则后面的热键全被带偏。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

; 记事本里：Ctrl+Alt+D 插入当前时间
#HotIf WinActive("ahk_exe notepad.exe")
^!d::SendText FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss")
#HotIf

; 资源管理器里：F2 仍是重命名，但 Ctrl+Alt+D 打开下载目录
#HotIf WinActive("ahk_class CabinetWClass")
^!d::Run EnvGet("USERPROFILE") "\Downloads"
#HotIf

^!x::ExitApp()
```

## R8 · 开机自启开关

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

Base := RegExReplace(A_ScriptName, "i)\.ahk$", "")
Lnk  := A_Startup "\" Base ".lnk"     ; A_Startup = 用户启动文件夹

^!a:: {
    global Lnk
    FileCreateShortcut A_ScriptFullPath, Lnk
    TrayTip "已加入开机自启", Lnk
}

^!r:: {
    global Lnk
    if FileExist(Lnk)
        FileDelete Lnk
    TrayTip "已移除开机自启", Base
}

^!x::ExitApp()
```

> 也可以手工操作：把 `.ahk` 或其快捷方式拖进 `Win+R` → `shell:startup` 打开的目录。
> 本配方的好处是**跟随脚本自身路径**，脚本挪了位置重新按一次 `Ctrl+Alt+A` 即可。

## R9 · 进程守护（退出就重开）

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

Target   := "notepad.exe"            ; ← 要守着的进程
Interval := 5000                     ; ← 检查间隔（毫秒）

SetTimer Guard, Interval
Guard() {
    global Target
    if !ProcessExist(Target) {
        Run Target
        TrayTip FormatTime(A_Now, "HH:mm:ss") " 已重新拉起", Target
    }
}

^!x::ExitApp()
```

> ⚠️ 别用来守护**你自己想手动关掉**的程序，否则关一次弹一次，很烦。
> 加个开关：`Suspend` + `#SuspendExempt` 可以让某个热键在挂起时仍然生效。

---

# 二、键鼠 / 热键 / 热字串

## R10 · 键位改绑

把 `CapsLock` 变成 `Ctrl` —— 打字最受益的一条改动。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

CapsLock::Ctrl                       ; 简单重映射：CapsLock 就是 Ctrl

; 想保留大小写锁定功能，就用组合键
^!CapsLock::SetCapsLockState "T"     ; T = 切换

; Win+C 打开计算器（Win+E 等系统组合键会被系统先吃掉，改非系统占用键更稳）
#c::Run "calc.exe"

^!x::ExitApp()
```

常用键名：`` ` ``（反引号是转义符，写成 ```` `` ````）、`Enter` `Esc` `Tab` `Space`
`Backspace` `Delete` `Insert` `Home` `End` `PgUp` `PgDn` `Up` `Down` `Left` `Right`
`WheelUp` `WheelDown` `MButton` `XButton1` `XButton2` `CapsLock` `F1`–`F24`。

## R11 · 连点器

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force
CoordMode "Mouse", "Screen"
SendMode "Input"

Interval := 120                      ; ← 点击间隔（毫秒）

^!q::ToggleClick()
^!x::ExitApp()

ToggleClick() {
    static on := false
    on := !on
    if on
        SetTimer DoClick, Interval
    else
        SetTimer DoClick, 0
    TrayTip on ? "连点开启（" Interval " ms）" : "连点停止", "连点器"
}

DoClick() {
    Click
}
```

> **把状态放在函数的 `static` 变量里**，比用全局变量干净得多（也不用满世界写 `global`）。
> 需要让连点在指定位置点击，用 `Click 500, 300` 或 `MouseClick "left", 500, 300`。

## R12 · 一键输入常用文本

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force
SendMode "Input"

^!1::SendText "这是一段常用回复内容"
^!2::SendText "订单号：20261013-001"

^!Enter:: {                          ; 输入后自动回车发出去
    SendText "已确认，请查收。"
    Send "{Enter}"
}

^!x::ExitApp()
```

> 单语句热键可以写在一行、省略花括号；多语句必须换行放进 `{ }`。

## R13 · 热字串：邮箱 / 日期 / 签名

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

; 立即触发（打出来就换，不用按空格）
:*:@@::me@example.com
:*:@@qq::12345678

; 按空格/回车后触发，替换成代码执行的结果
::/date::
{
    SendText FormatTime(A_Now, "yyyy-MM-dd")
}

::/time::
{
    SendText FormatTime(A_Now, "HH:mm")
}

; 多行文本替换
::sig::
(
此致
敬礼
)
```

> 触发词避免用 `dd`、`aa` 这类常见字母组合，否则正常打字也会被替换。
> 带 `/`、`;` 前缀的触发词不容易误触发。
> 热字串默认会先"退格删掉"已输入的触发词，所以不要用在会被程序拦截的输入框里。

## R14 · 滚轮与鼠标侧键

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

; Alt + 滚轮 = 调音量
!WheelUp::Send "{Volume_Up}"
!WheelDown::Send "{Volume_Down}"

; 鼠标侧键 = 浏览器前进/后退（多数软件通用）
XButton1::Send "{Browser_Back}"
XButton2::Send "{Browser_Forward}"

; Ctrl + 滚轮 = 缩放（很多软件自带，这里仅示范写法）
^WheelUp::Send "^{+}"
^WheelDown::Send "^{-}"

^!x::ExitApp()
```

## R15 · 固定操作序列宏

把一串重复操作打包成一个热键。核心是**每一步都等目标真的就绪**，而不是盲目 `Sleep`。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force
SetKeyDelay 30, 50
Win := "ahk_exe notepad.exe"         ; ← 目标窗口

^!m:: {
    global Win
    if !WinExist(Win) {
        Run "notepad.exe"
        WinWait Win, , 5
    }
    WinActivate Win
    WinWaitActive Win, , 3           ; 等窗口真的激活，别硬 Sleep

    SendText "标题行`n"
    Sleep 200
    SendText FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss") "`n"
    Sleep 200
    Send "^s"
    Sleep 500
    Send "{Enter}"                   ; 应对「另存为」之类的确认框
    TrayTip "操作序列执行完毕", "宏"
}

^!x::ExitApp()
```

> 需要更稳的宏：把每一步都包进 `try/catch` 并写日志，
> 出错时知道卡在第几步（见 `references/errors.md`）。

---

# 三、剪贴板 / 文本 / 文件

## R16 · 剪贴板清洗

复制来的文本常带多余空格、空行、软换行。这个配方**粘贴前先洗一遍**。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

^!v:: {
    ; 先存下原始剪贴板（含图片等非文本格式），出问题能还原
    saved := ClipboardAll()
    A_Clipboard := ""
    Send "^c"
    if !ClipWait(1) {
        TrayTip "没取到内容", "清洗失败"
        A_Clipboard := saved          ; 还原，别把用户剪贴板搞坏
        return
    }
    t := A_Clipboard
    t := StrReplace(t, "`r`n", "`n")
    t := RegExReplace(t, "[ `t]+", " ")      ; 连续空格/制表符折叠成一个空格
    t := RegExReplace(t, "`n{2,}", "`n")     ; 连续空行折叠成一个换行
    t := Trim(t)
    A_Clipboard := t
    Send "^v"
    TrayTip "已清洗（" StrLen(t) " 字符）", "剪贴板"
}

^!x::ExitApp()
```

## R17 · 多剪贴板历史

自动记住最近 10 条复制内容，`Ctrl+Alt+1` 取回最新一条。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

MaxKeep := 10                        ; ← 最多记几条
History := []

OnClipboardChange Collect            ; 剪贴板一变就记下来
Collect(type) {
    global History, MaxKeep
    if (type != 1)                   ; 1 = 文本；2 = 图片等非文本
        return
    s := A_Clipboard
    if (s = "")
        return
    if (History.Length && s = History[History.Length])
        return                       ; 和最新一条相同就不重复记
    History.Push(s)
    if (History.Length > MaxKeep)
        History.RemoveAt(1)
}

^!1::SendText HistoryAt(1)           ; 最新
^!2::SendText HistoryAt(2)
^!3::SendText HistoryAt(3)

^!x::ExitApp()

HistoryAt(n) {
    global History
    if (History.Length < n)
        return ""
    return History[History.Length - n + 1]
}
```

## R18 · 选中文字 → 搜索

通用套路：**选中 → `Ctrl+C` → 拿剪贴板 → 拼 URL → 打开浏览器**。
难点是把中文正确转成 URL 编码（要用 UTF-8 字节，不是字符码）。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

; ---------- 配置区 ----------
SearchURL := "https://www.bing.com/search?q="      ; ← 换成百度/谷歌都行

^!g:: {
    global SearchURL
    txt := GetSelection()
    if (Trim(txt) = "") {
        TrayTip "没有选中内容", "搜索"
        return
    }
    Run SearchURL UrlEncode(Trim(txt))
}

; 取当前选中文本，并还原剪贴板
GetSelection() {
    saved := ClipboardAll()
    A_Clipboard := ""
    Send "^c"
    ok := ClipWait(1)
    txt := ok ? A_Clipboard : ""
    A_Clipboard := saved
    return txt
}

; 按 UTF-8 字节做百分号编码（中文才能被正确识别）
UrlEncode(s) {
    n := StrPut(s, "UTF-8") - 1               ; 不含结尾的 0
    buf := Buffer(n + 1)
    StrPut s, buf, "UTF-8"
    out := ""
    Loop n {
        b := NumGet(buf, A_Index - 1, "UChar")
        if (b >= 0x41 && b <= 0x5A) || (b >= 0x61 && b <= 0x7A) || (b >= 0x30 && b <= 0x39)
            out := out Chr(b)
        else if (b = 0x2D || b = 0x5F || b = 0x2E || b = 0x7E)   ; - _ . ~ 不编码
            out := out Chr(b)
        else
            out := out "%" Format("{1:02X}", b)
    }
    return out
}

^!x::ExitApp()
```

> 换搜索引擎只改 `SearchURL`。加一个翻译配方同理，
> 例如 `https://translate.google.com/?text=`。

## R19 · 批量重命名

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

Dir   := A_Desktop "\待整理"         ; ← 目标目录
Ext   := "*.txt"                     ; ← 文件类型

^!n:: {
    global Dir, Ext
    if !DirExist(Dir) {
        TrayTip "目录不存在", Dir
        return
    }
    stamp := FormatTime(A_Now, "yyyyMMdd_HHmmss")
    n := 0
    Loop Files, Dir "\" Ext {
        SplitPath A_LoopFilePath, , , , &nameNoExt
        target := Dir "\" stamp "_" (n + 1) "_" nameNoExt "." A_LoopFileExt
        FileMove A_LoopFileFullPath, target
        n += 1
    }
    TrayTip Format("已重命名 {1} 个文件", n), "批量重命名"
}

^!x::ExitApp()
```

> **为什么要加时间戳前缀**：如果新名字可能和老名字撞车（比如把 `a.txt` 改成 `1_a.txt`），
> 边遍历边改名会让后面的文件读到已经改过的名字。加一个绝不会重复的前缀最省事。
> 想先预演，把 `FileMove` 换成 `FileAppend A_LoopFileFullPath " → " target "`n", A_ScriptDir "\rename-preview.txt", "UTF-8"`。

## R20 · 文件夹监听（新文件出现就处理）

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

WatchDir := A_Desktop "\监视"        ; ← 监视哪个目录
LogFile  := A_ScriptDir "\watch.log"

if !DirExist(WatchDir)
    DirCreate WatchDir

SetTimer Scan, 3000                  ; 每 3 秒扫一次
Scan() {
    global WatchDir, LogFile
    static firstRun := true
    static seen := Map()
    Loop Files, WatchDir "\*.*" {
        p := A_LoopFileFullPath
        if seen.Has(p)
            continue
        seen[p] := true
        if !firstRun                  ; 首次扫描只登记，不处理历史文件
            HandleNewFile(p, LogFile)
    }
    firstRun := false
}

HandleNewFile(path, logFile) {
    stamp := FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss")
    FileAppend stamp " 发现 " path "`n", logFile, "UTF-8"
}

^!x::ExitApp()
```

> 这是**轮询**方案，简单可靠。要毫秒级实时，得用
> `ReadDirectoryChangesW`（`DllCall`），复杂度高很多，日常场景不必。
> 监听网络盘或大量文件时，把间隔调大到 10 秒以上，别让磁盘一直转。

## R21 · 批量文本替换

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

Dir  := A_Desktop "\替换测试"        ; ← 目标目录
From := "旧公司名"                   ; ← 被替换的文字
To   := "新公司名"                   ; ← 替换成的文字

^!r:: {
    global Dir, From, To
    if !DirExist(Dir) {
        TrayTip "目录不存在", Dir
        return
    }
    n := 0
    Loop Files, Dir "\*.txt" {
        path := A_LoopFileFullPath
        try
            txt := FileRead(path, "UTF-8")
        catch {
            continue                     ; 读不了就跳过，别让整个任务崩掉
        }
        if !InStr(txt, From)
            continue
        FileCopy path, path ".bak", 1    ; 先备份再写，出事能回退
        f := FileOpen(path, "w", "UTF-8")
        f.Write(StrReplace(txt, From, To))
        f.Close()
        n += 1
    }
    TrayTip Format("已处理 {1} 个文件（原文件备份为 .bak）", n), "批量替换"
}

^!x::ExitApp()
```

> **坑点**：`FileAppend` 是"追加"不是"覆盖"，直接用它改写文件会把内容翻倍。
> 要覆盖就用 `FileOpen(path, "w", "UTF-8")`（`w` 模式会先清空文件）。
> 另外**写文件一定要带编码参数**：不写 `"UTF-8"` 会按系统 ANSI 码页写，中文直接变乱码（实测）。

## R22 · CSV / 日志逐行处理

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

Src := A_ScriptDir "\input.csv"      ; ← 输入文件
Dst := A_ScriptDir "\output.csv"     ; ← 输出文件

^!c:: {
    global Src, Dst
    if !FileExist(Src) {
        TrayTip "找不到输入文件", Src
        return
    }
    out := ""
    Loop Read, Src {                 ; 逐行读，不用一次全load 进内存
        line := A_LoopReadLine
        if (A_Index = 1) {           ; 表头原样保留
            out := out line "`n"
            continue
        }
        if (Trim(line) = "")
            continue
        parts := StrSplit(line, ",")
        if (parts.Length < 3)
            continue                 ; 列数不对的行丢掉
        out := out Trim(parts[1]) "," Trim(parts[3]) "`n"
    }
    FileDelete Dst
    FileAppend out, Dst, "UTF-8"
    TrayTip "处理完成", Dst
}

^!x::ExitApp()
```

> 逗号分隔的朴素解析够用就行。**CSV 里有引号包裹的逗号**（如 `"张,三",25`）时，
> 需要按引号状态机解析 —— 那种情况建议用 `RegExMatch` 或干脆交给 PowerShell：
> `Import-Csv` 一条就解决了。

---

# 四、截图 / 找图找色 / 网络

## R23 · 截图（全屏 / 区域 / 窗口）

**AHK 没有原生截图函数**。本 skill 自带一个零依赖片段
`scripts/snippets/screenshot.ahk`（内嵌 PowerShell + .NET），支持全屏、指定区域、
指定窗口（**含浏览器等硬件加速窗口**，用 `PrintWindow` 的 `PW_RENDERFULLCONTENT` 标志）。

它对外提供 4 个函数：

| 函数 | 说明 |
|---|---|
| `CaptureFullScreen(outPath?)` | 全屏，返回保存路径 |
| `CaptureRegion(x, y, w, h, outPath?)` | 指定区域 |
| `CaptureWindow(winTitle?, outPath?)` | 指定窗口（默认 `"A"` 活动窗口），找不到会抛 `TargetError` |
| `CaptureToClipboard()` | 全屏截图进剪贴板，可直接粘贴 |

默认存到脚本同目录的 `screenshots\` 下，文件名带时间戳。

**独立使用**（片段自带热键和自测入口）：

```bash
# 自测：截一张全屏并打印路径
"C:\Program Files\AutoHotkey\v2\AutoHotkey.exe" "路径\snippets\screenshot.ahk" test
```

**作为库引入自己的脚本**（注意避开片段里已占用的 `^!s` `^!a` `^!r` `^!c` `^!x`）：

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force
#Include "%A_ScriptDir%\snippets\screenshot.ahk"

^!F5::TrayTip "已保存", CaptureFullScreen()
^!F6::TrayTip "已保存", CaptureWindow("A")
^!F7::TrayTip "已保存", CaptureRegion(0, 0, 800, 600)
```

> 需要**高频截图**或更专业的窗口截图时，换
> [Buzzerb/AHKv2-Screenshot-Tools](https://github.com/Buzzerb/AHKv2-Screenshot-Tools)
> （纯 AHK v2 + GDI+，截图在本进程内完成，没有 PowerShell 启动开销）。

## R24 · 找色点击

找到屏幕上某颜色的像素并点它。常用于点没标题、只有图标颜色的按钮。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force
CoordMode "Pixel", "Screen"
CoordMode "Mouse", "Screen"

TargetColor := 0xE01B24              ; ← 目标颜色，注意是 0xBBGGRR（不是 RGB！）
Tolerance   := 12                    ; ← 允许的色差，0~255

^!f:: {
    global TargetColor, Tolerance
    if PixelSearch(&px, &py, 0, 0, A_ScreenWidth, A_ScreenHeight, TargetColor, Tolerance) {
        MouseMove px, py, 5
        Sleep 120
        Click
        TrayTip Format("已点击 ({1}, {2})", px, py), "找色点击"
    } else {
        TrayTip "没找到目标颜色", "找色点击"
    }
}

^!x::ExitApp()
```

> **颜色字节序**：AHK 用 `0xBBGGRR`。网页/CSS 里的 `#RRGGBB` 要手动颠倒，
> 例如红色 `#E01B24` → `0x241BE0`。取色最省事的办法是用 `PixelGetColor(x, y)`
> 先打印出来看看。
>
> **加速技巧**：别每次都全屏搜。把搜索范围缩小到按钮所在的区域
> （例如右下角 `A_ScreenWidth - 300, A_ScreenHeight - 200, A_ScreenWidth, A_ScreenHeight`），
> 速度能快几十倍。

## R25 · 找图点击

比找色稳得多 —— 不依赖颜色数值，直接匹配图案。

**准备工作**：先用截图工具把目标按钮截成一个小 PNG，存成脚本同目录的 `target.png`。
截图时**只截按钮本身**，不要带周围背景，不然屏幕分辨率或主题一变就匹配不上。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force
CoordMode "Pixel", "Screen"
CoordMode "Mouse", "Screen"

Image     := A_ScriptDir "\target.png"   ; ← 目标图片
Variation := 30                          ; ← 允许的色差（0~255）

^!i:: {
    global Image, Variation
    if !FileExist(Image) {
        TrayTip "缺少图片文件", Image
        return
    }
    if ImageSearch(&ix, &iy, 0, 0, A_ScreenWidth, A_ScreenHeight, "*" Variation " " Image) {
        MouseMove ix, iy, 5
        Sleep 120
        Click
        TrayTip Format("已点击 ({1}, {2})", ix, iy), "找图点击"
    } else {
        TrayTip "屏幕上没找到该图片", "找图点击"
    }
}

^!x::ExitApp()
```

> `"*30 target.png"` 里的 `*30` 就是色差容差。太低匹配不上（颜色有细微差别），
> 太高会误匹配。先设为 0 试，匹配不上再逐步加。
> 还能加 `*TransBlack` 之类选项让纯黑像素透明，适合图标背景不定的场景。

## R26 · 调用 HTTP 接口取 JSON

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

Url := "https://api.github.com/repos/AutoHotkey/AutoHotkey"   ; ← 改这里

^!h:: {
    global Url
    try
        data := HttpGet(Url)
    catch as e {
        TrayTip "请求失败：" e.Message, "HTTP"
        return
    }
    if RegExMatch(data, '"stargazers_count"\s*:\s*(\d+)', &m)
        TrayTip "Star 数：" m[1], "GitHub"
    else
        TrayTip "没解析到目标字段", "HTTP"
}

HttpGet(url) {
    whr := ComObject("WinHttp.WinHttpRequest.5.1")
    whr.Open("GET", url, false)              ; false = 同步等待
    whr.SetRequestHeader("User-Agent", "AutoHotkey-v2")   ; 不少 API 要求带 UA
    whr.Send()
    if (whr.Status != 200)
        throw Error("HTTP " whr.Status " " whr.StatusText)
    return whr.ResponseText
}

^!x::ExitApp()
```

> **不做完整 JSON 解析**：AHK 没有内置 JSON 库，用 `RegExMatch` 掏一两个字段最省事。
> 需要完整解析时，两条路：
> ① 用 `ComObject("MSScriptControl.ScriptControl")` 借 JScript 的 `eval` 解析（32 位才稳）；
> ② 调 PowerShell：`ConvertFrom-Json` 然后取字段。
> 发 POST 请求就是多加一行 `whr.SetRequestHeader("Content-Type", "application/json")`
> 和 `whr.Send('{"key":"value"}')`。

## R27 · 下载文件

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

Url := "https://www.autohotkey.com/download/ahk-v2.exe"   ; ← 改这里
Dst := A_ScriptDir "\ahk-v2.exe"                          ; ← 存到哪

^!d:: {
    global Url, Dst
    if FileExist(Dst)
        FileDelete Dst
    try
        Download Url, Dst
    catch as e {
        TrayTip "下载失败：" e.Message, "下载"
        return
    }
    size := Round(FileGetSize(Dst) / 1024, 1)
    TrayTip Format("已下载 {1} KB", size), "下载完成"
}

^!x::ExitApp()
```

> `Download` **不支持**自定义请求头、POST、代理、超时。需要这些就用 R26 的
> `WinHttp.WinHttpRequest.5.1`，把 `whr.ResponseBody` 写进文件即可。

## R28 · 定时截图存档（延时摄影）

每 30 秒截一次屏，文件名带时间戳，攒成一份操作记录。

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force
#Include "%A_ScriptDir%\snippets\screenshot.ahk"

OutDir   := A_ScriptDir "\timelapse"     ; ← 存到哪
Interval := 30 * 1000                    ; ← 每隔多久截一张（毫秒）

if !DirExist(OutDir)
    DirCreate OutDir

SetTimer Shot, Interval
Shot() {
    global OutDir
    p := OutDir "\shot_" FormatTime(A_Now, "yyyyMMdd_HHmmss") ".png"
    CaptureFullScreen(p)
}

^!F4::TrayTip "开始存档（每 " Interval // 1000 " 秒一张）", "延时摄影"
^!F3:: {
    SetTimer Shot, 0
    TrayTip "已停止存档", "延时摄影"
}
; 逃生热键 ^!x 由截图片段自己提供，这里不要再定义一遍（会报 Duplicate hotkey）
```

> 长时间跑会占不少磁盘：全屏 PNG 一张约 400 KB，一张/30 秒 ≈ 每小时 48 MB。
> 建议配合清理：`FileRecycle` 而不是 `FileDelete`，误删还能从回收站捞回来。

---

## R29 · 命令文件驱动批量桌面操作（免重写脚本）

> 场景：要操作一个**只有 GUI、没有 API** 的程序，动作多、还要反复试错 ——
> 点错一下就得改脚本重跑。这时别一步写一个 `.ahk`，改用
> `scripts/delivered/cmd_driver.ahk`：**脚本固定，动作全写在纯文本命令文件里**，
> 改动作只改文本，脚本不用动。

**固定脚本**（技能内已交付，直接调用，不要复制一份出去）：

```
C:\Users\Administrator\.workbuddy\skills\autohotkey-v2-yashu\scripts\delivered\cmd_driver.ahk
```

**跑一条动作序列**：

```bash
AHK="C:/Program Files/AutoHotkey/v2/AutoHotkey.exe"
D="C:/Users/Administrator/.workbuddy/skills/autohotkey-v2-yashu/scripts/delivered/cmd_driver.ahk"
"$AHK" "$D" "D:/temp/steps.txt" "ahk_exe Doubao.exe" "D:/temp/steps.log"
```

命令文件（存 UTF-8，一行一条，`;` 开头是注释）：

```
activate                      ; 不带参数 → 用命令行第 2 个参数指定的窗口
sleep|800                     ; 等窗口渲染完再截图
shot|D:\temp\s01.png          ; 全屏截图，等到文件真出现才返回
click|1795|983                ; 屏幕绝对坐标点左键
typefile|D:\temp\prompt.txt   ; 长文本从文件发，绕开 | 与换行问题
key|{Enter}
probe                         ; 把当前前台窗口标题、鼠标坐标写进日志
```

完整命令表见脚本头部注释（`activate / move / click / dblclick / wheel / type /
typefile / key / sleep / shot / probe / log`）。

**三条调用侧硬经验（都是实测踩出来的）**：

| # | 经验 | 不遵守的后果 |
|---|---|---|
| 1 | **`shot` 之前必须先 `activate`** | 目标窗口不在前台时，全屏截图拍到的是遮挡它的窗口 ⇒ 从图里量出的"按钮坐标"全错，**且不报任何错** |
| 2 | **pwsh/bash 里 `& 解释器.exe 脚本.ahk` 不等待 GUI 程序** | 命令立刻返回、退出码为空，看着像"没跑"，其实还在跑。**判完成看产物文件**：先删旧产物，再轮询等它出现（本机实测截屏约 4~5 秒落盘） |
| 3 | **命令文件必须存 UTF-8** | 存成 ANSI/GBK 时，中文参数进脚本变乱码，命令静默失效 |

**定位按钮：优先 OCR，别硬估坐标**。先 `activate` + `shot` 截全屏，把图交给本地 OCR
（本机 `rapidocr-local-ocr` 技能），直接拿到「文字 + 屏幕绝对坐标」，点文字中心即可 ——
按钮改名、多语言、多行折行都不会错位。比按底色扫像素（R24）稳，颜色会被主题和高亮态改变。

**要加一条新命令**：在 `ExecCmd()` 里加一个 `case`，再写个 `DoXxx(Parts)` 函数；
`Parts[1]` 是命令名，`Parts[2..]` 是参数。文本类参数用 `JoinParts(Parts, 2)` 拼回，
这样参数里含 `|` 也不会被截断。

---

# 附录 · 非阻塞提示的几种写法

调试和反馈**都不要用 `MsgBox`**（模态，会卡住脚本等人点击）。按场景选：

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force

^!1::TrayTip "任务完成", "标题"                 ; 右下角气泡，非阻塞，最常用
^!2::OutputDebug "数值 x=" 42                   ; 输出到调试器（DebugView），用户看不见
^!3::FileAppend FormatTime(A_Now, "HH:mm:ss") " 有进展`n", A_ScriptDir "\debug.log", "UTF-8"
^!4::SoundBeep 500, 800                         ; 响一声：注意 v2 是 (时长, 频率)

^!x::ExitApp()
```

> ⚠️ **`SoundBeep` 的参数顺序在 v2 里和 v1 相反**：
> v1 是 `SoundBeep, Frequency, Duration`，v2 是 `SoundBeep(Duration, Frequency)`。
> 写反了不会报错，只是声音长短和音高都变奇怪。

# 附录 · 给配方加个"自测入口"

配方是完整脚本，加了自测入口之后就能被 `ahk_run.py` 真跑验证，而不是只做语法检查：

```ahk
#Requires AutoHotkey v2.0
#SingleInstance Force
SetWorkingDir A_ScriptDir

Config := "演示用的配置"        ; ← 顶层只放真正需要共享的配置

^!s::DoWork(Config)

DoWork(input) {
    return StrUpper(input)      ; 核心逻辑抽成纯函数
}

; ---- 自测入口：命令行传 test 时只跑验证，立即退出 ----
if (A_Args.Length && A_Args[1] = "test") {
    SelfTest()
}

SelfTest() {
    ; 自测逻辑必须包进函数，否则它的变量会变成全局变量、污染脚本（--strict 会报出来）
    FileAppend "结果：" DoWork("样例输入"), "*"
    ExitApp(0)
}

^!x::ExitApp()
```

跑法：

```bash
python "$S/scripts/ahk_run.py" "D:\temp\我的脚本.ahk" --timeout 6 test
```

> 三条注意：① 自测代码**必须包在函数里**；② 用 `FileAppend(..., "*")` 输出结果给试跑器看；
> ③ 自测涉及文件/截图时指向**临时目录**，别动真实数据。

# 附录 · 写配方时最容易翻车的 6 件事

| # | 翻车点 | 正确做法 |
|---|---|---|
| 1 | 把 `Send` 当文本发送器 | 文本一律 `SendText`。`Send "a!b"` 会把 `!` 当 Alt |
| 2 | 用 `%` 取余 | v2 里 `%` 不能当运算符，用 `Mod(a, b)` |
| 3 | 花括号里塞单行语句 | `if (x) { y := 1 }` 直接报错；`{` 之后必须换行 |
| 4 | 用 v1 旧函数名 | 如 `StringReplace` / `IfWinExist` / `GetPixelColor` —— 官方校验器**只报警告不报错**，会放你过去 |
| 5 | 改动文件用 `FileAppend` | 它是追加！覆盖要用 `FileOpen(path, "w", "UTF-8")` |
| 6 | 颜色字节序搞反 | AHK 是 `0xBBGGRR`，CSS 是 `#RRGGBB`，得颠倒 |

出错后按报错消息反查根因 → 见 `references/errors.md`。
