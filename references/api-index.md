# AutoHotkey v2.0.26 内建函数索引（权威 · 已实测核验）

> **数据来源**：`AutoHotkey v2.0.26` 官方源码的两张互补表 —— `source/script.cpp` 的 `g_BIF[]`（运行时函数注册表，含参数个数）与 `source/lib/functions.h`（参数名与类型）。两者互不重叠，并集共 **342 个内建函数**。

> **已核验**：342 个名字全部用本机解释器逐个跑过存在性探针，**零虚构、零遗漏**。另附 **131 个内建变量**与 **36 个内建类**。

> **怎么用**：脚本写完后，把用到的每个函数名在本文件里 Grep 一遍。**查不到就是写错了** —— 这是本 skill 拦截 V1 旧名与编造函数名的主要手段（官方校验器只报警告、不报错，会放你过去）。

> **记法**：`?` = 可选参数；`&Name` = 输出参数（须传变量）；`→ R` = 有返回值；`...` = 可变参数；`n~m 个参数` = 源码只给了个数，参数名未在类型表中声明。

> **不在此表 ≠ 不存在**：本表只含**全局函数**。对象方法（`arr.Push()`、`map.Set()`、`obj.HasProp()`、`m.HasKey()`、正则匹配对象、`File` 对象等）属于对象协议，不走 BIF 注册表。


---


## A

```
Abs(1~1 个参数)
ACos(1~1 个参数)
ASin(1~1 个参数)
ATan(1~1 个参数)
```

## B

```
BlockInput(Mode)
```

## C

```
CallbackCreate(Function, Options?, ParamCount?) → R
CallbackFree(Callback)
CaretGetPos(0~2 个参数)
Ceil(1~1 个参数)
Chr(1~1 个参数)
Click(0~6 个参数)
ClipWait(Timeout?, AnyType?) → R
ComCall(2 个以上参数)
ComObjActive(1~1 个参数)
ComObjConnect(1~2 个参数)
ComObjFlags(1~3 个参数)
ComObjFromPtr(1~1 个参数)
ComObjGet(1~1 个参数)
ComObjQuery(2~3 个参数)
ComObjType(1~2 个参数)
ComObjValue(1~1 个参数)
ControlAddItem(Value, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlChooseIndex(Index, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlChooseString(Value, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlClick(Control?, WinTitle?, WinText?, Button?, Count?, Options?, ExcludeTitle?, ExcludeText?)
ControlDeleteItem(Index, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlFindItem(Item, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlFocus(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlGetChecked(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetChoice(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetClassNN(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetEnabled(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetExStyle(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetFocus(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetHwnd(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetIndex(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetItems(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetPos(&X?, &Y?, &Width?, &Height?, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlGetStyle(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetText(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlGetVisible(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
ControlHide(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlHideDropDown(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlMove(X?, Y?, Width?, Height?, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlSend(Keys, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlSendText(Keys, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlSetChecked(Value, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlSetEnabled(Value, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlSetExStyle(Value, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlSetStyle(Value, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlSetText(NewText, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlShow(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ControlShowDropDown(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
CoordMode(TargetType, RelativeTo?) → R
Cos(1~1 个参数)
Critical(OnOffNumber?...) → R
```

## D

```
DateAdd(DateTime, Time, TimeUnits) → R
DateDiff(DateTime1, DateTime2, TimeUnits) → R
DetectHiddenText(Mode...) → R
DetectHiddenWindows(Mode...) → R
DirCopy(Source, Dest, Overwrite?)
DirCreate(Path)
DirDelete(Path, Recurse?)
DirExist(Pattern...) → R
DirMove(Source, Dest, Flag?)
DirSelect(StartingFolder?, Options?, Prompt?) → R
DllCall(1 个以上参数)
Download(URL, Path)
DriveEject(Drive?)
DriveGetCapacity(Path) → R
DriveGetFilesystem(Drive) → R
DriveGetLabel(Drive) → R
DriveGetList(Type?) → R
DriveGetSerial(Drive) → R
DriveGetSpaceFree(Path) → R
DriveGetStatus(Path) → R
DriveGetStatusCD(Drive?) → R
DriveGetType(Path) → R
DriveLock(Drive)
DriveRetract(Drive?)
DriveSetLabel(Drive, Label?)
DriveUnlock(Drive)
```

