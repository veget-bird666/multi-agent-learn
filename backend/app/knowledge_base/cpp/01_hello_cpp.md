# C++ 环境搭建与第一个程序

## C++ 是什么？

C++ 是 Bjarne Stroustrup 于 1979 年在 C 语言基础上发展而来的**多范式编程语言**。它保留了 C 的高效与底层控制能力，同时引入了**面向对象、泛型编程、RAII 资源管理**等现代特性。

### C 与 C++ 的关系

```
C 语言:     过程式，手动内存管理，无类/模板/异常/引用
C++:        几乎兼容 C 语法，增加了 OOP、STL、模板、异常、命名空间等
编译器:     g++ / clang++ 可编译 .c 和 .cpp；.cpp 默认按 C++ 规则处理
链接库:     C++ 程序通常额外链接 libstdc++（GCC）或 libc++（Clang）
```

**重要**：C++ 不是"带类的 C"。有效使用 C++ 意味着利用 RAII、`std::vector`、智能指针、`enum class` 等现代机制，而不是写"C 风格的 C++"。

## 从源代码到可执行文件

C++ 同样是**编译型语言**，整体流程与 C 相同，但编译器在 C 的基础上增加了**名字修饰（Name Mangling）**、**模板实例化**、**异常处理表生成**等步骤。

### 编译的四个阶段

```
hello.cpp (源代码)
    ↓
[预处理器 cpp] → 处理 #include, #define, #ifdef；展开宏；处理条件编译
    ↓
[编译器 cc1plus] → 词法/语法分析、语义分析、模板实例化 → 生成汇编 .s
    ↓
[汇编器 as] → 将汇编翻译成机器码 → 生成目标文件 .o / .obj
    ↓
[链接器 ld] → 合并多个 .o、解析符号、重定位 → 链接 libstdc++ 等库 → 生成可执行文件
```

你可以用 GCC 观察每个阶段：

```bash
g++ -E hello.cpp -o hello.i    # 仅预处理
g++ -S hello.i -o hello.s      # 编译到汇编
g++ -c hello.s -o hello.o        # 汇编到目标文件
g++ hello.o -o hello             # 链接生成可执行文件
```

### 为什么 C++ 链接比 C 更复杂？

**1. 名字修饰（Name Mangling）**

C 语言中，函数名在目标文件中就是 `main`、`printf`。C++ 支持**函数重载**，同名不同参的函数必须生成不同符号：

```cpp
void print(int x);
void print(double x);
// 目标文件中可能是 _Z5printi 和 _Z5printd（Itanium ABI，因编译器而异）
```

链接器通过修饰后的名字区分重载版本。若声明与定义签名不一致，可能链接失败或产生难以调试的运行时错误。

**2. C 链接互操作**

与 C 库交互时，需告诉编译器使用 C 的名字规则：

```cpp
extern "C" {
    #include <stdio.h>   // printf 等符号不被 C++ 名字修饰
}
```

**3. 标准库依赖**

C++ 的 `std::cout` 等实现在 C++ 标准库中。纯 C 程序只链接 `libc`；C++ 程序通常还要链接 `libstdc++`（或 MSVC 的对应库）。

### 与 C 编译流程的对比

| 阶段 | C | C++ 额外处理 |
|:---|:---|:---|
| 预处理 | `#include` 文本替换 | 相同，另处理 `#pragma once` 等 |
| 编译 | C 语法 → 汇编 | C++ 语法、模板实例化、异常表 |
| 汇编 | 汇编 → 机器码 | 相同 |
| 链接 | 解析 C 符号 | 解析修饰后的 C++ 符号 + 标准库 |

## 第一个程序的深度解析

```cpp
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
```

### 逐行剖析

**`#include <iostream>`**
- 这是**预处理指令**，不是 C++ 语句，末尾不需要分号
- `<>` 表示在系统头文件目录查找；`""` 表示先当前目录再系统目录
- C++ 标准头文件**无 `.h` 后缀**（如 `<iostream>`，不是 `<iostream.h>`）
- 预处理器将 `iostream` 的内容**文本插入**到此处——不是 Java/Python 式的模块导入
- 该头文件声明了 `std::cout`、`std::cin`、`std::endl` 等

**`std::cout`**
- `cout` = **C**haracter **Out**put，标准输出流对象（类型为 `std::ostream`）
- `<<` 是**流插入运算符**，将右侧数据"插入"左侧流，支持链式调用
- `std::` 是**命名空间**前缀，避免与用户自定义的 `cout` 冲突

