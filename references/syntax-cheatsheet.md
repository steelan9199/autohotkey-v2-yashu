# AutoHotkey v2.0 语法速查

> 全部示例已用本机 `AutoHotkey v2.0.26` 逐块校验通过。
> 函数名与参数以 `api-index.md`（342 个内建函数全集）为准。

## 1. 脚本结构

```ahk
#Requires AutoHotkey v2.0        ; 版本要求，必须放最前
#SingleInstance Force            ; 重复运行时的处理：Force/Ignore/Prompt/Off

; 自动执行段（脚本启动时自上而下执行一次）
SetWorkingDir A_ScriptDir
A_IconTip := "我的自动化脚本"

; 热键定义（脚本加载时注册，之后等待触发）
^!s:: {
    SendText "被按下`n"
}

; 函数定义
DoWork(path, mode := "r") {
    return FileRead(path, mode)
}

; 类定义
class Config {
    static Dir := "D:\data"
}
```
执行顺序：**自动执行段 → 停下等待热键/定时器**（什么都没注册时脚本直接退出）。

## 2. 变量与作用域

```ahk
x := 1                       ; 全局变量（在函数外定义）
s := "text"
flag := true                 ; 布尔：true / false
n := unset                   ; 「未赋值」状态，用 IsSet(x) 判断

global gCount := 0           ; 显式声明为全局（也可在脚本顶层直接赋值）

ReadOnly() {
    ; ✅ 读取全局变量**不需要** global 声明，直接读就行（实测）
    return gCount
}

Counter() {
    global gCount            ; ⚠️ 赋值给全局变量**必须**先声明 global
    gCount += 1
    local temp := gCount     ; 局部变量
    static calls := 0        ; 静态变量：函数多次调用间保持
    calls += 1
    return temp "|" calls
}

IsSet(undefinedVar)          ; → 0（false），安全地检测变量是否已赋值
```

**变量作用域规则（实测结论，这条最容易记反）**：

| 在函数里…… | 要不要写 `global` | 不写会怎样 |
|---|---|---|
| **读**一个全局变量 | **不用** | 正常读到全局值（实测 `A=顶层值`） |
| **写**一个全局变量 | **必须写** | 会创建**同名局部变量**，全局值不变，并报 `This local variable has the same name as a global variable` |

```ahk
x := "顶层值"

ReadIt() {
    return x                  ; ✅ 读到 "顶层值"
}

WriteIt() {
    x := "局部"                ; ⚠️ 只改了局部！全局 x 仍是 "顶层值"，而且报警告
    return x
}

WriteGlobal() {
    global x                  ; ✅ 声明后才能改到全局
    x := "改了全局"
    return x
}
```

> `static` 是另一条路：函数内 `static count := 0` 让变量在多次调用间保持，不需要全局变量。
> 需要「多个函数共享一份配置」时才用真正的全局变量。
>
> 📌 上面这块里的 `WriteIt()` **故意**会触发 `local variable has the same name as a global variable`
> 警告 —— 那就是"写全局忘了声明"的真实后果，不是笔误。

- 变量名**大小写不敏感**（`myVar` 与 `MyVar` 是同一个）。
- 字符串与数字可互换，比较时按需自动转换：`"5" + 1` → `6`。

## 3. 运算符

```ahk
; 算术
a := 7 + 3 * 2        ; 13
b := 7 // 2           ; 3   整除
c := Mod(7, 2)        ; 1   取余 ← 必须用 Mod()，见下方警告
d := 2 ** 10          ; 1024
e := -5
f := Abs(-3)          ; 3

; 赋值
x := 1
x += 1                ; 累加，还有 -= *= /= //= |= &= ^= >>= <<=
x++                   ; 自增（先取值），还有 -- 与 ++x

; 比较（比较本身是表达式，要放进 if 或赋值里，不能单独成行）
same := (x = 1)       ; 相等（不区分大小写）
same2 := (x == 1)     ; 相等（区分大小写）
diff := (x != 1)      ; 不等
bigger := (x > 1)

; 逻辑
p := true && false    ; 与（短路）
q := true || false    ; 或（短路）
r := !true            ; 非

; 三元
label := (x > 0) ? "正数" : "非正数"

; 字符串拼接（唯一正确写法）：空格隐式连接
greet := "Hello" " " "World"        ; → "Hello World"