## E

```
Edit(...)
EditGetCurrentCol(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
EditGetCurrentLine(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
EditGetLine(Index, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
EditGetLineCount(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
EditGetSelectedText(Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
EditPaste(Value, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
EnvGet(VarName) → R
EnvSet(VarName, Value?)
Exit(ExitCode?)
ExitApp(ExitCode?)
Exp(1~1 个参数)
```

## F

```
FileAppend(Value, Path?, Options?)
FileCopy(Source, Dest, Overwrite?)
FileCreateShortcut(Target, LinkFile)
FileDelete(Pattern)
FileEncoding(Encoding) → R
FileExist(Pattern...) → R
FileGetAttrib(Path?) → R
FileGetShortcut(LinkFile, &Target?)
FileGetSize(Path?, Units?) → R
FileGetTime(Path?, WhichTime?) → R
FileGetVersion(Path?) → R
FileInstall(Source, Dest, Overwrite?)
FileMove(Source, Dest, Overwrite?)
FileOpen(2~3 个参数)
FileRead(Path, Options?) → R
FileRecycle(Pattern)
FileRecycleEmpty(Drive?)
FileSelect(Options?, RootDirFileName?, Title?, Filter?) → R
FileSetAttrib(Attributes, Pattern?, Mode?)
FileSetTime(YYYYMMDD?, Pattern?, WhichTime?, Mode?)
Floor(1~1 个参数)
Format(1 个以上参数)
FormatTime(0~2 个参数)
```

## G

```
GetKeyName(KeyName...) → R
GetKeySC(KeyName)
GetKeyState(KeyName, Mode?) → R
GetKeyVK(KeyName)
GetMethod(1~3 个参数)
GroupActivate(GroupName, Mode?) → R
GroupAdd(GroupName, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
GroupClose(GroupName, Mode?)
GroupDeactivate(GroupName, Mode?)
GuiCtrlFromHwnd(Hwnd...) → R
GuiFromHwnd(Hwnd, Recurse?...) → R
```

## H

```
HasBase(2~2 个参数)
HasMethod(1~3 个参数)
HasProp(2~2 个参数)
HotIf(Criterion?)
HotIfWinActive(WinTitle?, WinText?)
HotIfWinExist(WinTitle?, WinText?)
HotIfWinNotActive(WinTitle?, WinText?)
HotIfWinNotExist(WinTitle?, WinText?)
Hotkey(KeyName, Action?, Options?)
Hotstring(String, Replacement?, OnOffToggle?) → R
```

## I

```
IL_Add(ImageList, Filename, IconNumber?, ResizeNonIcon?) → R
IL_Create(InitialCount?, GrowCount?, LargeIcons?)
IL_Destroy(ImageList)
ImageSearch(X1, Y1, X2, Y2, Image) → R
IniDelete(Path, Section, Key?)
IniRead(Path, Section?, Key?, Default?) → R
IniWrite(Value, Path, Section, Key?)
InputBox(Prompt?, Title?, Options?, Default?) → R
InstallKeybdHook(Install?, Force?...)
InstallMouseHook(Install?, Force?...)
InStr(2~5 个参数)
IsAlnum(1~2 个参数)
IsAlpha(1~2 个参数)
IsDigit(1~1 个参数)
IsFloat(1~1 个参数)
IsInteger(1~1 个参数)
IsLabel(Name)
IsLower(1~2 个参数)
IsNumber(1~1 个参数)
IsObject(1~1 个参数)
IsSetRef(1~1 个参数)
IsSpace(1~1 个参数)
IsTime(1~1 个参数)
IsUpper(1~2 个参数)
IsXDigit(1~1 个参数)
```

## K

```
KeyHistory(MaxEvents?)
KeyWait(KeyName, Options?) → R
```

## L

```
ListHotkeys(...)
ListLines(Mode?...) → R
ListVars(...)
ListViewGetContent(Options?, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
Ln(1~1 个参数)
LoadPicture(Filename, Options?, &ImageType?) → R
Log(1~1 个参数)
LTrim(1~2 个参数)
```

## M

