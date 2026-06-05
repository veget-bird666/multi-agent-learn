# C语言标准与可移植性

## C标准演进

| 标准 | 年份 | 主要特性 |
|:---|:---|:---|
| C89/C90 | 1989/1990 | 第一个标准化版本 |
| C95 | 1995 | 少量修正，宽字符支持 |
| C99 | 1999 | 重大更新：//注释、变长数组、stdint、复数、inline、restrict、long long |
| C11 | 2011 | 多线程、原子操作、Unicode、匿名结构体、静态断言、对齐 |
| C17/C18 | 2017/2018 | 修复C11的缺陷，无新特性 |
| C23 | 2023 | 属性语法、constexpr、typeof、数字分隔符 |

## 编译器支持

```bash
# 指定标准
gcc -std=c89 program.c
gcc -std=c99 program.c
gcc -std=c11 program.c
gcc -std=c17 program.c
gcc -std=c23 program.c

# 使用 GNU 扩展
gcc -std=gnu11 program.c   # C11 + GNU 扩展
```

## C99 重要特性

### 单行注释

```c
// C99 起支持单行注释
/* C89 只能用多行注释 */
```

### 变长数组（VLA）

```c
void process(int n) {
    int arr[n];   // C99 变长数组，C11 起变为可选特性
    // ...
}
```

**注意**：VLA 在 C11 中是可选的，某些嵌入式编译器不支持。C23 已移除。

### stdint.h

```c
#include <stdint.h>

int8_t   i8;     // 精确 8 位有符号整数
uint8_t  u8;     // 精确 8 位无符号整数
int16_t  i16;    // 精确 16 位
uint16_t u16;
int32_t  i32;    // 精确 32 位
uint32_t u32;
int64_t  i64;    // 精确 64 位
uint64_t u64;

intptr_t  iptr;  // 可以存储指针的整数类型
uintptr_t uptr;
```

**优势**：跨平台类型大小一致。

### 复数类型

```c
#include <complex.h>

double complex z = 1.0 + 2.0*I;
double real_part = creal(z);
double imag_part = cimag(z);
```

### 内联函数

```c
inline int max(int a, int b) {
    return (a > b) ? a : b;
}
```

### restrict 关键字

```c
void add(int *restrict a, int *restrict b, int n) {
    for (int i = 0; i < n; i++) {
        a[i] += b[i];
    }
}
```

`restrict` 承诺指针是访问该内存的唯一方式，允许编译器优化。

## C11 重要特性

### 多线程支持

```c
#include <threads.h>

int thread_func(void *arg) {
    printf("Thread running\n");
    return 0;
}

int main(void) {
    thrd_t t;
    thrd_create(&t, thread_func, NULL);
    thrd_join(t, NULL);
    return 0;
}
```

**注意**：C11 线程支持在某些平台上不完整，POSIX 线程（pthread）更常用。

### 原子操作

```c
#include <stdatomic.h>

_Atomic int counter = 0;

void increment(void) {
    atomic_fetch_add(&counter, 1);
}
```

### 静态断言

```c
_Static_assert(sizeof(int) == 4, "int must be 4 bytes");
```

编译时检查，失败时编译错误。

### 匿名结构体和联合体

```c
struct Person {
    char name[20];
    struct {
        int year;
        int month;
        int day;
    };   // 匿名结构体
};

struct Person p;
p.year = 1990;   // 直接访问匿名结构体成员
```

### 对齐支持

```c
#include <stdalign.h>

alignas(16) char buffer[64];   // 16 字节对齐

// 或
_Alignas(16) int arr[10];
```

## 可移植性编程

### 条件编译

```c
#ifdef __STDC_VERSION__
    #if __STDC_VERSION__ >= 201112L
        // C11 或更新
        #define C11_SUPPORTED
    #elif __STDC_VERSION__ >= 199901L
        // C99
        #define C99_SUPPORTED
    #endif
#endif
```

### 平台抽象

```c
// platform.h
#ifdef _WIN32
    #include <windows.h>
    #define PATH_SEP '\\'
    #define sleep(ms) Sleep(ms)
#else
    #include <unistd.h>
    #define PATH_SEP '/'
    #define sleep(ms) usleep((ms) * 1000)
#endif
```

### 整数类型选择

```c
#include <stdint.h>

// 需要精确大小时
uint32_t flags;     // 必须是 32 位

// 需要至少某大小时
unsigned long count;   // 至少 32 位

// 指针相关
uintptr_t ptr_as_int;   // 可以存储指针的整数
```

### 字节序处理

```c
#include <stdint.h>

// 标准方式检测大小端
union {
    uint32_t i;
    uint8_t c[4];
} u = {0x01020304};

#define IS_LITTLE_ENDIAN (u.c[0] == 0x04)
```

## 常见可移植性问题

### 1. 整数大小

```c
// 错误：假设 int 是 32 位
int big_value = 3000000000;   // 在 16 位系统上溢出

// 正确
#include <stdint.h>
int32_t big_value = 3000000000;
```

### 2. 指针大小

```c
// 错误：假设指针是 4 字节
int ptr_size = sizeof(void *);   // 64 位系统上是 8

// 正确
size_t ptr_size = sizeof(void *);
```

### 3. char 的符号性

```c
// char 可能是有符号或无符号，取决于编译器
char c = 200;   // 如果 char 有符号，200 溢出

// 正确
unsigned char c = 200;
```

### 4. 右移行为

```c
int x = -1;
x >> 1;   // 算术右移还是逻辑右移？实现定义！

// 正确
unsigned int ux = (unsigned int)x;
ux >> 1;   // 保证逻辑右移
```

## 学习要点总结

1. C99 是广泛支持的现代标准，提供 //注释、stdint、inline、restrict 等
2. C11 引入多线程、原子操作、静态断言，但线程支持不完整
3. 使用 `stdint.h` 中的固定宽度类型保证跨平台一致性
4. 不要假设整数大小、指针大小、char 符号性、大小端
5. 用条件编译处理平台差异，优先使用标准库函数