; 引用（把变量本身传出去）
Swap(&a, &b) {
    t := a, a := b, b := t
}
Swap(&left, &right)
```

> ⚠️ **`%` 不能当取余运算符用**（实测 `c := 7 % 2` 直接报 `Missing ending "%"`，
> 加不加括号都一样）。v2 里 `%` 被保留给了遗留的变量解引用语法。
> 取余一律写 **`Mod(7, 2)`**。
>
> ⚠️ 不要用 v1 的点号拼接 `"a" . "b"` —— 实测 v2.0 能跑（输出 `ab`，校验 0 错误 0 警告），
> 但它和 v2.1 移除的是同一套语法，留着等于埋雷。**一律用空格隐式拼接 `"a" "b"`**。
>
> 实测补充：`.=`（追加赋值）在 v2.0 可用（`x := "a"` 然后 `x .= "b"` → `ab`），
> 但它和点号拼接是配套的，同样不建议用。要追加就写 `x := x "b"`。

**换行续行规则（实测）**：一行语句太长想折行，**行尾必须是运算符或逗号**，
单纯以字符串结尾不算续行：

```ahk
; ✅ 行尾是逗号 → 续行
FileAppend "内容",
    "log.txt", "UTF-8"

; ✅ 也行：下一行以逗号开头
FileAppend "内容"
    , "log.txt", "UTF-8"

; ✅ 行尾是运算符 → 续行
n := 1 +
    2

; ❌ 行尾是字符串 → 不算续行。下面两行会被当成两条独立语句，
;    第二行报 `This line does not contain a recognized action.`
; x := "a"
;   "b"
```

## 4. 字符串

```ahk
s := "Hello World"

StrLen(s)                        ; 长度
SubStr(s, 1, 5)                  ; "Hello"
InStr(s, "World")                ; 7（找不到返回 0）
StrReplace(s, "World", "AHK")
StrSplit("a,b,c", ",")           ; 数组 ["a","b","c"]
StrUpper(s), StrLower(s), StrTitle("hi there")
Trim(s), LTrim(s), RTrim(s)
Format("{1} 有 {2:.2f} 元", "苹果", 3.14159)   ; 格式化，比手拼好看
StrCompare("a", "b", "CaseSense")               ; 大小写敏感比较

; 多行字符串
long := "
(
第一行
第二行
)"

; 转义与特殊字符（反引号是唯一的转义符）
esc := "制表符`t换行`n引号`"反引号``"
code := Chr(65)                  ; "A"
num := Ord("A")                  ; 65
```

**正则**：

```ahk
if RegExMatch(text, "(\d{4})-(\d{2})", &m)
    year := m[1], month := m[2]

out := RegExReplace(text, "\s+", " ")          ; 空白折叠
; StrReplace / RegExReplace 最适合用来清洗剪贴板文本
```

## 5. 数组、Map 与对象

```ahk
; 数组（下标从 1 开始！）
arr := [10, 20, 30]
arr.Push(40)              ; 追加
last := arr.Pop()         ; 弹出末尾
first := arr[1]
arr.Length                ; 元素个数
arr.RemoveAt(1)           ; 删除第 1 个
arr.InsertAt(1, 5)        ; 插入到第 1 位
for index, value in arr
    OutputDebug index ": " value

; Map（键值对，键可以是任意值）
m := Map("name", "Musk", "age", 30)
m["city"] := "深圳"
if m.Has("name")
    OutputDebug m["name"]
m.Delete("age")
for k, v in m
    OutputDebug k "=" v

; 普通对象（属性访问）
o := { name: "Musk", age: 30 }
o.city := "深圳"
o.HasProp("name")         ; true
ObjOwnProps(o)            ; 属性名数组
o.GetOwnPropDesc("age")
```

## 6. 流程控制

```ahk
if (x > 10) {
    ; ...
} else if (x > 5) {
    ; ...
} else {
    ; ...
}

; v2 必须用表达式判断，不能写 if x = 10
if WinExist("ahk_class Notepad") && ProcessExist("notepad.exe")
    WinActivate()

; 循环
Loop 5 {
    OutputDebug A_Index          ; 1..5
}

Loop {
    if (++i > 100)
        break
    if (Mod(i, 2) = 0)
        continue
}

while (i < 10) {
    i += 1
}

for i, v in ["a", "b"]
    OutputDebug i ":" v

; 遍历字符串行
Loop Parse "a`nb`nc", "`n"
    OutputDebug A_LoopField