```
Max(1 个以上参数)
MenuFromHandle(Handle...) → R
MenuSelect(WinTitle?, WinText?)
Min(1 个以上参数)
Mod(2~2 个参数)
MonitorGet(N?, &Left?, &Top?, &Right?, &Bottom?) → R
MonitorGetCount()
MonitorGetName(N?) → R
MonitorGetPrimary()
MonitorGetWorkArea(N?, &Left?, &Top?, &Right?, &Bottom?) → R
MouseGetPos(&X?, &Y?, &Win?, &Control?, Flag?)
MsgBox(Text?, Title?, Options?) → R
```

## N

```
NumGet(2~3 个参数)
NumPut(3 个以上参数)
```

## O

```
ObjAddRef(1~1 个参数)
ObjBindMethod(1 个以上参数)
ObjFromPtr(1~1 个参数)
ObjFromPtrAddRef(1~1 个参数)
ObjGetBase(1~1 个参数)
ObjGetCapacity(1~1 个参数)
ObjHasOwnProp(2~2 个参数)
ObjOwnPropCount(1~1 个参数)
ObjOwnProps(1~1 个参数)
ObjPtr(1~1 个参数)
ObjPtrAddRef(1~1 个参数)
ObjRelease(1~1 个参数)
ObjSetBase(2~2 个参数)
ObjSetCapacity(2~2 个参数)
OnClipboardChange(Function, AddRemove?)
OnError(Function, AddRemove?)
OnExit(Function, AddRemove?)
OnMessage(Number, Function, MaxThreads?)
Ord(1~1 个参数)
OutputDebug(Text...)
```

## P

```
Pause(NewState?)
Persistent(NewValue?...) → R
PixelGetColor(X, Y, Mode?) → R
PixelSearch(X1, Y1, X2, Y2, Color, Variation?) → R
PostMessage(Msg, wParam?, lParam?, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
ProcessClose(Process) → R
ProcessExist(Process?)
ProcessGetName(Process?) → R
ProcessGetParent(Process?)
ProcessGetPath(Process?) → R
ProcessSetPriority(Priority, Process?) → R
ProcessWait(Process, Timeout?) → R
ProcessWaitClose(Process, Timeout?) → R
```

## R

```
Random(0~2 个参数)
RegCreateKey(0~1 个参数)
RegDelete(0~2 个参数)
RegDeleteKey(0~1 个参数)
RegExMatch(2~4 个参数)
RegExReplace(2~6 个参数)
RegRead(0~3 个参数)
RegWrite(1~4 个参数)
Reload()
Round(1~2 个参数)
RTrim(1~2 个参数)
Run(Target, WorkingDir?, Options?, &PID?)
RunAs(User?, Password?, Domain?...)
RunWait(1~4 个参数)
```

## S

```
Send(Keys...)
SendEvent(Keys...)
SendInput(Keys...)
SendLevel(Level) → R
SendMessage(Msg, wParam?, lParam?, Control, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?, Timeout?) → R
SendMode(Mode) → R
SendPlay(Keys...)
SendText(Text...)
SetCapsLockState(State?)
SetControlDelay(Delay) → R
SetDefaultMouseSpeed(Speed) → R
SetKeyDelay(Delay?, Duration?, Mode?)
SetMouseDelay(Delay, Mode?) → R
SetNumLockState(State?)
SetRegView(RegView) → R
SetScrollLockState(State?)
SetStoreCapsLockMode(Mode...) → R
SetTimer(Function?, Period?, Priority?)
SetTitleMatchMode(Mode) → R
SetWinDelay(Delay) → R
SetWorkingDir(Path)
Shutdown(Flags)
Sin(1~1 个参数)
Sleep(Delay)
Sort(1~3 个参数)
SoundBeep(Duration?, Frequency?...)
SoundGetInterface(1~3 个参数)
SoundGetMute(0~2 个参数)
SoundGetName(0~2 个参数)
SoundGetVolume(0~2 个参数)
SoundPlay(Path, Wait?)
SoundSetMute(1~3 个参数)
SoundSetVolume(1~3 个参数)
SplitPath(1~6 个参数)
Sqrt(1~1 个参数)
StatusBarGetText(Part?, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
StatusBarWait(Text?, Timeout?, Part?, WinTitle?, WinText?, Interval?, ExcludeTitle?, ExcludeText?) → R
StrCompare(2~3 个参数)
StrGet(1~3 个参数)
StrLen(1~1 个参数)
StrLower(1~1 个参数)
StrPtr(1~1 个参数)
StrPut(1~4 个参数)
StrReplace(2~6 个参数)
StrSplit(String, Delimiters?, OmitChars?, MaxParts?) → R
StrTitle(1~1 个参数)
StrUpper(1~1 个参数)
SubStr(2~3 个参数)
Suspend(Mode?)
SysGet(Index)
SysGetIPAddresses() → R
```

