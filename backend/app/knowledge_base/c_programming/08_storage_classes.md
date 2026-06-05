# C语言作用域与存储类

## 作用域（Scope）

作用域决定标识符在程序的哪些区域可见。

### 块作用域（Block Scope）

```c
void func(void) {
    int a = 10;           // a 的作用域从声明开始到块结束
    {
        int a = 20;       // 内层 a 隐藏外层 a
        printf("%d\n", a);  // 输出 20
    }
    printf("%d\n", a);     // 输出 10，内层 a 已销毁
}
```

**变量隐藏（Shadowing）**：内层同名变量会隐藏外层变量。编译器通常会警告。

### 文件作用域（File Scope）

```c
int global_var = 10;      // 文件作用域，从声明到文件末尾

static int file_static;   // 文件作用域，但仅限本文件

void func(void) {
    // 可以访问 global_var 和 file_static
}
```

### 函数作用域（Function Scope）

仅适用于 `goto` 标签：

```c
void func(void) {
    goto label;    // 合法
    label:         // 标签在整个函数内可见
        // ...
}
```

### 函数原型作用域

```c
int func(int x, int y);   // x 和 y 只在原型中有效
```

## 链接属性（Linkage）

链接属性决定标识符在多个翻译单元（源文件）间是否共享。

| 链接属性 | 含义 | 示例 |
|:---|:---|:---|
| 外部链接（External） | 可被其他文件访问 | 普通全局变量/函数 |
| 内部链接（Internal） | 仅限当前文件 | `static` 全局变量/函数 |
| 无链接（None） | 仅限当前块 | 局部变量 |

```c
// file1.c
int global = 10;          // 外部链接
static int file_only = 5; // 内部链接

void public_func(void) { }    // 外部链接
static void private_func(void) { }  // 内部链接

// file2.c
extern int global;        // 引用 file1.c 的 global
// extern int file_only;  // 错误！file_only 是内部链接
```

## 存储期（Storage Duration）

存储期决定变量在内存中存在的时间。

### 自动存储期（Automatic）

```c
void func(void) {
    int local = 10;       // 自动存储期，进入块时创建，退出时销毁
    auto int x = 20;      // auto 关键字（C11 前），显式但冗余
}
```

**特点**：
- 存储在栈上
- 未初始化时值不确定（垃圾值）
- 递归时每个调用有独立的副本

### 静态存储期（Static）

```c
static int count = 0;     // 静态存储期，程序启动时创建，结束时销毁

void func(void) {
    static int call_count = 0;  // 静态局部变量
    call_count++;
    printf("被调用了 %d 次\n", call_count);
}
```

**静态局部变量的特点**：
- 只初始化一次（在程序启动时）
- 值在函数调用间保持
- 作用域仍是块作用域，但存储期是全局的

```c
void counter(void) {
    static int count = 0;   // 只执行一次初始化
    count++;
    printf("%d\n", count);
}

counter();  // 输出 1
counter();  // 输出 2
counter();  // 输出 3
```

### 线程存储期（Thread）

C11 引入：

```c
_Thread_local int thread_var;   // 每个线程有独立副本
```

### 动态存储期（Allocated）

```c
int *p = malloc(sizeof(int));   // 动态分配，直到 free 才释放
```

## 存储类说明符

### auto

```c
auto int x = 10;   // C11 前：自动存储期（默认，几乎不用）
// C11 起：auto 用于类型推导（类似 C++ auto）
auto y = 10;       // y 的类型为 int（C11 起）
```

### register

```c
register int i;    // 建议编译器将变量存储在寄存器中
```

**现代意义**：
- 编译器优化已经足够好，几乎不需要手动指定
- C99 起不能对 `register` 变量取地址（因为它可能在寄存器中）
- 现在主要作为语义提示：这个变量频繁使用

### static

`static` 有两个完全不同的含义：

**1. 局部变量：改变存储期**

```c
void func(void) {
    static int count = 0;   // 静态存储期，值保持
}
```

**2. 全局变量/函数：改变链接属性**

```c
static int internal;        // 内部链接，仅限本文件
static void helper(void) { }  // 内部链接，仅限本文件
```

### extern

```c
// file1.c
int global = 10;

// file2.c
extern int global;          // 声明（不是定义），引用 file1.c 的变量
```

**`extern` 不分配存储**，只是告诉编译器 "这个变量在其他地方定义"。

**陷阱**：如果同时初始化，就变成定义了：

```c
extern int x = 10;   // 有初始化，这是定义！不是声明
```

### _Thread_local（C11）

```c
_Thread_local int tls_var;   // 每个线程独立
```

## 完整示例

```c
// 文件作用域，外部链接
int global_count = 0;

// 文件作用域，内部链接
static int file_private = 0;

// 文件作用域，内部链接
static void helper(void) {
    // 只能在本文件调用
}

void public_func(void) {
    // 块作用域，自动存储期
    int local = 10;

    // 块作用域，静态存储期
    static int persistent = 0;
    persistent++;

    helper();   // 可以调用内部函数
}
```

## 常见错误

### 1. 混淆 static 的两种含义

```c
static int x;       // 文件作用域：内部链接

void func(void) {
    static int y;   // 块作用域：静态存储期
}
```

### 2. 未初始化的静态变量

```c
static int x;       // 自动初始化为 0
static int *p;      // 自动初始化为 NULL

void func(void) {
    int y;          // 未初始化，垃圾值
}
```

### 3. 静态局部变量的线程安全问题

```c
char *get_string(void) {
    static char buffer[100];   // 所有调用共享同一块内存
    sprintf(buffer, "value: %d", rand());
    return buffer;               // 线程不安全！
}
```

多线程环境下，静态局部变量需要同步保护或使用线程局部存储。

### 4. 重复定义

```c
// header.h
int global = 10;    // 错误！头文件中定义了外部链接变量

// 正确做法：头文件中声明，某个 .c 文件中定义
// header.h
extern int global;

// source.c
int global = 10;
```

## 学习要点总结

1. 作用域决定可见性，链接属性决定跨文件共享，存储期决定生命周期
2. `static` 对局部变量改变存储期，对全局变量/函数改变链接属性
3. `extern` 是声明不是定义，有初始化就变成定义
4. 静态变量自动初始化为0，自动变量不会
5. 静态局部变量在函数调用间保持值，但存在线程安全问题
