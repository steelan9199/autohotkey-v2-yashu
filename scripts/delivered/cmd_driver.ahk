#Requires AutoHotkey v2.0
#SingleInstance Force
SendMode "Input"
SetWorkingDir A_ScriptDir
CoordMode "Mouse", "Screen"
CoordMode "Pixel", "Screen"
SetKeyDelay 30, 20
SetMouseDelay 20

; ============================================================================
; cmd_driver —— 命令文件驱动的桌面操作执行器
; ----------------------------------------------------------------------------
; 干什么：把「每次自动化都新写一个 .ahk」换成「写一个纯文本命令文件」。
;         键鼠 / 窗口 / 截图 / 日志全部由本脚本解释执行，改动作不用改脚本。
;         适合多步、反复试错的场景（如操作某个只有 GUI、没有 API 的客户端）。
;
; 用法：
;   AutoHotkey.exe cmd_driver.ahk <命令文件> [目标窗口] [日志文件]
;
;   <命令文件>  每行一条命令，字段用 | 分隔；; 开头是注释；空行忽略
;   [目标窗口]  可选。activate 不带参数时激活它，可写 "ahk_exe Doubao.exe"、
;               "ahk_class Notepad" 或窗口标题的一部分；省略则 activate 必须带参数
;   [日志文件]  可选。默认 <脚本目录>\cmd_driver.log
;
; 命令表：
;   activate[|窗口]   激活窗口到前台（不带参数时用命令行第 2 个参数）
;   move|x|y          鼠标移到屏幕绝对坐标
;   click|x|y         左键单击
;   dblclick|x|y      左键双击
;   wheel|x|y|n       鼠标移到 (x,y) 后滚轮 n 格（n>0 下滚，n<0 上滚）
;   type|文本         发送文本（SendText，不会被当成按键解析；文本含 | 也能正确发送）
;   typefile|路径     发送文件全文（文本极长或含换行时用它）
;   key|按键          发送按键，如 {Enter} / ^a / ^s / {Tab} / {Esc}
;   sleep|毫秒        等待
;   shot|png路径      全屏截图（内部借 PowerShell + .NET，等到文件真出现为止）
;   probe             记录当前前台窗口标题与鼠标坐标
;   log|文本          写一行自定义日志
;
; 三条硬经验（都是实测踩出来的，违反任一条都会静默跑偏）：
;   1) 截图前必须先 activate —— 目标窗口不在前台时，全屏截图拍到的是遮挡它的窗口，
;      拿到的"按钮坐标"全是错的，而且不报任何错。
;   2) 命令文件必须存 UTF-8 —— 存成 ANSI/GBK 时中文参数会变乱码。
;   3) 调用侧（pwsh / bash）用 & 启 GUI 程序不会等待 —— 判完成别看退出码，
;      看产物文件（如截图 PNG）是否生成；先删旧产物再轮询最稳。
;
; 坐标：全部是屏幕绝对坐标（CoordMode "Mouse","Screen"）。多屏时以主屏左上为原点。
;
; 定位按钮的两条路（按优先级）：
;   ① OCR：先 activate + shot 截图，再用本地 OCR 拿「文字 + 屏幕绝对坐标」，
;      直接点文字中心 —— 别名/多语言/换行都不会错位，是最省心的方式；
;   ② 找色：PixelSearch 按按钮底色扫描（见 recipes.md 的 R24 找色点击）。
;
; 自测： AutoHotkey.exe cmd_driver.ahk test    → 只验解析与分发，不动键鼠
;
; 逃生： Ctrl+Alt+X
; ============================================================================

LogPath := ""
TargetWin := ""

if (A_Args.Length >= 1 && A_Args[1] = "test") {
    ExitApp SelfTest()
}

if (A_Args.Length < 1) {
    FileAppend "ERR 缺少命令文件参数`n用法: cmd_driver.ahk <命令文件> [目标窗口] [日志文件]`n", "*"
    ExitApp 1
}

CmdFile := A_Args[1]
TargetWin := A_Args.Length >= 2 ? A_Args[2] : ""
LogPath := A_Args.Length >= 3 ? A_Args[3] : A_ScriptDir "\cmd_driver.log"

if !FileExist(CmdFile) {
    FileAppend "ERR 命令文件不存在: " CmdFile "`n", "*"
    ExitApp 1
}

