# C语言函数基础

## 函数的本质

函数是C程序的基本构建块。从底层看，函数调用涉及：
1. **参数传递**：将实参值压入栈（或寄存器）
2. **跳转**：保存返回地址，跳转到函数代码
3. **执行**：运行函数体
4. **返回**：将返回值放入约定位置，跳回调用处

## 函数声明与定义

### 声明（原型）

```c
// 告诉编译器：存在这样一个函数，参数和返回值类型是什么
int add(int a, int b);
void print_message(const char *msg);
```

**为什么需要声明？**

编译器是单遍的（从左到右扫描）。如果函数定义在使用之后，编译器会不知道参数类型，导致默认参数提升（`char`→`int`，`float`→`double`），可能产生错误。

### 定义

```c
int add(int a, int b) {
    return a + b;
}
```

**声明和定义的区别**：声明不分配内存，定义分配内存并给出实现。

### 隐式函数声明（已废弃）

在C89中，如果调用未声明的函数，编译器会假设它返回 `int`。这在C99中已移除，但某些编译器仍允许（带警告）。

```c
// 没有声明
int result = unknown_func(3.14);   // 编译器假设返回 int，参数为 double
// 实际函数可能定义为：float unknown_func(int x);
// 类型不匹配，未定义行为！
```

## 参数传递机制

### 值传递

C语言**所有参数都是值传递**：

```c
void swap_wrong(int a, int b) {
    int temp = a;
    a = b;
    b = temp;
    // 只修改了局部副本，外部变量不变
}

void swap_correct(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}
```

**理解值传递**：

```c
void func(int x) {
    x = 10;   // 修改的是形参 x（局部变量），不影响实参
}

int main(void) {
    int a = 5;
    func(a);      // 将 a 的值（5）复制给 x
    printf("%d\n", a);   // 输出 5
}
```

### 数组作为参数

```c
void process(int arr[], int n);      // 等价于 void process(int *arr, int n)
void process(int *arr, int n);       // 更准确的写法
```

**关键**：数组作为参数时**退化为指针**，丢失了长度信息。必须额外传递大小。

```c
void print_array(int arr[], int n) {
    printf("sizeof(arr) = %zu\n", sizeof(arr));   // 输出 8（指针大小），不是数组大小！
}
```

### 多维数组参数

```c
// 必须指定除第一维外的所有维度
void process_matrix(int matrix[][10], int rows);

// 等价写法
void process_matrix(int (*matrix)[10], int rows);   // matrix 是指向 int[10] 的指针
```

## 返回值

### 返回基本类型

```c
int max(int a, int b) {
    return (a > b) ? a : b;
}
```

### 返回指针的危险

```c
// 致命错误！
int *create_array(void) {
    int arr[10];           // 局部变量，在栈上分配
    for (int i = 0; i < 10; i++) {
        arr[i] = i;
    }
    return arr;            // 返回局部变量的地址！函数返回后 arr 已失效
}

// 正确做法：使用动态内存
int *create_array_safe(void) {
    int *arr = malloc(sizeof(int) * 10);
    for (int i = 0; i < 10; i++) {
        arr[i] = i;
    }
    return arr;            // 堆内存不会随函数返回而释放
}
```

### 返回结构体

```c
struct Point create_point(int x, int y) {
    struct Point p = {x, y};
    return p;   // 复制整个结构体返回，小结构体效率可接受
}

// 大结构体用指针返回更高效
void create_point_ptr(int x, int y, struct Point *p) {
    p->x = x;
    p->y = y;
}
```

## 递归函数

### 阶乘

```c
unsigned long long factorial(int n) {
    if (n <= 1) return 1;           // 基准情况
    return n * factorial(n - 1);      // 递归情况
}
```

### 尾递归优化

```c
// 普通递归，栈深度 O(n)
int factorial(int n) {
    if (n <= 1) return 1;
    return n * factorial(n - 1);   // 乘法在递归调用之后，不是尾递归
}

// 尾递归形式，编译器可能优化为循环
int factorial_tail(int n, int acc) {
    if (n <= 1) return acc;
    return factorial_tail(n - 1, n * acc);   // 最后操作是递归调用
}
```

**注意**：C标准不保证尾递归优化，依赖具体编译器实现。

### 递归的陷阱

```c
// 缺少基准情况 → 无限递归 → 栈溢出
void infinite(void) {
    infinite();
}

// 斐波那契的朴素递归，时间复杂度 O(2^n)
long long fib(int n) {
    if (n <= 1) return n;
    return fib(n - 1) + fib(n - 2);   // 大量重复计算
}
```

## 变参函数

```c
#include <stdarg.h>

// 计算平均值
double average(int count, ...) {
    va_list args;
    va_start(args, count);

    double sum = 0;
    for (int i = 0; i < count; i++) {
        sum += va_arg(args, double);   // 提取 double 类型参数
    }

    va_end(args);
    return sum / count;
}

// 调用
average(3, 1.0, 2.0, 3.0);   // 注意：变参部分会发生默认参数提升
```

**陷阱**：
- `char`、`short`、`float` 会被提升为 `int`、`double`
- 没有类型检查，传入错误类型导致未定义行为
- 必须有一个方式知道参数数量和类型（如 `printf` 的格式字符串）

## 内联函数

```c
inline int max(int a, int b) {
    return (a > b) ? a : b;
}
```

**`inline` 的含义**：建议编译器将函数体直接插入调用处，减少函数调用开销。

**注意**：
- `inline` 只是建议，编译器可能忽略
- 内联函数的定义通常放在头文件中（因为每个翻译单元都需要看到定义）
- 现代编译器通常自动内联小函数，手动添加 `inline` 并非必要

## 函数指针基础

```c
int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }

// 声明函数指针
int (*op)(int, int);

op = add;
int result = op(3, 4);   // 调用 add(3, 4)，result = 7

op = sub;
result = op(3, 4);        // 调用 sub(3, 4)，result = -1
```

**函数指针的语法**：`返回类型 (*指针名)(参数列表)`

## 常见错误

### 1. 声明与定义不匹配

```c
// 文件1.c
int func(int x);   // 声明接受 int

// 文件2.c
int func(double x) {   // 定义接受 double
    return (int)x;
}

// 链接时可能不报错，但运行时参数传递错误！
```

### 2. 忽略返回值

```c
scanf("%d", &x);   // 忽略返回值，如果输入错误无法检测

// 正确做法
if (scanf("%d", &x) != 1) {
    printf("输入错误\n");
}
```

### 3. 递归没有基准情况

### 4. 栈溢出

```c
void deep_recursion(int n) {
    char buffer[1024];   // 大局部数组
    deep_recursion(n - 1);  // 每次递归消耗 1KB 栈空间
}
// 默认栈大小通常 1MB~8MB，递归过深会溢出
```

## 学习要点总结

1. C语言所有参数都是值传递，修改外部变量需要传指针
2. 数组作为参数退化为指针，必须额外传递大小
3. 不要返回局部变量的地址，需要持久数据用 malloc 或 static
4. 递归必须有基准情况，注意栈溢出风险
5. 变参函数没有类型安全，printf 的格式字符串必须与参数匹配