; switch
switch key {
    case "a", "A": OutputDebug "字母 A"
    case "1":      OutputDebug "数字 1"
    default:       OutputDebug "其它"
}
```

## 7. 函数

```ahk
; 普通定义
Add(a, b) {
    return a + b
}

; 默认参数 + 可选参数
Greet(name, greeting := "你好", punct := "！") {
    return greeting name punct
}

; 可变参数
Sum(nums*) {
    total := 0
    for n in nums
        total += n
    return total
}
Sum(1, 2, 3)                 ; 6

; 输出参数（通过引用返回多个值）
GetSize(&w, &h) {
    w := 1920, h := 1080
}
GetSize(&width, &height)

; 箭头函数（适合短小的回调）
double := (x) => x * 2                  ; ⚠️ 变量名大小写不敏感，别和上面的 Add 撞名
plus := (a, b) => a + b
; 多语句箭头函数需要花括号
logIt := (msg) => (FileAppend(msg "`n", "log.txt"))

; 函数是对象，可传递
Apply(fn, v) => fn(v)
Apply(double, 5)             ; 10

; 绑定方法
cb := ObjBindMethod(Animal, "Reset")
cb()
```

> **注意**：v2 里函数内**读**全局变量是允许的（直接读即可），只有**赋值给**全局变量才必须
> 先写 `global`。写错了不会报错，只会静默地创建一个局部变量 —— 所以务必跑校验，
> `--strict` 会把这种"局部变量与全局同名"的警告拦下来。

## 8. 类

```ahk
class Animal {
    static Count := 0                    ; 静态属性

    __New(name) {                        ; 构造函数
        this.Name := name
        Animal.Count += 1
    }

    Speak() {                            ; 方法
        return this.Name " 叫了一声"
    }

    static Reset() {
        Animal.Count := 0
    }
}

class Dog extends Animal {
    Speak() {                            ; 覆盖
        return super.Speak() "（汪）"
    }
}

d := Dog("旺财")
d.Name                                   ; "旺财"
d.Speak()
Animal.Count
```

## 9. 错误处理

```ahk
try {
    risky()
} catch as e {
    ; e 是错误对象：e.Message / e.What / e.File / e.Line / e.Extra / e.Stack
    OutputDebug e.Message " @ " e.File ":" e.Line
} finally {
    Cleanup()
}

; 只捕获特定类型
try {
    FileRead("不存在的文件.txt")
} catch OSError as e {
    OutputDebug "文件操作失败：" e.Message
}

; 没有异常时也要判断返回值
result := FileExist("a.txt")
if !result
    OutputDebug "文件不存在"

; 主动抛错
Validate(x) {
    if (x = "")
        throw ValueError("参数不能为空", -1)
}
```

> **AHK 的运行期错误默认弹模态框**，会把自动化脚本卡死。
> 凡是可能失败的调用（文件、剪贴板、窗口、网络）都放进 `try/catch`。
> `scripts/ahk_run.py` 就是用这个原理把错误关进笼子的。

## 10. 热键与热字串

```ahk
; 基本热键
^!s:: {                       ; Ctrl+Alt+S
    SendText "hello"
}

; 键名速查：^=Ctrl  !=Alt  +=Shift  #=Win
; 字母/数字直接写；功能键 F1-F24；其他键名见下
#n::Run "notepad.exe"          ; Win+N

; 单行热键可以省略花括号（只有一个语句时）
^!q::ExitApp()

; 热键块里多语句必须用花括号
^!d:: {
    A_Clipboard := ""
    Send "^c"
    if ClipWait(1)
        SendText StrUpper(A_Clipboard)
}

; 上下文相关热键（只在特定窗口生效）
#HotIf WinActive("ahk_exe notepad.exe")
^!s::SendText "只在记事本里生效"
#HotIf                          ; 结束条件段（必须写，否则影响后面的热键）

; 热字串：输入触发的文本替换
::btw::by the way
::sig::
(
此致
敬礼
)

; 立即触发的热字串
:*:@@::musk@example.com

#Hotstring EndChars -()[]{}:;'"/\,.?!`n`t                ; 自定义触发字符