## T

```
Tan(1~1 个参数)
Thread(Command, Value1?, Value2?)
ToolTip(Text?, X?, Y?, Index?) → R
TraySetIcon(File?, Number?, Freeze?)
TrayTip(Text?, Title?, Options?)
Trim(1~2 个参数)
Type(1~1 个参数)
```

## V

```
VarSetStrCapacity(1~2 个参数)
VerCompare(2~2 个参数)
```

## W

```
WinActivate(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinActivateBottom(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinActive(0~4 个参数)
WinClose(WinTitle?, WinText?, WaitTime?, ExcludeTitle?, ExcludeText?)
WinExist(0~4 个参数)
WinGetClass(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetClientPos(&X?, &Y?, &Width?, &Height?, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinGetControls(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetControlsHwnd(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetCount(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetExStyle(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetID(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetIDLast(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetList(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetMinMax(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetPID(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetPos(&X?, &Y?, &Width?, &Height?, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinGetProcessName(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetProcessPath(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetStyle(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetText(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetTitle(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetTransColor(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinGetTransparent(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?) → R
WinHide(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinKill(WinTitle?, WinText?, WaitTime?, ExcludeTitle?, ExcludeText?)
WinMaximize(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinMinimize(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinMinimizeAll(...)
WinMinimizeAllUndo(...)
WinMove(X?, Y?, Width?, Height?, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinMoveBottom(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinMoveTop(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinRedraw(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinRestore(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinSetAlwaysOnTop(Value?, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinSetEnabled(Value, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinSetExStyle(Style, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinSetRegion(Options?, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinSetStyle(Style, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinSetTitle(NewTitle, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinSetTransColor(Value, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinSetTransparent(Value, WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinShow(WinTitle?, WinText?, ExcludeTitle?, ExcludeText?)
WinWait(WinTitle?, WinText?, Timeout?, ExcludeTitle?, ExcludeText?) → R
WinWaitActive(WinTitle?, WinText?, Timeout?, ExcludeTitle?, ExcludeText?) → R
WinWaitClose(WinTitle?, WinText?, Timeout?, ExcludeTitle?, ExcludeText?) → R
WinWaitNotActive(WinTitle?, WinText?, Timeout?, ExcludeTitle?, ExcludeText?) → R
```

---


## 内建变量 `A_*`（131 个 · 可写 37 个）

> 数据源：源码 `source/script.cpp` 的 `g_BIV_A[]` 注册表（编译期二分查找表，即解释器真正认的名字）。
> 131 个名字全部逐个跑过解释器存在性探针，另有 11 个近似假名作为反例被正确拒绝。

