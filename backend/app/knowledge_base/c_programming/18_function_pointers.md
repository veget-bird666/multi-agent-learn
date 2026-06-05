# C语言函数指针与回调机制

## 函数指针基础

函数在内存中也有地址，可以声明指针指向函数。

### 声明语法

```c
// 返回类型 (*指针名)(参数列表)
int (*func_ptr)(int, int);

// 对比
int *func_ptr(int, int);    // 这是声明一个函数，返回 int*
int (*func_ptr)(int, int);  // 这是函数指针
```

**记忆方法**：`(*func_ptr)` 表示 func_ptr 是一个指针，`(int, int)` 表示指向接受两个 int 参数的函数。

### 赋值与调用

```c
int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }

int (*op)(int, int);

op = add;           // 函数名退化为函数指针
op = &add;          // 等价写法

int result = op(3, 4);      // 调用 add(3, 4)，result = 7
int result = (*op)(3, 4);   // 等价写法，更明确
```

**注意**：`op = add` 和 `op = &add` 完全等价，函数名在表达式中退化为函数指针。

### typedef 简化

```c
typedef int (*BinaryOp)(int, int);

BinaryOp op = add;
int result = op(3, 4);
```

## 回调函数

### 什么是回调

回调函数是作为参数传递给另一个函数的函数，由被调用者在适当时机调用。

```c
// 通用遍历函数
void foreach(int *arr, int n, void (*callback)(int)) {
    for (int i = 0; i < n; i++) {
        callback(arr[i]);   // 调用回调函数
    }
}

// 回调函数
void print_int(int x) {
    printf("%d ", x);
}

void print_square(int x) {
    printf("%d ", x * x);
}

// 使用
int arr[] = {1, 2, 3, 4, 5};
foreach(arr, 5, print_int);     // 输出：1 2 3 4 5
foreach(arr, 5, print_square);  // 输出：1 4 9 16 25
```

### qsort 标准库函数

```c
#include <stdlib.h>

void qsort(void *base, size_t nmemb, size_t size,
           int (*compar)(const void *, const void *));
```

**比较函数**：
- 返回 < 0：a 在 b 前面
- 返回 == 0：a 和 b 相等
- 返回 > 0：a 在 b 后面

```c
int compare_int(const void *a, const void *b) {
    int ia = *(const int *)a;
    int ib = *(const int *)b;
    return (ia > ib) - (ia < ib);   // 避免溢出
}

int arr[] = {3, 1, 4, 1, 5, 9, 2, 6};
qsort(arr, 8, sizeof(int), compare_int);
```

**降序排列**：

```c
int compare_int_desc(const void *a, const void *b) {
    return compare_int(b, a);   // 交换 a 和 b
}
```

**结构体排序**：

```c
typedef struct {
    char name[20];
    int score;
} Student;

int compare_student_by_score(const void *a, const void *b) {
    const Student *sa = a;
    const Student *sb = b;
    return sa->score - sb->score;   // 按分数升序
}

Student students[] = {...};
qsort(students, 10, sizeof(Student), compare_student_by_score);
```

### bsearch 二分查找

```c
void *bsearch(const void *key, const void *base,
              size_t nmemb, size_t size,
              int (*compar)(const void *, const void *));

int key = 5;
int *result = bsearch(&key, arr, 8, sizeof(int), compare_int);
if (result != NULL) {
    printf("找到：%d\n", *result);
}
```

**注意**：`bsearch` 要求数组已排序。

## 函数指针数组

```c
typedef int (*Operation)(int, int);

Operation ops[] = {
    add, sub, mul, div
};

// 简单的计算器
int calculate(int a, int b, int op_index) {
    return ops[op_index](a, b);
}

int result = calculate(10, 5, 0);   // 10 + 5 = 15
```

**应用场景**：状态机、命令分发、插件系统。

## 信号处理

```c
#include <signal.h>

typedef void (*sighandler_t)(int);

sighandler_t signal(int signum, sighandler_t handler);

void handler(int sig) {
    printf("收到信号 %d\n", sig);
}

signal(SIGINT, handler);   // Ctrl+C 时调用 handler
```

## 比较函数指针

```c
if (op == add) {
    printf("当前是加法\n");
}

// 函数指针可以比较
void (*p1)(int) = print_int;
void (*p2)(int) = print_int;
if (p1 == p2) { }   // 可能为真（同一函数）
```

## 常见错误

### 1. 声明与定义不匹配

```c
// 声明
void process(int (*callback)(int));

// 错误定义
void process(int *callback(int)) {   // 这是函数返回 int*，不是函数指针
    // ...
}

// 正确定义
void process(int (*callback)(int)) {
    // ...
}
```

### 2. 回调函数签名不匹配

```c
void foreach(int *arr, int n, void (*callback)(int));

void bad_callback(int x, int y) { }   // 参数不匹配
foreach(arr, 5, bad_callback);         // 编译错误
```

### 3. 空指针调用

```c
void (*callback)(int) = NULL;
callback(10);   // 段错误！

// 安全做法
if (callback != NULL) {
    callback(10);
}
```

## 学习要点总结

1. 函数指针声明：`返回类型 (*指针名)(参数列表)`，typedef 可以大幅简化
2. 回调函数是将函数作为参数传递，由被调用者执行，实现解耦和扩展
3. `qsort` 和 `bsearch` 是标准库中回调的典型应用
4. 函数指针数组可以实现状态机、命令分发等模式
5. 始终检查函数指针是否为 NULL 再调用
