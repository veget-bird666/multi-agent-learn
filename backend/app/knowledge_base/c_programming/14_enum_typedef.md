# C语言枚举与typedef

## 枚举（enum）

### 基本用法

```c
enum Color {
    RED,      // 0
    GREEN,    // 1
    BLUE      // 2
};

enum Color c = RED;
if (c == RED) {
    printf("红色\n");
}
```

### 显式赋值

```c
enum Status {
    OK = 200,
    NOT_FOUND = 404,
    ERROR = 500
};

// 未指定值的成员 = 前一个值 + 1
enum Priority {
    LOW = 1,
    MEDIUM,     // 2
    HIGH        // 3
};
```

### 枚举的本质

C语言的枚举在底层就是**整数**：

```c
enum Color c = RED;
printf("%d\n", c);   // 输出 0

// 甚至可以这样（不推荐）
c = 5;   // 合法！枚举变量可以赋任意整数值
```

**C 与 C++ 的区别**：
- C：枚举就是 `int`，可以赋任意整数值
- C++：枚举是强类型，不能直接赋整数

### 枚举的大小

```c
printf("%zu\n", sizeof(enum Color));   // 通常是 4（int 的大小）
```

C11 起可以用 `_Bool`、`_Complex` 等，但枚举通常仍是 `int`。

### 枚举的命名冲突

```c
enum Color { RED, GREEN, BLUE };
enum Fruit { APPLE, ORANGE, RED };   // 错误！RED 已定义
```

枚举常量位于**全局命名空间**，不同枚举不能有同名常量。

**解决**：使用前缀命名约定

```c
enum Color { COLOR_RED, COLOR_GREEN, COLOR_BLUE };
enum Fruit { FRUIT_APPLE, FRUIT_ORANGE, FRUIT_BANANA };
```

### 枚举作为 switch case

```c
enum Color c = GREEN;
switch (c) {
    case RED:   printf("红\n"); break;
    case GREEN: printf("绿\n"); break;
    case BLUE:  printf("蓝\n"); break;
    default:    printf("未知\n");
}
```

**优势**：编译器可以检查是否遗漏 case（带 `-Wswitch` 警告）。

## typedef

### 基本用法

```c
typedef unsigned int uint;       // uint 是 unsigned int 的别名
typedef unsigned char byte;      // byte 是 unsigned char 的别名

uint a = 10;
byte b = 0xFF;
```

### 简化复杂声明

```c
// 函数指针类型
int (*signal(int sig, int (*func)(int)))(int);
// 这个声明太复杂了！

// 用 typedef 分解
typedef void (*sighandler_t)(int);
sighandler_t signal(int sig, sighandler_t handler);
// 清晰多了！
```

### typedef vs #define

```c
#define BYTE unsigned char      // 预处理器文本替换
typedef unsigned char Byte;     // 类型别名

// 关键区别
typedef char *String;
String s1, s2;   // s1 和 s2 都是 char*

#define STRING char *
STRING s3, s4;   // s3 是 char*，s4 是 char！（宏替换为 char *s3, s4）
```

**原则**：类型别名用 `typedef`，简单常量用 `#define`。

### typedef 与结构体

```c
// 方式1：先定义结构体，再 typedef
typedef struct Point {
    int x;
    int y;
} Point;

// 方式2：匿名结构体 + typedef
typedef struct {
    int x;
    int y;
} Point2;

Point p1;    // 不需要 struct 关键字
Point2 p2;
```

**注意**：方式2不能自引用（结构体内部不能用 `Point2`）。

### typedef 与指针

```c
typedef int *IntPtr;
typedef int IntArray[10];

IntPtr p;        // int *p
IntArray arr;    // int arr[10]

// 注意
const IntPtr p2;     // int *const p2（p2 是常量指针）
const int *p3;       // p3 指向常量 int
```

## 常见组合用法

### 回调函数类型

```c
typedef int (*CompareFunc)(const void *, const void *);

void sort(void *arr, size_t n, size_t size, CompareFunc cmp);

// 使用
int compare_int(const void *a, const void *b) {
    return (*(int *)a - *(int *)b);
}

sort(arr, n, sizeof(int), compare_int);
```

### 状态机状态类型

```c
typedef enum {
    STATE_IDLE,
    STATE_RUNNING,
    STATE_PAUSED,
    STATE_STOPPED
} State;

typedef void (*StateHandler)(void);

typedef struct {
    State state;
    StateHandler handler;
} StateTransition;
```

## 常见错误

### 1. 枚举与整数混淆

```c
enum Color c = 5;   // 合法但危险，5 不是有效的枚举值

// 防御性检查
if (c < RED || c > BLUE) {
    printf("无效的枚举值\n");
}
```

### 2. typedef 重复定义

```c
typedef int MyInt;
typedef int MyInt;   // 错误！重复定义

// 但可以用条件编译
#ifndef MYINT_DEFINED
typedef int MyInt;
#define MYINT_DEFINED
#endif
```

### 3. 隐藏指针

```c
typedef char *String;
String s = malloc(100);
free(s);   // 看起来没问题

// 但如果
String s1, s2;
s1 = malloc(100);
s2 = s1;
free(s1);
// s2 现在是野指针，但类型隐藏了这一点
```

**建议**：不要 typedef 指针类型，保持 `*` 可见。

## 学习要点总结

1. 枚举在C中本质是 `int`，可以赋任意整数值，没有类型安全
2. 枚举常量位于全局命名空间，不同枚举避免同名
3. `typedef` 是类型别名，`#define` 是文本替换，复杂类型优先用 typedef
4. 不要 typedef 指针类型，保持 `*` 可见以避免混淆
5. typedef 函数指针类型可以大幅简化复杂声明
