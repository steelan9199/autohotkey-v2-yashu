# AutoHotkey v2 报错速查（错误原文 → 根因 → 修法）

> 本文件里所有报错原文都是**本机 v2.0.26 实测抓取**的，不是转述。
> 用法：把报错消息在本文里搜一下，直接看修法。

## 0. 先搞懂报错长什么样

### 加载期（编译/解析）错误

格式固定为 `文件 (行号) : ==> 消息`，下一行常跟一句 `Specifically:` 指明罪魁：

```
D:\temp\a.ahk (12) : ==> Function calls require a space or "(".  Use comma only between parameters.
     Specifically: MsgBox, "hello"
```

**返回码**：`0` = 加载通过，`2` = 加载期错误。校验器 `ahk_check.py` 就是看这个。

### 运行期错误对象

`try/catch as e` 抓到的 `e` 有这些字段（都实测可用）：

| 字段 | 内容 | 例子 |
|---|---|---|
| `e.What` | 出错的函数/操作 | `WinActivate`、`Array.Prototype.__Item.Get` |
| `e.Message` | 主要消息 | `Target window not found.` |
| `e.Extra` | 补充信息 | 窗口标识、越界下标、变量名 |
| `e.File` | 文件路径 | |
| `e.Line` | 行号 | |
| `e.Stack` | 调用栈（多行） | |
| `Type(e)` | 错误类型 | `TargetError`、`OSError` |

> ⚠️ **AHK 运行期错误默认会弹模态对话框**，无人值守脚本就此卡死。
> 所以：可能失败的调用一律套 `try/catch`，或者用 `scripts/ahk_run.py` 跑一遍。

---

## 1. 加载期错误速查

| 报错原文 | 根因 | 修法 |
|---|---|---|
| `Syntax error. Did you mean to use ":="?` | 写了 v1 的 `x = 1` | 改成 `x := 1` |
| `Function calls require a space or "(".  Use comma only between parameters.` | 写了 v1 命令式逗号语法 | 删掉名字后的逗号：`MsgBox "hi"`、`Loop 5`、`SetKeyDelay 10, 50` |
| `Missing ending "%"` | 用 `%` 当取余运算符 | 改 `Mod(a, b)`。`c := 7 % 2` 必错 |
| `Unexpected "If"` / `Unexpected "Loop"` | 把多条语句挤在 `{ }` 里 | `{` 之后必须换行，逐行写 |
| `This Func cannot be used as an output variable.  Specifically: Add` | 变量名和函数名撞了（**大小写不敏感**） | 换名字。定义了 `Add()` 就不能再写 `add := ...` |
| `Duplicate hotkey.  Specifically: ^!x` | 同一个热键定义了两次 | 删掉一个；或 `#Include` 的片段里已经定义过 |
| `This line does not contain a recognized action.` | v1 指令（`#NoEnv`）或整行语法不对 | 查 `v1-v2-pitfalls.md` 第四节 |
| `Missing "}"` | 花括号没配对 | 补齐；或用了"单行块" |
| `Missing """` | 字符串没闭合 | 补引号。注意反引号才是转义符 |
| `Syntax error.  Specifically: .)` | 悬空/误用的点号 | 点号拼接删掉，用空格拼接 |
| `#Include file "..." cannot be opened.` | 被包含的文件路径不存在 | 检查路径；用 `%A_ScriptDir%\` 打头 |
| `Too few parameters passed to function.  Specifically: StrLen` | 必填参数没给 | 按 `api-index.md` 的签名补参数 |
| `Too many parameters passed to function.  Specifically: WinActivate` | 参数给多了 | 同上（全部参数可选的函数不会报这个） |
| `This built-in variable cannot be used as an output variable.  Specifically: A_Now` | 给只读内建变量赋值 | 查 `api-index.md` 的「可写变量」（131 个里只有 37 个可写） |
| `Invalid key name.  Specifically: NotAKey_zzz` | 热键/热字串的键名写错 | 查键名列表；字母、数字、`F1`-`F24`、`WheelUp`… |
| `Parameter #1 required  Specifically: if` | 写了没有表达式的 `if` | `if` 后必须跟条件表达式 |
| `Illegal character in expression.` | 表达式里有非法字符（常见于未加引号的路径） | 路径要加引号：`IfExist` → `if FileExist("C:\Windows")` |
| `Label not found in current scope.  Specifically: X` | v1 的 `Goto X` | 用函数/循环重构，v2 不推荐跳转 |
| `Unexpected operator following literal string.` | 字符串字面量后面跟了算术运算符，如 `"abc" + 1` | 先转换：`Integer(StrReplace("abc", ...))`，或检查是不是想拼接（改用空格） |
| `This variable is read-only`（部分场景运行期才报） | 同上 | 同上 |