```
A_AhkPath                 A_Index                   A_LoopRegKey              A_Sec
A_AhkVersion              A_InitialWorkingDir       A_LoopRegName             A_SendLevel
A_AllowMainWindow         A_Is64bitOS               A_LoopRegTimeModified     A_SendMode
A_AppData                 A_IsAdmin                 A_LoopRegType             A_Space
A_AppDataCommon           A_IsCompiled              A_MaxHotkeysPerInterval   A_StartMenu
A_Clipboard               A_IsCritical              A_MDay                    A_StartMenuCommon
A_ComputerName            A_IsPaused                A_MenuMaskKey             A_Startup
A_ComSpec                 A_IsSuspended             A_Min                     A_StartupCommon
A_ControlDelay            A_KeyDelay                A_MM                      A_StoreCapsLockMode
A_CoordModeCaret          A_KeyDelayPlay            A_MMM                     A_Tab
A_CoordModeMenu           A_KeyDuration             A_MMMM                    A_Temp
A_CoordModeMouse          A_KeyDurationPlay         A_Mon                     A_ThisFunc
A_CoordModePixel          A_Language                A_MouseDelay              A_ThisHotkey
A_CoordModeToolTip        A_LastError               A_MouseDelayPlay          A_TickCount
A_Cursor                  A_LineFile                A_MSec                    A_TimeIdle
A_DD                      A_LineNumber              A_MyDocuments             A_TimeIdleKeyboard
A_DDD                     A_ListLines               A_Now                     A_TimeIdleMouse
A_DDDD                    A_LoopField               A_NowUTC                  A_TimeIdlePhysical
A_DefaultMouseSpeed       A_LoopFileAttrib          A_OSVersion               A_TimeSincePriorHotkey
A_Desktop                 A_LoopFileDir             A_PriorHotkey             A_TimeSinceThisHotkey
A_DesktopCommon           A_LoopFileExt             A_PriorKey                A_TitleMatchMode
A_DetectHiddenText        A_LoopFileFullPath        A_ProgramFiles            A_TitleMatchModeSpeed
A_DetectHiddenWindows     A_LoopFileName            A_Programs                A_TrayMenu
A_EndChar                 A_LoopFilePath            A_ProgramsCommon          A_UserName
A_EventInfo               A_LoopFileShortName       A_PtrSize                 A_WDay
A_FileEncoding            A_LoopFileShortPath       A_RegView                 A_WinDelay
A_HotkeyInterval          A_LoopFileSize            A_ScreenDPI               A_WinDir
A_HotkeyModifierTimeout   A_LoopFileSizeKB          A_ScreenHeight            A_WorkingDir
A_Hour                    A_LoopFileSizeMB          A_ScreenWidth             A_YDay
A_IconFile                A_LoopFileTimeAccessed    A_ScriptDir               A_Year
A_IconHidden              A_LoopFileTimeCreated     A_ScriptFullPath          A_YWeek
A_IconNumber              A_LoopFileTimeModified    A_ScriptHwnd              A_YYYY
A_IconTip                 A_LoopReadLine            A_ScriptName
```

### 常用变量族速查

| 族 | 变量 | 说明 |
|---|---|---|
| 日期时间 | `A_YYYY` `A_MM` `A_MDay` `A_Hour` `A_Min` `A_Sec` `A_MSec` | 当前时间各段（可单独取用） |
| 日期时间 | `A_YYYY` `A_Mon` `A_WDay` `A_YDay` `A_YWeek` `A_MMM` `A_MMMM` `A_DDD` `A_DDDD` | 月/日/周的中英文名 |
| 日期时间 | `A_Now` `A_NowUTC` `A_TickCount` | 时间戳；`A_TickCount` 是开机以来的毫秒数，适合算耗时 |
| 路径 | `A_ScriptDir` `A_ScriptFullPath` `A_ScriptName` `A_WorkingDir` `A_InitialWorkingDir` | 脚本自身位置 |
| 路径 | `A_Temp` `A_MyDocuments` `A_WinDir` `A_ComSpec` `A_AhkPath` | 常用系统路径 |
| 特殊文件夹 | `A_Desktop` `A_DesktopCommon` `A_AppData` `A_AppDataCommon` `A_ProgramFiles` `A_Programs` `A_ProgramsCommon` `A_StartMenu` `A_StartMenuCommon` `A_Startup` `A_StartupCommon` | 取代 v1 的 `%A_Desktop%` 等展开写法，**直接当路径用** |
| 屏幕 | `A_ScreenWidth` `A_ScreenHeight` `A_ScreenDPI` | 也是 `PixelSearch` / `ImageSearch` 的常用边界 |
| 循环期 | `A_Index` `A_LoopField` `A_LoopReadLine` | 只在对应循环内有效 |
| 遍历文件 | `A_LoopFileName` `A_LoopFileFullPath` `A_LoopFilePath` `A_LoopFileDir` `A_LoopFileExt` `A_LoopFileShortName` `A_LoopFileAttrib` `A_LoopFileSize` `A_LoopFileSizeKB` `A_LoopFileSizeMB` `A_LoopFileTimeCreated` `A_LoopFileTimeModified` `A_LoopFileTimeAccessed` | `Loop Files` 内有效 |
| 遍历注册表 | `A_LoopRegKey` `A_LoopRegName` `A_LoopRegType` `A_LoopRegTimeModified` | `Loop Reg` 内有效 |
| 系统信息 | `A_ComputerName` `A_UserName` `A_OSVersion` `A_Language` `A_Is64bitOS` `A_IsAdmin` `A_PtrSize` | 判断运行环境 |
| 热键上下文 | `A_ThisHotkey` `A_PriorHotkey` `A_ThisFunc` `A_TimeSinceThisHotkey` `A_TimeSincePriorHotkey` `A_TimeIdle` `A_TimeIdleKeyboard` `A_TimeIdleMouse` `A_TimeIdlePhysical` | 热键行为微调、空闲检测 |
| 每输入字符 | `A_EndChar` | 热字串触发时按下的结束符 |
| 托盘 | `A_TrayMenu` `A_IconFile` `A_IconNumber` | 托盘菜单与图标 |
| 定位 | `A_LineFile` `A_LineNumber` | 调试打日志用 |