**`std::endl`**
- 输出换行符 `\n`，并**刷新（flush）**输出缓冲区
- 性能敏感场景可用 `'\n'` 代替，避免每次输出都强制 flush

**`int main()`**
- C++ 标准规定 `main` 必须返回 `int`（`void main()` 是非标准的）
- C++ 中 `main` 省略 `return` 时等价于 `return 0`（C99 起 C 也支持，但 C++ 更早明确）
- 与 C 不同：C 中 `int main()` 表示参数未指定；C++ 中 `int main()` 等价于 `int main(void)`，即无参数

**`return 0;`**
- 返回值传给操作系统：0 表示成功，非 0 表示错误码
- 在 `main` 中可省略，编译器自动补 `return 0`

### 与 C 版 Hello World 的对比

| 方面 | C | C++ |
|:---|:---|:---|
| 头文件 | `#include <stdio.h>` | `#include <iostream>` |
| 输出 | `printf("Hello, World!\n");` | `std::cout << "Hello, World!" << std::endl;` |
| 类型安全 | 格式串 `%d` 与参数不匹配 → 未定义行为 | 编译期检查 `<<` 两侧类型 |
| 缓冲 | `printf` 行缓冲，`\n` 触发刷新 | `endl` 强制刷新；`'\n'` 仅换行 |

```c
// C 版本
#include <stdio.h>
int main(void) {
    printf("Hello, World!\n");
    return 0;
}
```

### 程序在内存中的布局

当程序运行时，操作系统分配虚拟内存空间，C++ 与 C 布局相同：

```
高地址
┌─────────────────┐
│    栈 (Stack)    │ ← 局部变量、函数参数、返回地址，向下增长
│                 │
├─────────────────┤
│    堆 (Heap)     │ ← new/malloc 分配，向上增长
│                 │
├─────────────────┤
│   数据段 (Data)  │ ← 全局变量、静态变量
│   - 已初始化     │
│   - 未初始化(BSS)│
├─────────────────┤
│  代码段 (Text)   │ ← 编译后的机器指令，只读
└─────────────────┘
低地址
```

**C++ 特有**：`std::cout` 等标准流对象通常在程序启动时由库在静态存储区构造（静态初始化），在 `main` 之前完成；程序结束时析构。这涉及**静态初始化顺序**问题（复杂项目需注意）。

## 命名空间

```cpp
#include <iostream>
using namespace std;   // 不推荐在头文件中使用

int main() {
    cout << "Hello" << endl;
    return 0;
}
```

### 命名空间的本质

命名空间是**名字的作用域划分**，解决大型项目中符号名冲突，不是运行时概念，零开销。

```cpp
namespace MyLib {
    void print() { /* ... */ }
}
namespace Other {
    void print() { /* ... */ }
}

MyLib::print();    // 调用 MyLib 中的 print
Other::print();    // 调用 Other 中的 print
```

### 最佳实践（防御式编程）

- 在 `.cpp` 文件中可局部 `using std::cout;`
- **永远不要在头文件**中写 `using namespace std;`，会污染所有 include 该头文件的翻译单元
- 优先使用 `std::` 前缀，或仅在函数体内 `using`

## 开发环境搭建

### Linux / macOS

```bash
# 检查编译器
g++ --version
# 或
clang++ --version

# 编译并运行
g++ hello.cpp -o hello -Wall -Wextra -std=c++17
./hello
```

### Windows

**MinGW-w64 / MSYS2**：
```bash
g++ hello.cpp -o hello.exe -Wall -Wextra -std=c++17
hello.exe
```

**Visual Studio**：安装"使用 C++ 的桌面开发"工作负载，使用 MSVC 编译器。

**CMake + Ninja**（推荐用于较大项目）：
```cmake
cmake_minimum_required(VERSION 3.16)
project(hello CXX)
add_executable(hello hello.cpp)
set(CMAKE_CXX_STANDARD 17)
```

### 推荐的编译命令模板

```bash
g++ program.cpp -o program -Wall -Wextra -Werror -std=c++17 -g -O0
```

| 选项 | 含义 |
|:---|:---|
| `-Wall -Wextra` | 开启常见和额外警告 |
| `-Werror` | 警告视为错误，强制写出干净代码 |
| `-std=c++17` | 使用 C++17 标准（入门推荐；C++20/23 按需选用） |
| `-g` | 生成调试信息，供 GDB/LLDB 使用 |
| `-O0` | 关闭优化，调试时变量值不会被优化掉 |

