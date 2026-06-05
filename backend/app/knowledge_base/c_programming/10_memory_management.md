# C语言动态内存管理

## 内存布局回顾

程序运行时，操作系统分配虚拟地址空间：

```
高地址
┌──────────────────┐
│     栈区 (Stack)  │ ← 局部变量，自动分配释放，向下增长
│                  │
├──────────────────┤
│     堆区 (Heap)   │ ← malloc/free 管理，向上增长
│                  │
├──────────────────┤
│    数据段 (Data)   │ ← 全局变量、静态变量
│   - 已初始化 (.data)│
│   - 未初始化 (.bss) │
├──────────────────┤
│   代码段 (Text)    │ ← 机器指令，只读
└──────────────────┘
低地址
```

**栈 vs 堆**：
- **栈**：自动管理，速度快，空间有限（通常1-8MB），数据生命周期跟随函数
- **堆**：手动管理，速度较慢，空间较大（受限于物理内存+交换空间），生命周期由程序员控制

## malloc 家族

### malloc

```c
#include <stdlib.h>

int *p = (int *)malloc(sizeof(int) * 100);   // 分配 400 字节
if (p == NULL) {
    perror("malloc failed");
    exit(EXIT_FAILURE);
}
// 使用 p...
free(p);
p = NULL;   // 避免野指针
```

**为什么需要强制类型转换？**

C++ 需要，C 不需要（`malloc` 返回 `void*`）。但显式转换：
- 提高代码可移植性（C++ 兼容）
- 如果忘记 `#include <stdlib.h>`，没有声明时编译器假设返回 `int`，转换会报错

**sizeof 的用法**：

```c
int *arr = malloc(100 * sizeof(int));        // 如果 int 大小改变会出错
int *arr = malloc(100 * sizeof(*arr));       // 更好：根据指针指向的类型自动计算
int *arr = malloc(sizeof(int[100]));          // 最佳：直接分配数组大小
```

### calloc

```c
int *arr = calloc(100, sizeof(int));   // 分配 100 个 int，全部初始化为 0
```

**malloc vs calloc**：
- `malloc`：不初始化，速度略快
- `calloc`：清零初始化，适合需要零值的场景
- `calloc` 的参数分开传递，有助于检测溢出：`calloc(n, size)` 会检查 `n * size` 是否溢出

### realloc

```c
int *new_arr = realloc(arr, sizeof(int) * 200);   // 扩展到 200 个元素
if (new_arr == NULL) {
    // 扩展失败，原 arr 仍然有效！
    free(arr);
    exit(EXIT_FAILURE);
}
arr = new_arr;
```

**realloc 的行为**：
- 如果新大小更小：截断，原数据保留
- 如果新大小更大：
  - 原位置有足够连续空间：原地扩展
  - 没有足够空间：分配新块，复制数据，释放旧块
- 如果传入 `NULL`：等价于 `malloc`
- 如果新大小为 0：行为未定义（某些实现等价于 `free`）

**安全使用 realloc**：

```c
// 危险！如果 realloc 失败，原指针丢失，内存泄漏
arr = realloc(arr, new_size);

// 安全
void *tmp = realloc(arr, new_size);
if (tmp != NULL) {
    arr = tmp;
}
```

### free

```c
free(ptr);      // 释放 ptr 指向的内存
ptr = NULL;     // 好习惯：避免野指针
```

**free 的规则**：
- 只能释放 `malloc`/`calloc`/`realloc` 分配的内存
- 不能重复释放同一块内存
- 不能释放栈上的内存
- 传入 `NULL` 是安全的（什么都不做）

## 常见内存错误

### 1. 内存泄漏

```c
void leaky(void) {
    int *p = malloc(sizeof(int) * 100);
    // 使用 p...
    // 忘记 free！
}   // p 是局部变量，函数返回后丢失，但堆内存仍然占用
```

**检测工具**：Valgrind

```bash
valgrind --leak-check=full ./program
```

### 2. 使用已释放内存（Use-after-free）

```c
int *p = malloc(sizeof(int));
free(p);
*p = 10;        // 未定义行为！可能崩溃，可能静默错误
```

### 3. 重复释放（Double Free）

```c
free(p);
free(p);        // 未定义行为！可能破坏堆管理结构
```

### 4. 越界访问

```c
int *arr = malloc(sizeof(int) * 10);
arr[10] = 0;    // 越界！写入未分配的内存
free(arr);
```

### 5. 释放非堆内存

```c
int local;
free(&local);   // 灾难！栈内存不能 free
```

## 动态二维数组

### 方法1：数组指针

```c
int (*matrix)[COLS] = malloc(sizeof(int[ROWS][COLS]));
matrix[i][j] = 10;   // 连续内存，缓存友好
free(matrix);
```

### 方法2：指针数组（不连续内存）

```c
int **matrix = malloc(sizeof(int *) * ROWS);
for (int i = 0; i < ROWS; i++) {
    matrix[i] = malloc(sizeof(int) * COLS);
}

// 使用...
matrix[i][j] = 10;

// 释放：必须先释放每一行，再释放指针数组
for (int i = 0; i < ROWS; i++) {
    free(matrix[i]);
}
free(matrix);
```

**对比**：
- 方法1：内存连续，一次分配/释放，缓存友好
- 方法2：内存不连续，每行可独立调整大小，释放复杂

## 柔性数组（Flexible Array Member）

C99 特性：结构体最后一个成员可以是大小未知的数组。

```c
struct Packet {
    int header;
    int size;
    char data[];   // 柔性数组，不占结构体大小
};

// 分配
struct Packet *p = malloc(sizeof(struct Packet) + 100);
p->size = 100;
strcpy(p->data, "Hello");

// 释放
free(p);   // 一次释放
```

**优势**：
- 只需要一次 malloc/free
- 内存连续，缓存友好
- 比 `char *data` + 额外 malloc 更高效

## 内存对齐

### 为什么需要对齐？

硬件访问内存时通常按字长（4或8字节）读取。未对齐访问可能导致：
- 性能下降（需要多次读取）
- 某些架构直接崩溃（如 ARM）

### alignas 和 aligned_alloc

```c
#include <stdalign.h>

// 变量对齐
alignas(64) char cache_line[64];   // 64字节对齐，适合缓存行

// 动态分配对齐内存
void *p = aligned_alloc(64, 1024);   // 64字节对齐，分配1024字节
free(p);
```

## 自定义内存池

对于频繁分配释放小对象，系统 malloc/free 开销大。可以实现简单的内存池：

```c
#define POOL_SIZE 1024
#define BLOCK_SIZE 64

static char pool[POOL_SIZE];
static int pool_index = 0;

void *pool_alloc(size_t size) {
    if (pool_index + size > POOL_SIZE) {
        return NULL;   // 池已满，回退到 malloc
    }
    void *p = &pool[pool_index];
    pool_index += size;
    return p;
}

void pool_reset(void) {
    pool_index = 0;   // 一次性"释放"所有内存
}
```

## 学习要点总结

1. `malloc` 不初始化，`calloc` 清零初始化，`realloc` 调整大小
2. `free` 后必须将指针置 `NULL`，避免野指针和重复释放
3. 每次 `malloc` 必须有对应的 `free`，使用 Valgrind 检测泄漏
4. 柔性数组适合变长数据结构，只需一次分配/释放
5. 注意内存对齐，未对齐访问在某些平台会导致崩溃