; 动态注册/注销热键
Hotkey "^!j", (*) => SendText "dynamic"
Hotkey "^!j", "Off"
```

**常用键名**：`` ` ``(转义)、`Enter`、`Esc`、`Tab`、`Space`、`Backspace`、`Delete`、`Insert`、
`Home`、`End`、`PgUp`、`PgDn`、`Up/Down/Left/Right`、`WheelUp`、`WheelDown`、`MButton`、
`XButton1`、`CapsLock`、`在 vk 码写法` → `vkFF`。

## 11. 等待、定时与线程

```ahk
Sleep 500                                 ; 毫秒
SetKeyDelay 10, 50                        ; 按键间隔、按住时长
SetMouseDelay 10
SetWinDelay 100
SetControlDelay 20
SetTitleMatchMode 2                       ; 1=开头匹配 2=包含 3=精确
DetectHiddenWindows true
CoordMode "Mouse", "Screen"               ; 鼠标坐标用屏幕绝对坐标
CoordMode "Pixel", "Screen"               ; 找图找色同理

; 定时器（脚本常驻的关键手段）
SetTimer Tick, 60000                      ; 每分钟执行一次
SetTimer Tick, 0                          ; 关闭
Tick() {
    FileAppend FormatTime() " 心跳`n", "hb.log"
}

; 等待类函数都带超时（不让脚本死等）
WinWait "ahk_exe notepad.exe", , 5
WinWaitActive "ahk_exe notepad.exe", , 5
WinWaitClose "ahk_exe notepad.exe", , 5
ClipWait 2
ProcessWait "notepad.exe", 5
KeyWait "Shift"
```

## 12. 指令（v2 全部 19 个）

```ahk
#Requires AutoHotkey v2.0            ; 版本要求
#SingleInstance Force                ; 单实例：Force / Ignore / Prompt / Off
#NoTrayIcon                          ; 隐藏托盘图标
#Warn All, Off                       ; 警告处理：MsgBox / StdOut / OutputDebug / Off
; #Include "lib\helper.ahk"          ; 包含文件（路径写错会直接报 cannot be opened）
; #IncludeAgain "x.ahk"              ; 允许重复包含
#HotIf WinActive("ahk_exe code.exe") ; 热键生效条件
#HotIfTimeout 1000                   ; 条件表达式超时
#Hotstring EndChars -()[]{}:;'"/\,.?!`n`t
#Hotstring NoMouse
#InputLevel 1
#UseHook                             ; 强制用钩子实现热键（兼容性问题时用）
#SuspendExempt                       ; 该热键在挂起时仍然生效
#ClipboardTimeout 1000
#DllLoad "user32.dll"                ; 预加载 DLL
#ErrorStdOut                         ; 语法错误输出到标准输出（校验器用）
#MaxThreads 10
#MaxThreadsBuffer true
#MaxThreadsPerHotkey 1
#WinActivateForce                    ; 强制激活窗口（对付顽固窗口）
```

`#Persistent`、`#KeyHistory`、`#MenuMaskKey`、`#InstallKeybdHook`、`#MaxHotkeysPerInterval`
**都不存在了**，改用函数或变量，详见 `v1-v2-pitfalls.md`。

## 13. 常用函数分类速查

> 完整签名查 `api-index.md`。下面是自动化场景最常用的。