## C++ 与 C 的头文件混用

```cpp
// C++ 方式包含 C 头文件（推荐）
#include <cstdio>    // 等价于 C 的 stdio.h，符号在 std 命名空间
#include <cstring>   // 等价于 string.h

std::printf("Hello\n");   // 或通过 using
// 或
using std::printf;

// 兼容旧 C 代码
extern "C" {
    #include "legacy_c_header.h"
}
```

**原因**：`<cstdio>` 将 C 函数放入 `std` 命名空间，同时可能注入全局命名空间（实现定义），避免与 C++ 自定义符号冲突。

## 常见错误与排查

### 1. 忘记 `#include <iostream>`

```cpp
int main() {
    cout << "Hello";   // 错误：cout 未声明
}
```

**原因**：编译器不知道 `cout` 是什么。C++ 没有 C89 那种"隐式 int"的宽松规则，会直接报错。

### 2. 使用已废弃的 `<iostream.h>`

```cpp
#include <iostream.h>   // 非标准！旧编译器扩展
```

**原因**：C++ 标准库头文件无 `.h` 后缀。`<iostream.h>` 将名字注入全局命名空间，与现代 C++ 规范不符。

### 3. 混用 C 和 C++ 风格 I/O 导致同步问题

```cpp
#include <iostream>
#include <cstdio>

int main() {
    printf("C style\n");
    std::cout << "C++ style\n";
}
```

**原因**：C++ 标准流默认与 C 的 `stdin`/`stdout` 同步（`std::ios::sync_with_stdio(true)`），混用可能带来性能损失或输出顺序问题。新代码应统一风格；必须混用时了解 `sync_with_stdio(false)` 的副作用。

### 4. 返回值类型错误

```cpp
void main() {   // 错误！main 必须返回 int
}
```

**原因**：C++ 标准明确规定 `main` 返回 `int`。某些编译器扩展允许 `void main()`，但不可移植。

### 5. 忘记换行或 flush 导致输出延迟

```cpp
std::cout << "Hello";   // 可能不立即显示
```

**原因**：`cout` 通常绑定到行缓冲的 `stdout`。解决：加 `<< std::endl` 或 `<< '\n'`，或 `std::cout.flush()`。

### 6. 头文件中 `using namespace std`

```cpp
// bad_header.h
using namespace std;   // 污染所有 include 此头文件的代码
```

**原因**：可能导致符号冲突、ADL（参数依赖查找）意外行为，是大型项目的维护噩梦。

## 翻译单元与多文件项目预览

单个 `.cpp` 文件经编译器处理后产生一个**翻译单元（Translation Unit）**，对应一个 `.o` 目标文件：

```
main.cpp  →  main.o  ┐
utils.cpp →  utils.o ┼→ 链接器 → program.exe
math.cpp  →  math.o  ┘
```

**头文件（.h/.hpp）** 不参与单独编译，被 `#include` 插入到 `.cpp` 中。因此：

- 头文件放**声明**（函数原型、类定义）
- 源文件放**定义**（函数体、全局变量定义）
- 使用 **include guard** 或 `#pragma once` 防止重复包含

```cpp
// mylib.h
#ifndef MYLIB_H
#define MYLIB_H
void greet(const char* name);
#endif

// mylib.cpp
#include "mylib.h"
#include <iostream>
void greet(const char* name) {
    std::cout << "Hello, " << name << std::endl;
}
```

**与 C 相同**：一个变量/函数在整个程序中只能**定义一次**（ODR），但可**声明**多次。

## 学习要点总结

1. C++ 几乎兼容 C，但应使用现代 C++ 风格（RAII、STL、智能指针），而非"C 风格 C++"
2. 编译流程与 C 类似，但多了名字修饰、模板实例化和 C++ 标准库链接
3. `#include` 是文本替换，不是模块导入；C++ 头文件无 `.h` 后缀
4. 使用 `#include <iostream>` 和 `std::` 前缀是标准做法
5. 推荐 `-std=c++17 -Wall -Wextra -Werror` 编译，把警告当错误处理
6. 头文件中禁止使用 `using namespace std;`
7. `main` 必须返回 `int`，省略 `return` 时等价于 `return 0`
