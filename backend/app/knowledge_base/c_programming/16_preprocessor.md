# C语言预处理器与宏

## 预处理器的作用

预处理器在编译之前处理源代码，主要功能：
- 文件包含（`#include`）
- 宏定义（`#define`）
- 条件编译（`#if`、`#ifdef` 等）
- 行控制（`#line`）
- 错误指令（`#error`）

预处理是**纯文本替换**，没有类型检查，没有语法分析。

## #include

### 两种形式

```c
#include <stdio.h>     // 系统头文件，在系统目录查找
#include "myheader.h"  // 用户头文件，先在当前目录查找
```

### 头文件保护

防止重复包含导致的重复定义错误：

```c
// myheader.h
#ifndef MYHEADER_H
#define MYHEADER_H

// 头文件内容...

#endif // MYHEADER_H
```

**C11 替代方案**：

```c
#pragma once   // 非标准但几乎所有编译器都支持
```

### 头文件内容规范

头文件应该包含：
- 函数声明（不是定义）
- 结构体/联合体/枚举声明
- 宏定义
- 类型定义（typedef）
- `extern` 变量声明

**不应该包含**：
- 函数定义（除非 inline）
- 变量定义（会导致重复定义）
- `using namespace`（C++）

## #define 宏

### 对象式宏

```c
#define PI 3.14159
#define MAX_SIZE 100
#define DEBUG 1
```

**宏不是变量**，没有类型，不占内存，是编译前的文本替换。

### 函数式宏

```c
#define SQUARE(x) ((x) * (x))
#define MAX(a, b) ((a) > (b) ? (a) : (b))
```

**括号的重要性**：

```c
#define SQUARE_BAD(x) x * x
SQUARE_BAD(3 + 2);      // 展开为 3 + 2 * 3 + 2 = 11，不是 25！

#define SQUARE_GOOD(x) ((x) * (x))
SQUARE_GOOD(3 + 2);     // 展开为 ((3 + 2) * (3 + 2)) = 25
```

**副作用陷阱**：

```c
int a = 5, b = 3;
int m = MAX(a++, b++);   // 展开为 ((a++) > (b++) ? (a++) : (b++))
// a 和 b 可能被增加两次！
```

### 多行宏

```c
#define SWAP(a, b) do {     typeof(a) temp = (a);     (a) = (b);     (b) = temp; } while(0)
```

**`do { ... } while(0)` 技巧**：
- 允许在宏中使用分号
- 保证宏作为单条语句使用（如 `if` 后面）
- 避免空语句警告

```c
if (condition)
    SWAP(a, b);   // 展开为 do { ... } while(0);，正确
else
    // ...
```

### 字符串化（#）

```c
#define STRINGIFY(x) #x
STRINGIFY(hello);        // 展开为 "hello"
STRINGIFY(1 + 2);        // 展开为 "1 + 2"
```

### 标记连接（##）

```c
#define CONCAT(a, b) a ## b
CONCAT(var, 123);        // 展开为 var123
```

**应用场景**：生成变量名或函数名

```c
#define DEFINE_GETTER(type, name)     type get_##name(void) {         return name;     }

DEFINE_GETTER(int, count);   // 生成 int get_count(void) { return count; }
```

### 可变参数宏（C99）

```c
#define LOG(fmt, ...) printf("[LOG] " fmt "\n", ##__VA_ARGS__)

LOG("Value: %d", 42);      // 展开为 printf("[LOG] Value: %d\n", 42);
LOG("Hello");               // 展开为 printf("[LOG] Hello\n");
```

**`##__VA_ARGS__`**：当 `__VA_ARGS__` 为空时，删除前面的逗号。

## 条件编译

### #ifdef / #ifndef

```c
#ifdef DEBUG
    printf("Debug mode\n");
#endif

#ifndef PI
    #define PI 3.14
#endif
```

### #if / #elif / #else