```ahk
; —— 键盘鼠标 ——
Send "^c"                     ; 发送按键（会解析特殊字符）
SendText "纯文本内容"           ; 只发文本，不解析特殊键 ← 首选
SendEvent "^v"                ; 逐个事件发送，兼容某些老程序
SendInput "^v"                ; 最快（默认模式）
SendMode "Event"              ; 全局改模式
MouseMove 100, 200, 10        ; x, y, 速度
MouseClick "left", 100, 200   ; 按钮, x, y
Click "right"                 ; 在当前位置右键
Click 500, 300                ; 左键点指定位置
GetKeyState("Shift", "P")     ; 物理状态
KeyWait "Ctrl", "T3"          ; 等待按键，超时 3 秒
MouseGetPos &x, &y
SetScrollLockState "On"       ; 也可以 SetCapsLockState / SetNumLockState
BlockInput "MouseMove"        ; 屏蔽用户输入（部分系统需管理员）

; —— 剪贴板 ——
A_Clipboard := ""             ; 清空
A_Clipboard := "文本"
Send "^c"
if ClipWait(1)                ; 等剪贴板出现内容，超时 1 秒
    text := A_Clipboard
ClipWait()                    ; 保留原剪贴板内容
SavedClip := ClipboardAll()   ; 保存全部格式（图片等）
A_Clipboard := SavedClip      ; 还原

; —— 窗口 ——
if WinExist("ahk_exe notepad.exe") {
    WinActivate()
}
WinActivate "ahk_exe notepad.exe"
WinWaitActive "ahk_exe notepad.exe", , 3
WinGetTitle("ahk_id " hwnd)
WinGetPos(&x, &y, &w, &h, "ahk_exe notepad.exe")
WinMove(100, 100, 800, 600, "ahk_exe notepad.exe")
WinMinimize "ahk_exe notepad.exe"
WinMaximize "ahk_exe notepad.exe"
WinRestore "ahk_exe notepad.exe"
WinClose "ahk_exe notepad.exe"
WinKill "ahk_exe notepad.exe"
WinSetAlwaysOnTop true, "ahk_exe notepad.exe"
WinSetTransparent 200, "ahk_exe notepad.exe"
h := WinExist("A")            ; "A" = 当前活动窗口
WinGetList("ahk_class Notepad")
WinGetClass("ahk_id " h)
ControlSendText "文本", "Edit1", "ahk_class Notepad"   ; 后台向控件发文本
ControlClick "Button1", "ahk_class Notepad"

; —— 进程与运行 ——
Run "notepad.exe"
Run 'notepad.exe "D:\a.txt"'
RunWait "cmd.exe /c echo hi", , "Hide"
pid := Run("notepad.exe")
ProcessExist("notepad.exe")
ProcessWaitClose(pid, 10)
ProcessClose("notepad.exe")
ExitApp()
ExitApp(1)                    ; 带退出码
Run A_ComSpec " /c dir"       ; A_ComSpec = cmd.exe

; —— 文件与目录 ——
FileExist("D:\a.txt")         ; 返回属性字符串，空 = 不存在
DirExist("D:\folder")
FileRead("D:\a.txt", "UTF-8")
FileAppend("新一行`n", "D:\a.txt", "UTF-8")
FileDelete("D:\a.txt")
FileCopy("a.txt", "b.txt", 1)     ; 1 = 覆盖
FileMove("a.txt", "b.txt", 1)
DirCreate("D:\newdir")
DirCopy("D:\a", "D:\b", 1)
DirDelete("D:\a", 1)              ; 1 = 递归删除
FileGetSize("D:\a.txt")
FileGetTime("D:\a.txt")
Loop Files, "D:\data\*.txt" {     ; 遍历文件
    OutputDebug A_LoopFileName "  " A_LoopFileSize
}
Loop Read, "D:\a.txt" {           ; 逐行读取
    OutputDebug A_LoopReadLine
}
SplitPath("D:\a\b.txt", &name, &dir, &ext, &nameNoExt, &drive)

; —— 字符串与转换 ——
; 常用：StrLen / SubStr / InStr / StrReplace / StrSplit / Trim / Format / StrCompare
;       StrUpper / StrLower / StrTitle / Sort（完整签名见 api-index.md）
n1 := Integer("12")               ; 12
n2 := Float("1.5")                ; 1.5
s1 := String(42)                  ; "42"
t1 := Type(42)                    ; "Integer"
rnd := Random(1, 100)
r2 := Round(3.14159, 2)           ; 3.14
now := FormatTime(, "yyyy-MM-dd HH:mm:ss")
yesterday := DateAdd(A_Now, -1, "Days")
days := DateDiff(A_Now, yesterday, "Days")

; —— 系统 ——
SoundSetVolume 50             ; 0-100
SoundGetMute()
SoundPlay("C:\Windows\Media\notify.wav")
Shutdown(1)                   ; 1=关机 2=重启 4=休眠 8=待机
; 注册表：RegRead / RegWrite / RegDelete / RegCreateKey / RegDeleteKey
EnvGet("PATH")
EnvSet("MYVAR", "1")
TrayTip("标题", "内容")        ; 轻量气泡提示（不阻塞）
OutputDebug "调试输出"          ; 用 DebugView 查看，无窗口
; 常用内置变量：
; A_Clipboard  A_Now  A_TickCount  A_ScriptDir  A_ScriptFullPath  A_WorkingDir
; A_AppData  A_Desktop  A_Temp  A_ComputerName  A_UserName  A_AhkVersion
; A_IsAdmin  A_LineNumber  A_ThisHotkey  A_ScreenWidth  A_ScreenHeight  A_ScreenDPI

