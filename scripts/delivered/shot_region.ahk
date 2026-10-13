#Requires AutoHotkey v2.0
#SingleInstance Force
SendMode "Input"
SetWorkingDir A_ScriptDir

; ============================================================================
; 屏幕指定区域截图
;   区域：左上角 (15, 163)  →  右下角 (160, 193)   即 145 x 30 像素
; ----------------------------------------------------------------------------
; 用法：
;   双击本脚本        → 立即截取该区域，PNG 存到 screenshots\ 目录并弹提示
;   Ctrl+Alt+R        → 再截一张（脚本常驻后可用）
;   Ctrl+Alt+X        → 退出脚本
;   自测：AutoHotkey.exe shot_region.ahk test
;
; 实现：借系统 PowerShell + .NET Graphics.CopyFromScreen 抓屏，零第三方依赖。
; 归档：交付成品，位于 scripts\delivered\。改动后同步更新 SKILL.md 第 5 节台账。
; ============================================================================

; ---------- 配置区 ----------
BOX       := {x1: 15, y1: 163, x2: 160, y2: 193}      ; 左上角 → 右下角
SHOT_DIR  := A_ScriptDir "\screenshots"

PS_REGION := "
(
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b = New-Object Drawing.Bitmap(@@W@@, @@H@@)
$g = [Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen(@@X@@, @@Y@@, 0, 0, $b.Size)
$g.Dispose()
$b.Save('@@OUT@@', [Drawing.Imaging.ImageFormat]::Png)
$b.Dispose()
)"

; ---------- 入口 ----------
if (A_Args.Length && A_Args[1] = "test") {
    SelfTest()
} else {
    TrayTip(CaptureBox(), "截图已保存 · Ctrl+Alt+X 退出")
}

; ---------- 热键区 ----------
^!r::TrayTip(CaptureBox(), "截图已保存 · Ctrl+Alt+X 退出")
^!x::ExitApp()

; ---------- 主流程 ----------

; 按配置的 BOX 截一张，返回图片路径
CaptureBox() {
    global BOX
    return CaptureRegion(BOX.x1, BOX.y1, BOX.x2, BOX.y2)
}

; 截取 [x1,y1]-[x2,y2] 矩形区域；outPath 省略则自动生成到 SHOT_DIR
CaptureRegion(x1, y1, x2, y2, outPath := "") {
    global SHOT_DIR, PS_REGION
    if (outPath = "") {
        if !DirExist(SHOT_DIR)
            DirCreate SHOT_DIR
        outPath := SHOT_DIR "\region_" FormatTime(A_Now, "yyyyMMdd_HHmmss") ".png"
    }
    try FileDelete outPath

    ps := StrReplace(PS_REGION, "@@X@@", x1)
    ps := StrReplace(ps, "@@Y@@", y1)
    ps := StrReplace(ps, "@@W@@", x2 - x1)
    ps := StrReplace(ps, "@@H@@", y2 - y1)
    ps := StrReplace(ps, "@@OUT@@", outPath)
    RunPs ps

    if !FileExist(outPath)
        throw Error("截图失败，未生成文件：" outPath)
    return outPath
}

; ---------- 内部工具 ----------

; 优先用 PowerShell 7（pwsh），找不到再退回系统 Windows PowerShell 5.1
FindPsExe() {
    for p in ["D:\software\PowerShell\7\pwsh.exe", A_WinDir "\System32\WindowsPowerShell\v1.0\powershell.exe"] {
        if FileExist(p)
            return p
    }
    return "powershell.exe"
}

RunPs(script) {
    psFile := A_Temp "\ahk_shot_" A_TickCount ".ps1"
    f := FileOpen(psFile, "w", "UTF-8")     ; 带 BOM，保证 PowerShell 正确读中文路径
    f.Write(script)
    f.Close()
    try {
        RunWait '"' FindPsExe() '" -NoProfile -ExecutionPolicy Bypass -File "' psFile '"', , "Hide"
    } finally {
        Sleep 200
        try FileDelete psFile
    }
}

; ---------- 自测入口（不碰真实输出目录）----------
SelfTest() {
    testPath := A_Temp "\ahk_shot_selftest.png"
    CaptureRegion(0, 0, 100, 50, testPath)
    psExe := FindPsExe()
    if FileExist(testPath) {
        size := FileGetSize(testPath)
        FileAppend("OK " testPath " bytes=" size " ps=" psExe, "*")
    } else {
        FileAppend("FAIL " testPath, "*")
    }
    ExitApp
}