> 💡 **一个绝招**：参数个数、只读变量赋值这两类问题**一定会被加载期抓到**，
> 所以交付前跑一次校验，能挡掉一大半低级错误。

---

## 2. 运行期错误速查

按 `e.Message` 排序。`Type(e)` 那一列在 `catch 具体类型 as e` 时用得上。

| `e.Message` | 类型 | `e.Extra` | 典型场景与修法 |
|---|---|---|---|
| `Target window not found.` | `TargetError` | 窗口标识 | `WinActivate` / `WinGetPos` / `WinClose` 等**找不到窗口**。这些函数在 v2 里找不到目标会**抛异常**（v1 只是设置 ErrorLevel）。修法：先 `if WinExist(...)` 判断，或套 `try/catch` |
| `Divide by zero.` | `ZeroDivisionError` | — | `/`、`//` 或 `Mod()` 的分母为 0。修法：先判断分母，或 `catch ZeroDivisionError` |
| `Invalid index.` | `IndexError` | 越界的下标 | 数组越界。`arr := [1,2]` 后 `arr[9]` 就报这个。**下标从 1 开始**，且 `arr.Length` 是上限 |
| `Item has no value.` | `UnsetItemError` | 键名 | `Map` 取/删一个不存在的键。**注意类型是 `UnsetItemError` 不是 `IndexError`**。修法：先 `if m.Has(k)` |
| `This value of type "Object" has no property named "zzz".` | `PropertyError` | — | 用点号读了不存在的属性。修法：`o.HasProp("zzz")` 判断，或用 `Map` 代替裸对象 |
| `This global variable has not been assigned a value.` | `UnsetError` | 变量名 | 用了没赋值的变量。**也用于"调用了不存在的函数"** —— 见本文件第 3 节 |
| `This local variable has not been assigned a value.` | `UnsetError` | 变量名 | 同上，但变量在函数内。**常见于把内建变量名写错**，例如 `A_UserProfile`（不存在） |
| `(3) 系统找不到指定的路径。` | `OSError` | — | `FileRead` / `FileOpen` / `FileAppend` 的目录不存在。**先 `DirExist()` 或 `DirCreate()`** |
| `(2) 系统找不到指定的文件。` | `OSError` | — | 同上，文件级 |
| `(5) 拒绝访问。` | `OSError` | — | 权限不足 / 文件被占用 / 只读 |
| `Failed attempt to launch program or document:` | `Error` | 系统消息 | `Run` 的目标不存在或不是可执行文件 |
| `(0x800401F3) 无效的类字符串` | `Error` | — | `ComObject("...")` 的 ProgID 拼错，或该组件未安装 |
| `Failed to load DLL.` | `Error` | DLL 名 | `DllCall` 里 DLL 路径/名字不对。`user32\` 这类系统 DLL 不用写 `.dll` 后缀 |
| `Parameter #1 of SetTimer requires an Object, but received a String.` | `TypeError` | 实参值 | 参数类型不对。`SetTimer "FuncName", 1000` 错在传了字符串，要传**函数对象**：`SetTimer FuncName, 1000` |
| `Parameter #1 of Integer.Call requires a Number, but received a String.` | `TypeError` | 实参值 | `Integer("abc")` 这类转换失败。修法：先 `IsNumber()` 判断 |
| `Invalid key name.` | `ValueError` | 键名 | `Hotkey("NoSuchKey", ...)` 动态注册时的键名错 |

