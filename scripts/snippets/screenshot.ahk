#Requires AutoHotkey v2.0
#SingleInstance Force
; ============================================================================
; 截图工具 —— 零依赖方案
; ----------------------------------------------------------------------------
; 不引第三方库，借系统自带 PowerShell + .NET 完成截图。
; 支持：全屏 / 指定区域 / 指定窗口（含浏览器等硬件加速窗口）/ 直接进剪贴板。
;
; 自测：  AutoHotkey.exe screenshot.ahk test        → 截一张全屏并打印路径
;
; 【为什么不自己调 GDI+】
;   纯 AHK 截图要引 Gdip_All.ahk（3000+ 行第三方库）。日常自动化借 PowerShell
;   更省事、更稳、零维护。需要高频截图时再换 GDI+ 方案，见文件末尾。
;
; 【注意】截图是真实副作用，别把 CaptureFullScreen 挂到高频热键上。
; ============================================================================

SHOT_DIR := A_ScriptDir "\screenshots"

; ---- PowerShell 脚本模板（@@占位符@@ 由 AHK 替换后写入临时 .ps1）----
PS_FULL := "
(
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b = New-Object Drawing.Bitmap([Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
$g = [Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen(0, 0, 0, 0, $b.Size)
$g.Dispose()
$b.Save('@@OUT@@', [Drawing.Imaging.ImageFormat]::Png)
$b.Dispose()
)"

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

; PrintWindow 的 flag=2（PW_RENDERFULLCONTENT，微软未公开但被 Chromium/Rust 采用）
; 是截取硬件加速窗口（浏览器、DirectX 程序）的关键，Win8.1+ 有效。
PS_WINDOW := "
(
Add-Type -AssemblyName System.Drawing
Add-Type @'
using System;
using System.Runtime.InteropServices;
public class WinShot {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int L, T, R, B; }
    [DllImport(\"user32.dll\")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
    [DllImport(\"user32.dll\")] public static extern bool PrintWindow(IntPtr h, IntPtr dc, uint flags);
}
'@
$h = [IntPtr]@@HWND@@
$r = New-Object WinShot+RECT
[void][WinShot]::GetWindowRect($h, [ref]$r)
$w = $r.R - $r.L; $ht = $r.B - $r.T
$b = New-Object Drawing.Bitmap($w, $ht)
$g = [Drawing.Graphics]::FromImage($b)
$dc = $g.GetHdc()
[void][WinShot]::PrintWindow($h, $dc, 2)
$g.ReleaseHdc($dc)
$g.Dispose()
$b.Save('@@OUT@@', [Drawing.Imaging.ImageFormat]::Png)
$b.Dispose()
)"

PS_CLIP := "
(
Add-Type -AssemblyName System.Windows.Forms, System.Drawing
$b = New-Object Drawing.Bitmap([Windows.Forms.Screen]::PrimaryScreen.Bounds.Width, [Windows.Forms.Screen]::PrimaryScreen.Bounds.Height)
$g = [Drawing.Graphics]::FromImage($b)
$g.CopyFromScreen(0, 0, 0, 0, $b.Size)
$g.Dispose()
[Windows.Forms.Clipboard]::SetImage($b)
)"

; ---- 命令行自测 ----
if (A_Args.Length && A_Args[1] = "test") {
    FileAppend CaptureFullScreen(), "*"
    ExitApp()
}

; ---- 热键示例（按需保留）----
^!s::TrayTip("已保存", CaptureFullScreen())          ; 全屏
^!a::TrayTip("已保存", CaptureWindow("A"))           ; 活动窗口
^!r::TrayTip("已保存", CaptureRegion(100, 100, 800, 600))  ; 指定区域
^!c::CaptureToClipboard()                            ; 全屏进剪贴板
^!x::ExitApp()

; ---- 对外函数 ----

CaptureFullScreen(outPath := "") {
    outPath := outPath = "" ? MakeShotPath("full") : outPath
    EnsureDir(outPath)
    RunPs StrReplace(PS_FULL, "@@OUT@@", outPath)
    return outPath
}

CaptureRegion(x, y, w, h, outPath := "") {
    outPath := outPath = "" ? MakeShotPath("region") : outPath
    EnsureDir(outPath)
    ps := StrReplace(PS_REGION, "@@X@@", x)
    ps := StrReplace(ps, "@@Y@@", y)
    ps := StrReplace(ps, "@@W@@", w)
    ps := StrReplace(ps, "@@H@@", h)
    RunPs StrReplace(ps, "@@OUT@@", outPath)
    return outPath
}

CaptureWindow(winTitle := "A", outPath := "") {
    hwnd := WinExist(winTitle)
    if !hwnd
        throw TargetError("找不到窗口：" winTitle, -1)   ; v2 里找不到窗口会抛异常
    outPath := outPath = "" ? MakeShotPath("win") : outPath
    EnsureDir(outPath)
    ps := StrReplace(PS_WINDOW, "@@HWND@@", hwnd)
    RunPs StrReplace(ps, "@@OUT@@", outPath)
    return outPath
}

CaptureToClipboard() {
    RunPs PS_CLIP
}

; ---- 内部工具 ----

MakeShotPath(tag) => SHOT_DIR "\" tag "_" FormatTime(A_Now, "yyyyMMdd_HHmmss") ".png"

EnsureDir(path) {
    dir := SubStr(path, 1, InStr(path, "\", , -1) - 1)
    if (dir && !DirExist(dir))
        DirCreate dir
}

RunPs(script) {
    psFile := A_Temp "\ahk_shot_" A_TickCount ".ps1"
    f := FileOpen(psFile, "w", "UTF-8")     ; 带 BOM，PowerShell 才能正确读中文路径
    f.Write(script)
    f.Close()
    try
        RunWait A_ComSpec ' /c powershell -NoProfile -ExecutionPolicy Bypass -File "' psFile '"', , "Hide"
    finally {
        Sleep 300
        try FileDelete psFile
    }
}

; ============================================================================
; 需要更高性能 / 更专业能力时
; ----------------------------------------------------------------------------
; 推荐 Buzzerb/AHKv2-Screenshot-Tools（纯 AHK v2，基于 GDI+）：
;   https://github.com/Buzzerb/AHKv2-Screenshot-Tools
;
; 优势：截图在本进程内完成（无 PowerShell 启动开销）；
;       支持「窗口客户区」截图、多种渲染模式；同样支持硬件加速窗口。
;
; 用法：把库放进脚本同目录的 lib\ 下，然后
;   #Include "%A_ScriptDir%\lib\AHKv2_Screenshot_Tools.ahk"
;   具体调用参考仓库里的 AHKv2_Screenshotter_Quickstart.ahk
;
; 取舍：库约 4000 行（含 Gdip_All.ahk）。只在确实需要高频截图或专业窗口截图时引入。
; ============================================================================
