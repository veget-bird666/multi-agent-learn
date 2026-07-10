# C++ 预处理器

## 预处理器的作用

预处理器在**编译之前**处理源代码，主要功能：

- 文件包含（`#include`）
- 宏定义（`#define` / `#undef`）
- 条件编译（`#if`、`#ifdef`、`#ifndef` 等）
- 编译器指令（`#pragma`）
- 行控制（`#line`）
- 错误指令（`#error`、部分编译器支持 `#warning`）

```
源文件 → [预处理器] → 翻译单元（无 # 指令） → 编译器 → 目标文件 → 链接器
```

预处理是**纯文本替换**，没有类型检查，没有完整语法分析。C++ 中应**尽量少用宏**，优先 `constexpr`、模板、inline 函数。

## #include 文件包含

### 两种形式

```cpp
#include <iostream>       // 系统/标准库头文件，在系统 include 路径查找
#include "myheader.h"     // 用户头文件，通常先在当前目录查找
```

**include 路径**由编译器 `-I` 选项指定。构建系统（CMake 等）应正确设置 include 目录。

### 头文件保护（Include Guards）

防止同一头文件被多次展开导致重复定义：

```cpp
// myheader.h
#ifndef MYHEADER_H
#define MYHEADER_H

// 头文件内容...

#endif // MYHEADER_H
```

**C++ 广泛支持的替代**：

```cpp
#pragma once   // 非标准但几乎所有主流编译器支持
```

| 方式 | 优点 | 缺点 |
|:---|:---|:---|
| `#ifndef` / `#define` | 标准、可移植 | 宏名需唯一 |
| `#pragma once` | 简洁 | 理论上非标准（实际可用） |

### 头文件应包含什么

**应该包含**：
- 函数声明（非定义，除非 inline）
- 类/结构体/枚举声明或定义（若成员需要完整类型）
- 模板声明与定义（模板通常放头文件）
- `constexpr` / `inline` 变量（C++17 inline 变量）
- 类型别名、`using` 声明

**不应该包含**：
- 非 inline 函数定义（导致 ODR 违反）
- 非 inline、非 `constexpr` 的全局变量定义
- `using namespace std;`（污染所有 include 者）

```cpp
// good.h
#ifndef GOOD_H
#define GOOD_H

#include <vector>
#include <string>

class Foo;   // 前向声明，减少依赖

class Good {
    std::vector<int> data;
    std::string name;
public:
    void process(const Foo& f);
};

#endif
```

## #define 宏

### 对象式宏

```cpp
#define PI 3.14159
#define MAX_SIZE 1024
#define DEBUG 1
```

**现代替代**：

```cpp
constexpr double PI = 3.14159;
constexpr int MAX_SIZE = 1024;
```

### 函数式宏

```cpp
#define MAX(a, b) ((a) > (b) ? (a) : (b))
#define SQUARE(x) ((x) * (x))
#define LOG(msg) std::cout << "[LOG] " << msg << std::endl
```

**括号的重要性**：

```cpp
#define SQUARE_BAD(x) x * x
SQUARE_BAD(1 + 2);   // 展开为 1 + 2 * 1 + 2 = 5，不是 9

#define SQUARE(x) ((x) * (x))
SQUARE(1 + 2);       // ((1 + 2) * (1 + 2)) = 9
```

**副作用陷阱**：

```cpp
int x = 5, y = 3;
int m = MAX(x++, y++);   // x 或 y 可能被递增两次！
```

**现代替代**：用 `inline` 函数或模板：

```cpp
template<typename T>
constexpr const T& max(const T& a, const T& b) {
    return (a > b) ? a : b;
}
```

### 多行宏

```cpp
#define SWAP(a, b) do { \
    auto temp = (a);    \
    (a) = (b);          \
    (b) = temp;         \
} while(0)
```

`do { ... } while(0)` 保证宏在任意上下文中像一条语句一样使用（如 if 后只跟一条语句）。

### # 与 ## 运算符

```cpp
#define STR(x) #x           // 字符串化："hello"
#define CONCAT(a, b) a##b   // 连接：foo##bar → foobar

#define LOG_VAR(v) std::cout << #v << " = " << (v) << std::endl
LOG_VAR(count);   // 输出 count = 42
```

### 取消定义

```cpp
#undef PI
```

## 条件编译

```cpp
#define DEBUG 1

#if DEBUG
    #define DBG(x) std::cout << x << std::endl
#else
    #define DBG(x)
#endif

#ifdef _WIN32
    // Windows 特定代码
#elif defined(__linux__)
    // Linux 特定代码
#elif defined(__APPLE__)
    // macOS 特定代码
#else
    #error "Unsupported platform"
#endif

#if __cplusplus >= 201703L
    // C++17 及以上
#endif

#if defined(__has_include)
    #if __has_include(<filesystem>)
        #include <filesystem>
    #endif
#endif
```

### 常用条件

| 宏 | 含义 |
|:---|:---|
| `_DEBUG` / `NDEBUG` | MSVC 调试 / 发布（`NDEBUG` 禁用 assert） |
| `__GNUC__` | GCC 编译器 |
| `_MSC_VER` | MSVC 编译器 |
| `__cplusplus` | C++ 标准版本数值 |

### #if vs #ifdef

```cpp
#ifdef FOO        // 仅检查是否定义
#if FOO == 1      // 检查值
#if defined(FOO)  // 等价于 #ifdef FOO，但可组合
```

## 预定义宏

| 宏 | 含义 |
|:---|:---|
| `__FILE__` | 当前源文件名 |
| `__LINE__` | 当前行号 |
| `__func__` | 当前函数名（C++11） |
| `__cplusplus` | C++ 标准版本（如 201703L） |
| `__DATE__` / `__TIME__` | 编译日期与时间 |