> **关于中文乱码**：`OSError` 的消息来自 Windows `FormatMessage`，按**系统 ANSI 码页（简中是 GBK）**输出，
> 而 AHK 自己的报错按 UTF-8 输出。所以日志里可能出现两种编码混在一起、`OSError` 那半句变乱码。
> 这不影响排错 —— **看括号里的错误码就够了**：`(2)` 文件不存在、`(3)` 路径不存在、`(5)` 拒绝访问。

---

## 3. 那类"不报错只报警告"的坑

有一批问题**加载期返回码 0**，只在 `#Warn All` 下吐一条警告，然后运行时才炸：

```
a.ahk (2) : ==> Warning: This global variable appears to never be assigned a value.
     Specifically: StringReplace
```

**只要看到 `Specifically: <名字>`，就去核对那个名字。** 常见触发源：

- v1 旧函数名：`StringReplace`、`IfWinExist`、`GetPixelColor`
- 函数名拼错：`StrinReplace`
- 调用不存在的函数：`NoSuchLabel()`
- v1 命令式（**不带逗号**）：`SetEnv x, 1`、`StringReplace s, a, b`、`IfMsgBox Yes`、`IfGreater x, 1`、`Gosub Label`

自检：把那个名字在 `references/api-index.md` 里 Grep 一次。查不到 = 写错了。
完整清单和原理见 `v1-v2-pitfalls.md` 第一节。

---

## 4. 排错三步法

```bash
PY="D:/software/uv/python/cpython-3.14.7-windows-x86_64-none/python.exe"
S="C:/Users/Administrator/.workbuddy/skills/autohotkey-v2-yashu"

# ① 校验：抓加载期错误 + v1 遗留写法 + 函数名核对（不执行脚本，零副作用）
"$PY" "$S/scripts/ahk_check.py" "D:\temp\a.ahk" --strict

# ② 试跑：真的跑一遍，try/catch 兜住运行期错误，超时自动强杀（不弹窗）
"$PY" "$S/scripts/ahk_run.py" "D:\temp\a.ahk" --timeout 6
```

③ 还没头绪，就给关键步骤加日志（**别用 `MsgBox`**，它会卡住脚本）：

```ahk
try {
    FileRead "D:\可能不存在的文件.txt"          ; ← 换成你真正要保护的调用
} catch as e {
    msg := Type(e) " | " e.What " | " e.Message " | " e.Extra
    msg := msg " @ " e.File ":" e.Line
    FileAppend FormatTime(A_Now, "HH:mm:ss") " " msg "`n",
        A_ScriptDir "\error.log", "UTF-8"
    ; 顺手把调用栈也写下来，定位嵌套调用很省事
    FileAppend e.Stack "`n", A_ScriptDir "\error.log", "UTF-8"
}
```

**逐段二分**是定位问题最快的手段：把脚本后半段整段注释掉，看还报不报错，
再逐步放开 —— 比盯着代码猜快得多。

---

## 5. 高频翻车点回顾（跟 `recipes.md` 附录一致）

| 现象 | 真相 |
|---|---|
| 文字里的 `!` `^` `#` `{` `}` 变成了按键 | 用了 `Send`。文本必须用 `SendText` |
| 改文件后内容翻倍 | 用了 `FileAppend`（追加）。覆盖要用 `FileOpen(path, "w")` |
| 点按钮点偏了 | 忘记 `CoordMode "Mouse", "Screen"`；或颜色字节序写成 `0xRRGGBB`（应为 `0xBBGGRR`） |
| 脚本跑一阵就卡住不动 | 某处弹了模态框（`MsgBox` / `InputBox`）或开了信息窗口（`ListLines`）在等人点 |
| 中文全变乱码 | 脚本文件存成了 GBK。AHK v2 一律按 UTF-8 读 |
