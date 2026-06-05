# C语言多模块编程

## 为什么需要多模块

随着程序规模增长，将所有代码放在一个文件中会导致：
- 编译时间剧增（每次修改都需重新编译整个文件）
- 代码难以维护和理解
- 团队协作困难
- 命名冲突

**解决方案**：将程序分解为多个源文件（.c）和头文件（.h）。

## 编译模型

### 翻译单元

每个 `.c` 文件是一个**翻译单元**（Translation Unit），独立编译为目标文件（`.o` 或 `.obj`）：

```
main.c ──→ main.o ──┐
                    ├─→ 链接器 ──→ program
utils.c ──→ utils.o ─┘
```

### 编译过程

```bash
# 分别编译
gcc -c main.c -o main.o
gcc -c utils.c -o utils.o

# 链接
gcc main.o utils.o -o program

# 一步完成
gcc main.c utils.c -o program
```

## 头文件设计

### 头文件的作用

头文件是模块的**接口声明**，包含：
- 函数原型
- 结构体/联合体/枚举声明
- 宏定义
- 类型定义（typedef）
- `extern` 变量声明

### 头文件保护

```c
// utils.h
#ifndef UTILS_H
#define UTILS_H

// 内容...

#endif // UTILS_H
```

### 头文件内容规范

**应该包含**：
```c
// math_utils.h
#ifndef MATH_UTILS_H
#define MATH_UTILS_H

#include <stddef.h>   // 需要的系统头文件

// 宏定义
#define PI 3.14159
#define MAX(a, b) ((a) > (b) ? (a) : (b))

// 类型定义
typedef struct {
    double real;
    double imag;
} Complex;

// 函数声明
Complex complex_add(Complex a, Complex b);
Complex complex_mul(Complex a, Complex b);
double complex_abs(Complex c);

// extern 变量声明（定义在 .c 文件中）
extern int math_error_count;

#endif
```

**不应该包含**：
- 函数定义（会导致重复定义）
- 变量定义（`extern` 除外）
- `static` 函数声明（仅限本文件）

### 包含顺序

```c
// 源文件中的包含顺序
#include "当前模块的头文件"    // 首先包含自己的头文件

#include <系统头文件>         // 然后系统头文件
#include "其他模块头文件"      // 最后其他模块
```

**原因**：如果头文件有依赖问题，首先暴露。

## 变量与函数的链接属性

### extern 声明

```c
// config.h
#ifndef CONFIG_H
#define CONFIG_H

extern int global_debug_level;   // 声明
extern char *global_config_path; // 声明

#endif

// config.c
#include "config.h"

int global_debug_level = 0;       // 定义
char *global_config_path = NULL;  // 定义

// main.c
#include "config.h"
// 可以使用 global_debug_level 和 global_config_path
```

### static 限制链接

```c
// utils.c
static int internal_counter = 0;   // 仅限本文件

static void helper(void) {         // 仅限本文件
    internal_counter++;
}

void public_function(void) {       // 可被其他文件调用
    helper();
}
```

## 模块设计原则

### 信息隐藏

```c
// stack.h - 公开接口
#ifndef STACK_H
#define STACK_H

typedef struct Stack Stack;   // 不透明指针，隐藏实现

Stack *stack_create(void);
void stack_destroy(Stack *s);
void stack_push(Stack *s, int value);
int stack_pop(Stack *s);
int stack_is_empty(const Stack *s);

#endif

// stack.c - 私有实现
#include "stack.h"
#include <stdlib.h>

struct Stack {
    int *data;
    int capacity;
    int top;
};

Stack *stack_create(void) {
    Stack *s = malloc(sizeof(Stack));
    s->capacity = 10;
    s->data = malloc(sizeof(int) * s->capacity);
    s->top = -1;
    return s;
}

// ... 其他实现
```

**优势**：
- 用户无法直接访问 `Stack` 内部成员
- 实现细节可以自由修改而不影响使用者
- 防止非法状态（如直接修改 `top`）

### 模块初始化与清理

```c
// module.h
#ifndef MODULE_H
#define MODULE_H

int module_init(void);    // 初始化，返回 0 表示成功
void module_cleanup(void); // 清理资源

#endif

// module.c
static int initialized = 0;

int module_init(void) {
    if (initialized) {
        return 0;   // 已经初始化
    }
    // 分配资源...
    initialized = 1;
    return 0;
}

void module_cleanup(void) {
    if (!initialized) {
        return;
    }
    // 释放资源...
    initialized = 0;
}
```

## Makefile 基础

```makefile
# Makefile
CC = gcc
CFLAGS = -Wall -Wextra -std=c11 -g
TARGET = program
SRCS = main.c utils.c stack.c
OBJS = $(SRCS:.c=.o)

# 默认目标
all: $(TARGET)

# 链接
$(TARGET): $(OBJS)
	$(CC) $(OBJS) -o $(TARGET)

# 编译规则
%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

# 清理
clean:
	rm -f $(OBJS) $(TARGET)

# 依赖关系
main.o: main.c utils.h stack.h
utils.o: utils.c utils.h
stack.o: stack.c stack.h

.PHONY: all clean
```

## 常见错误

### 1. 重复定义

```c
// utils.h
int global_count = 0;   // 错误！头文件中定义了变量

// 如果多个 .c 文件包含 utils.h，链接时会报错：multiple definition

// 正确做法
// utils.h
extern int global_count;   // 声明

// utils.c
int global_count = 0;      // 定义（只在一个 .c 文件中）
```

### 2. 头文件循环包含

```c
// a.h
#include "b.h"

// b.h
#include "a.h"   // 循环包含！
```

**解决**：前向声明

```c
// a.h
#ifndef A_H
#define A_H

struct B;   // 前向声明，不需要包含 b.h

struct A {
    struct B *b;   // 指针可以前向声明
};

#endif
```

### 3. 内联函数定义位置

```c
// utils.h
inline int max(int a, int b) {   // 内联函数定义在头文件中
    return (a > b) ? a : b;
}

// 如果编译器不内联，需要在某个 .c 文件中提供外部定义
// utils.c
extern inline int max(int a, int b);   // C99 方式
```

### 4. 未声明函数

```c
// main.c
void process(void);   // 忘记包含头文件，手动声明

// 如果 utils.h 中 process 的参数改变，这里不会同步更新
// 导致链接时类型不匹配或运行时错误
```

## 学习要点总结

1. 每个 .c 文件是一个翻译单元，头文件是模块的接口声明
2. 头文件用 `#ifndef` 或 `#pragma once` 防止重复包含
3. 变量在头文件中用 `extern` 声明，在单个 .c 文件中定义
4. 使用不透明指针（`typedef struct Name Name`）隐藏实现细节
5. 避免头文件循环包含，使用前向声明解决