Log("=== START " FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss") " file=" CmdFile " ===")

Lines := StrSplit(FileRead(CmdFile, "UTF-8"), "`n", "`r")
for Idx, RawLine in Lines {
    Line := Trim(RawLine)
    if (Line = "" || SubStr(Line, 1, 1) = ";")
        continue
    Parts := StrSplit(Line, "|")
    Cmd := Trim(Parts[1])
    try {
        ExecCmd(Cmd, Parts)
    } catch as e {
        Log("ERROR @" Idx " [" Cmd "] " e.Message)
    }
}

Log("=== DONE ===")
ExitApp 0

; ---------------------------- 命令分发 ----------------------------

ExecCmd(Cmd, Parts) {
    switch Cmd {
        case "activate":
            DoActivate(Parts)
        case "move":
            DoMove(Parts)
        case "click":
            DoClick(Parts, false)
        case "dblclick":
            DoClick(Parts, true)
        case "wheel":
            DoWheel(Parts)
        case "type":
            DoType(Parts)
        case "typefile":
            DoTypeFile(Parts)
        case "key":
            Send(JoinParts(Parts, 2))
            Sleep 200
            Log("key " JoinParts(Parts, 2))
        case "sleep":
            Sleep Integer(Trim(Parts[2]))
        case "shot":
            DoShot(Parts)
        case "probe":
            DoProbe()
        case "log":
            Log(Parts.Length >= 2 ? JoinParts(Parts, 2) : "")
        default:
            Log("UNKNOWN cmd: " Cmd)
    }
}

; ---------------------------- 动作实现 ----------------------------

DoActivate(Parts) {
    W := Parts.Length >= 2 ? Trim(Parts[2]) : TargetWin
    if (W = "")
        throw Error("activate 未指定窗口（用 activate|<窗口> 或命令行第 2 参数）")
    if !WinExist(W)
        throw Error("找不到窗口: " W)
    WinRestore W
    WinActivate W
    WinWaitActive W, , 3
    Sleep 400
    Log("activate ok -> " W)
}

DoMove(Parts) {
    MouseMove Integer(Trim(Parts[2])), Integer(Trim(Parts[3])), 0
    Sleep 120
    Log("move -> " Trim(Parts[2]) "," Trim(Parts[3]))
}

DoClick(Parts, Dbl) {
    MouseMove Integer(Trim(Parts[2])), Integer(Trim(Parts[3])), 0
    Sleep 150
    Click()
    if Dbl {
        Sleep 80
        Click()
    }
    Sleep 200
    Log("click -> " Trim(Parts[2]) "," Trim(Parts[3]) (Dbl ? " x2" : ""))
}

DoWheel(Parts) {
    MouseMove Integer(Trim(Parts[2])), Integer(Trim(Parts[3])), 0
    Sleep 150
    N := Integer(Trim(Parts[4]))
    Key := N > 0 ? "WheelDown" : "WheelUp"
    Count := N > 0 ? N : -N
    Loop Count {
        Send "{" Key "}"
        Sleep 50
    }
    Log("wheel -> " Key " x" Count)
}

DoType(Parts) {
    Txt := JoinParts(Parts, 2)
    SendText Txt
    Sleep 120
    Log("type len=" StrLen(Txt))
}

DoTypeFile(Parts) {
    Path := Trim(Parts[2])
    if !FileExist(Path)
        throw Error("文本文件不存在: " Path)
    SendText FileRead(Path, "UTF-8")
    Sleep 200
    Log("typefile " Path)
}

DoProbe() {
    MouseGetPos &mx, &my
    Log("probe active='" WinGetTitle("A") "' mouse=" mx "," my " screen=" A_ScreenWidth "x" A_ScreenHeight)
}

; ---------------------------- 截图（PowerShell + .NET，零依赖） ----------------------------

DoShot(Parts) {
    Out := Trim(Parts[2])
    OutDir := SubStr(Out, 1, InStr(Out, "\", , -1) - 1)
    if (OutDir && !DirExist(OutDir))
        DirCreate OutDir
    Ps := "
    (
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
`$b = [System.Windows.Forms.Screen]::PrimaryScreen.Bounds
`$bmp = New-Object System.Drawing.Bitmap(`$b.Width, `$b.Height)
`$g = [System.Drawing.Graphics]::FromImage(`$bmp)
`$g.CopyFromScreen(`$b.X, `$b.Y, 0, 0, `$bmp.Size)
`$g.Dispose()
`$bmp.Save('@@OUT@@', [System.Drawing.Imaging.ImageFormat]::Png)
`$bmp.Dispose()
)"
    Ps := StrReplace(Ps, "@@OUT@@", Out)
    PsFile := A_Temp "\cmd_driver_" A_TickCount ".ps1"
    f := FileOpen(PsFile, "w", "UTF-8")
    f.Write(Ps)
    f.Close()
    if FileExist(Out)
        try FileDelete Out
    try {
        Run A_ComSpec ' /c powershell -NoProfile -ExecutionPolicy Bypass -File "' PsFile '"', , "Hide"
        Ok := 0
        Loop 60 {
            Sleep 100
            if FileExist(Out) {
                Ok := 1
                break
            }
        }
        Log("shot " Out " ok=" Ok)
    } finally {
        Sleep 150
        try FileDelete PsFile
    }
}

; ---------------------------- 工具函数 ----------------------------

; 把 Parts 从 StartIdx 起用 | 重新拼回（这样 type/log 的文本里含 | 也不会被截断）
JoinParts(Parts, StartIdx) {
    S := ""
    Loop Parts.Length - StartIdx + 1 {
        i := StartIdx + A_Index - 1
        S .= (A_Index = 1 ? "" : "|") Parts[i]
    }
    return S
}

Log(Msg) {
    global LogPath
    FileAppend FormatTime(A_Now, "HH:mm:ss") " " Msg "`n", LogPath, "UTF-8"
}

; ---------------------------- 自测（不动键鼠，只跑无副作用命令） ----------------------------

SelfTest() {
    global LogPath
    TmpLog := A_Temp "\cmd_driver_selftest.log"
    LogPath := TmpLog
    if FileExist(TmpLog)
        FileDelete TmpLog

    Cases := ["log|selftest-start", "log|含竖线|的文本", "sleep|10", "probe", "no-such-cmd|x"]
    for i, C in Cases {
        P := StrSplit(C, "|")
        ExecCmd(Trim(P[1]), P)
    }

    Txt := FileRead(TmpLog, "UTF-8")
    Ok := (InStr(Txt, "selftest-start") > 0)
    Ok := Ok && (InStr(Txt, "含竖线|的文本") > 0)
    Ok := Ok && (InStr(Txt, "probe active=") > 0)
    Ok := Ok && (InStr(Txt, "UNKNOWN cmd") > 0)
    FileAppend((Ok ? "SELFTEST OK`n" : "SELFTEST FAIL`n") Txt, "*")
    try FileDelete TmpLog
    return Ok ? 0 : 1
}

; ---------------------------- 逃生热键 ----------------------------

^!x::ExitApp()