; —— 图像与像素（截图/找图找色）——
if PixelSearch(&px, &py, 0, 0, A_ScreenWidth, A_ScreenHeight, 0xFF0000, 10)
    OutputDebug "找到红点 " px "," py
if ImageSearch(&ix, &iy, 0, 0, A_ScreenWidth, A_ScreenHeight, "*80 button.png")
    MouseClick "left", ix, iy
col := PixelGetColor(A_ScreenWidth // 2, A_ScreenHeight // 2)
CaretGetPos(&cx, &cy)             ; 取输入光标位置（注意只有 2 个参数）
; 截图见 scripts/snippets/screenshot.ahk

; —— 网络与外部调用 ——
Download("https://example.com/a.txt", "a.txt")
whr := ComObject("WinHttp.WinHttpRequest.5.1")
whr.Open("GET", "https://api.example.com/data", false)
whr.Send()
resp := whr.ResponseText
DllCall("user32\GetSystemMetrics", "Int", 0)          ; 调 Win32 API
Run 'powershell -NoProfile -Command "Get-Date"'       ; 调外部命令
```

## 14. 命令行

```bash
# 运行脚本
"C:\Program Files\AutoHotkey\v2\AutoHotkey.exe" "D:\temp\a.ahk"
# 传参数（脚本内用 A_Args 读取）
AutoHotkey.exe a.ahk 参数1 参数2

# 只校验语法不执行（本 skill 校验器内部用的就是这个）
AutoHotkey.exe /ErrorStdOut /validate a.ahk
#   返回码 0 = 通过；2 = 加载期错误
#   /ErrorStdOut 把错误写到 stderr（⚠️ 警告类问题不受它管，仍会弹窗）
#   /CP65001 指定脚本代码页（默认已是 UTF-8，一般不需要）
```

```ahk
; 脚本内读命令行参数
if (A_Args.Length > 0)
    target := A_Args[1]
```

## 15. 调试手段（不弹窗的那种）

```ahk
OutputDebug "第 " A_LineNumber " 行：x=" x        ; 用 DebugView / VS Code 看
FileAppend A_Now " " msg "`n", "debug.log", "UTF-8"   ; 最简单，永远有效
TrayTip "状态", msg                               ; 用户可见的非阻塞提示（会被系统折叠）
ListLines()                                       ; 让报错窗口显示最近执行的行
KeyHistory()                                      ; 查看最近的按键历史
```
> 调试期**别用 `MsgBox`**：它是模态窗口，会把自动化流程卡住等人点击。
> `ListLines()` / `KeyHistory()` 会开信息窗口并把线程占住，无人值守时也会卡死 —— 调试完记得删。

## 16. 文件读写与编码（实测数据）

**这一节是踩出来的，务必照做**：写文件不显式指定编码，中文会变成乱码。

| 写法 | 实测结果 |
|---|---|
| `FileAppend(txt, f, "UTF-8")` | ✅ UTF-8 **带 BOM**；重复追加**只写一个** BOM |
| `FileAppend(txt, f, "UTF-8-RAW")` | ✅ UTF-8 **不带 BOM** |
| `FileAppend(txt, f)` | ❌ 按**系统 ANSI 码页**写（简中是 GBK）→ 用 UTF-8 工具打开就是乱码 |
| `FileRead(f, "UTF-8")` | ✅ 按 UTF-8 读 |
| `FileRead(f)` | 按系统 ANSI 读 → 读 UTF-8 文件里的中文会乱码 |

```ahk
; 推荐写法：读写都把编码写全
logFile := A_ScriptDir "\run.log"
FileAppend FormatTime(A_Now, "yyyy-MM-dd HH:mm:ss") " 启动`n", logFile, "UTF-8"
text := FileRead(logFile, "UTF-8")

; 要覆盖（而不是追加）文件：FileAppend 做不到，得用 FileOpen 的 "w" 模式
f := FileOpen(logFile, "w", "UTF-8")
f.Write("覆盖后的内容`n")
f.Close()
```

> 实测细节：
> - 追加 3 次 `"UTF-8"`，文件里**只有 1 个 BOM**（AHK 只在文件为空时写 BOM），所以日志可以放心反复追加。
> - 同一个脚本里混用有无编码的写法会产生"半乱码"文件，很难查 —— 统一都写 `"UTF-8"`。