```cpp
#include <cassert>

void divide(int a, int b) {
    assert(b != 0);   // NDEBUG 定义时 assert 被移除
}

// 自定义日志
#define LOG_LOC(msg) \
    std::cerr << __FILE__ << ":" << __LINE__ << " " << msg << std::endl
```

## #error 与 #warning

```cpp
#if __cplusplus < 201703L
    #error "This project requires C++17 or later"
#endif

#if defined(_MSC_VER) && _MSC_VER < 1920
    #warning "Old MSVC detected, some features may be unavailable"
#endif
```

`#error` 中止编译；`#warning` 非标准，GCC/Clang 支持。

## #pragma 编译器指令

```cpp
#pragma once                              // 头文件保护
#pragma pack(push, 1)                     // 结构体 1 字节对齐（MSVC）
#pragma pack(pop)

#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-variable"
#pragma GCC diagnostic pop
```

**可移植性**：`#pragma` 多为编译器特定。跨平台代码应尽量少依赖，或用 `#ifdef` 分支。

## 编译期断言

```cpp
// C++11
static_assert(sizeof(int) >= 4, "int must be at least 4 bytes");

// C++17
static_assert(std::is_integral_v<int>);

// C++23：依赖 false 的 static_assert
template<typename T>
void foo() {
    static_assert(false, "Not implemented");   // C++23 前对模板实例化有问题
}
```

优于仅用 `#error` + 宏，错误信息更清晰，且与类型系统结合。

## 特性测试宏（C++20）

```cpp
#include <version>

#if __cpp_lib_ranges >= 201911L
    #include <ranges>
    // 使用 ranges
#endif

#if __cpp_concepts >= 201907L
    // 使用 concepts
#endif
```

查阅 `<version>` 头与编译器文档确认特性是否可用。

## 模块（C++20，了解）

模块旨在替代部分 `#include`，加快编译、改善接口隔离：

```cpp
// math.cppm（模块接口单元）
export module math;

export int add(int a, int b) { return a + b; }
export double pi() { return 3.14159; }

// main.cpp
import math;

int main() {
    return add(1, 2);
}
```

**现状**（2024–2026）：工具链与生态仍在普及，多数项目仍以头文件为主。了解概念即可，不必强行迁移。

## 头文件与编译模型

### 翻译单元

每个 `.cpp` 文件经预处理后成为独立**翻译单元**，分别编译再链接：

```
main.cpp  ──→ main.o  ──┐
utils.cpp ──→ utils.o ──┼──→ 链接器 ──→ program
```

### 减少编译依赖

1. 头文件中用**前向声明**代替 `#include`
2. 实现细节放 `.cpp`（PIMPL 惯用法）
3. 避免在头文件中 `#include` 大型模板库

```cpp
// widget.h — PIMPL 简化接口
class Widget {
    struct Impl;
    std::unique_ptr<Impl> pImpl;
public:
    Widget();
    ~Widget();
    void draw();
};
```

### 内联函数与 ODR

```cpp
// header.h
inline int helper(int x) { return x * 2; }   // 可在头文件定义

// C++17
inline constexpr int MAX = 100;   // inline 变量
```

非 inline 函数、非 inline 变量在头文件中定义会导致**重复定义**链接错误。

## X-Macro 模式（高级）

用宏列表生成重复代码：

```cpp
#define COLOR_LIST \
    X(Red)           \
    X(Green)         \
    X(Blue)

enum class Color {
#define X(name) name,
    COLOR_LIST
#undef X
};

const char* colorName(Color c) {
    switch (c) {
#define X(name) case Color::name: return #name;
        COLOR_LIST
#undef X
    }
    return "Unknown";
}
```

适合枚举与字符串映射等重复结构，但应适度使用。

## 常见错误

### 1. 宏参数无括号

```cpp
#define SQUARE(x) x * x
SQUARE(1 + 2);   // 1 + 2 * 1 + 2 = 5
// 正确
#define SQUARE(x) ((x) * (x))
```

### 2. 头文件循环依赖

A.h include B.h，B.h include A.h → 编译失败。用前向声明打破：

```cpp
// a.h
class B;   // 前向声明，不 include b.h
class A { void use(B& b); };
```

### 3. 在头文件定义变量

```cpp
// header.h — 错误
int globalVar = 0;   // 每个 include 的 .cpp 都有一份定义

// 正确
extern int globalVar;           // header
int globalVar = 0;              // 某一个 .cpp
// 或 C++17
inline int globalVar = 0;       // header（inline 变量）
```

### 4. 过度使用宏

能用 `constexpr`、`const`、`inline` 函数、模板替代的，不要用宏。宏不参与命名空间，无类型安全，调试困难。

### 5. 头文件 using namespace std

```cpp
// bad.h
using namespace std;   // 污染所有 include 此头文件的翻译单元
```

### 6. include 顺序不当

建议顺序：对应头文件 → C 库 → C++ 库 → 第三方 → 项目内头文件。部分项目要求先 include 自身头文件以验证自洽。

## 学习要点总结

1. `#include` 引入声明，必须用 include guards 或 `#pragma once`
2. 宏无类型安全，优先 `constexpr`、inline 函数和模板
3. 条件编译实现跨平台分支与调试开关
4. `static_assert` 做编译期检查，优于纯宏方案
5. 头文件最小化依赖，多前向声明，禁止 `using namespace std`
6. 理解翻译单元与 ODR，非 inline 定义放 `.cpp`
7. C++20 模块是 `#include` 的演进方向，生态仍在成熟中