### 可写变量（v1 靠指令配置，v2 改成给这些变量赋值）

```
A_AllowMainWindow            A_DetectHiddenWindows        A_KeyDuration                A_SendLevel
A_Clipboard                  A_EventInfo                  A_KeyDurationPlay            A_SendMode
A_ControlDelay               A_FileEncoding               A_LastError                  A_StoreCapsLockMode
A_CoordModeCaret             A_HotkeyInterval             A_ListLines                  A_TitleMatchMode
A_CoordModeMenu              A_HotkeyModifierTimeout      A_MaxHotkeysPerInterval      A_TitleMatchModeSpeed
A_CoordModeMouse             A_IconHidden                 A_MenuMaskKey                A_WinDelay
A_CoordModePixel             A_IconTip                    A_MouseDelay                 A_WorkingDir
A_CoordModeToolTip           A_Index                      A_MouseDelayPlay
A_DefaultMouseSpeed          A_KeyDelay                   A_RegView
A_DetectHiddenText           A_KeyDelayPlay               A_ScriptName
```

> 其余 `A_*` 一律**只读**，写了会报 `This variable is read-only`。
>
> 例：v1 `SetTitleMatchMode, 2` → v2 `A_TitleMatchMode := 2`；
> v1 `#KeyHistory 0` → v2 `KeyHistory(0)`（**没有** `A_KeyHistory` 变量）；
> v1 `CoordMode, Mouse, Screen` → v2 可写 `A_CoordModeMouse := "Screen"`（或用函数 `CoordMode("Mouse", "Screen")`）。
>
> **注意**：源码里的内部名 `BIV_xDelay` / `BIV_SpecialFolderPath` / `BIV_ScreenWidth_Height` 等
> **不是**可用的变量名，只是共享同一读取函数的实现细节。可用名就是上面那张表里的 `A_xxx`。


---


## 内建类与类型转换（非 BIF，但同样已核验存在）


以下名字可以直接 `Name(...)` 调用。它们不是普通函数，而是**内建类构造器**或**类型转换**，
所以不在上面的函数表里，但完全合法：


```
Array(...)
BoundFunc(...)
Buffer(...)
ClipboardAll(...)
Closure(...)
ComObjArray(...)
ComObject(...)
ComValue(...)
Enumerator(...)
Error(...)
File(...)
Float(...)
Func(...)
Gui(...)
IndexError(...)
Integer(...)
IsSet(...)
Map(...)
MemberError(...)
MemoryError(...)
Menu(...)
MenuBar(...)
MethodError(...)
Number(...)
OSError(...)
Object(...)
Primitive(...)
PropertyError(...)
RegExMatch(...)
String(...)
TargetError(...)
TypeError(...)
UnsetError(...)
ValueError(...)
VarRef(...)
ZeroDivisionError(...)
```

> 常见用法：`M := Map()`、`Arr := Array()`、`Buf := Buffer(64)`、`E := Error("msg")`、
> `throw ValueError("参数不能为空", -1)`、`C := ComObject("WScript.Shell")`。
> **注意**：`Gui(...)` / `MenuBar(...)` 属界面相关，本 skill 不使用。