```c
#if defined(DEBUG) && DEBUG > 0
    #define LOG_LEVEL DEBUG
#elif defined(RELEASE)
    #define LOG_LEVEL 0
#else
    #define LOG_LEVEL 1
#endif
```

### 预定义宏

| 宏 | 含义 |
|:---|:---|
| `__FILE__` | 当前源文件名 |
| `__LINE__` | 当前行号 |
| `__func__` | 当前函数名（C99） |
| `__DATE__` | 编译日期 "Mmm dd yyyy" |
| `__TIME__` | 编译时间 "hh:mm:ss" |
| `__STDC__` | 标准C编译器定义为1 |
| `__STDC_VERSION__` | C标准版本号 |

```c
#define LOG_ERROR(msg)     fprintf(stderr, "[%s:%d %s] ERROR: %s\n",             __FILE__, __LINE__, __func__, msg)

void process(void) {
    LOG_ERROR("Invalid input");
    // 输出：[main.c:42 process] ERROR: Invalid input
}
```

### 平台检测

```c
#ifdef _WIN32
    #include <windows.h>
    #define OS_NAME "Windows"
#elif defined(__linux__)
    #include <unistd.h>
    #define OS_NAME "Linux"
#elif defined(__APPLE__)
    #define OS_NAME "macOS"
#endif
```

## 宏的高级技巧

### X-Macros

```c
#define COLORS     X(RED,   0xFF0000)     X(GREEN, 0x00FF00)     X(BLUE,  0x0000FF)

// 生成枚举
enum Color {
    #define X(name, value) COLOR_##name = value,
    COLORS
    #undef X
};

// 生成字符串数组
const char *color_names[] = {
    #define X(name, value) #name,
    COLORS
    #undef X
};
```

### 编译期断言

```c
#define STATIC_ASSERT(expr)     typedef char static_assert_##__LINE__[(expr) ? 1 : -1]

STATIC_ASSERT(sizeof(int) == 4);   // 如果为假，编译错误：数组大小为负
```

C11 标准提供了 `_Static_assert`：

```c
_Static_assert(sizeof(int) == 4, "int must be 4 bytes");
```

## 宏的陷阱与最佳实践

### 1. 宏名冲突

```c
#define max(a, b) ((a) > (b) ? (a) : (b))

// 如果代码中有变量名 max
int max = 10;   // 被替换为 int ((10) > (b) ? (10) : (b)) = 10;  编译错误！
```

**解决**：宏名全大写，或使用 `do { ... } while(0)` 封装。

### 2. 多次求值

```c
#define MAX(a, b) ((a) > (b) ? (a) : (b))

int x = 5;
int m = MAX(x++, 10);   // x 可能被增加两次
```

**解决**：使用内联函数（C99 `inline`）或 `typeof` + 临时变量：

```c
#define SAFE_MAX(a, b) ({     typeof(a) _a = (a);     typeof(b) _b = (b);     _a > _b ? _a : _b; })
```

### 3. 优先级问题

```c
#define ADD(a, b) a + b
int x = ADD(1, 2) * 3;   // 展开为 1 + 2 * 3 = 7，不是 9

// 正确
#define ADD(a, b) ((a) + (b))
```

### 4. 分号问题

```c
#define INIT(x) x = 0;

if (condition)
    INIT(a);    // 展开为 a = 0;，没问题
else
    INIT(b);    // 展开为 else a = 0; b = 0;  语法错误！

// 解决：使用 do { ... } while(0)
#define INIT(x) do { x = 0; } while(0)
```

## 学习要点总结

1. 预处理器是纯文本替换，没有类型检查，宏名全大写避免冲突
2. 函数式宏必须给所有参数加括号，避免优先级问题
3. 宏参数有副作用时可能被多次求值，用 `do { ... } while(0)` 封装多行宏
4. 头文件必须用 `#ifndef` 或 `#pragma once` 防止重复包含
5. 优先使用 `inline` 函数替代复杂宏，编译器有类型检查且可调试
