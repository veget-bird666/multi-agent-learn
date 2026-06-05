# C语言结构体与联合体

## 结构体基础

### 声明与定义

```c
// 声明结构体类型
struct Point {
    int x;
    int y;
};

// 定义变量
struct Point p1;           // 必须带 struct 关键字
struct Point p2 = {10, 20}; // 初始化

// 声明时同时定义变量（C11 前常用）
struct Point {
    int x;
    int y;
} p3, p4;

// 匿名结构体（C11）
struct {
    int x;
    int y;
} p5;   // p5 是唯一的变量，没有类型名
```

### typedef 简化

```c
typedef struct Point {
    int x;
    int y;
} Point;   // Point 是 struct Point 的别名

Point p1;   // 不需要 struct 关键字
```

**注意**：在结构体内部使用自身时，必须用 `struct`：

```c
typedef struct Node {
    int data;
    struct Node *next;   // 不能用 Node *next，此时 typedef 还未完成
} Node;
```

## 结构体内存布局

### 内存对齐

```c
struct Example {
    char a;      // 1字节
    int b;       // 4字节
    char c;      // 1字节
};

printf("%zu\n", sizeof(struct Example));   // 输出 12，不是 6！
```

**内存布局**：

```
地址偏移:  0    1    2    3    4    5    6    7    8    9   10   11
内容:     [ a ][pad][pad][pad][  b  ][  b  ][  b  ][  b  ][ c ][pad][pad][pad]
```

**对齐规则**：
1. 结构体成员的偏移必须是其类型大小的整数倍
2. 结构体总大小必须是最大成员大小的整数倍
3. `char` 对齐到 1，`short` 到 2，`int`/`float` 到 4，`double`/`long long`/`指针` 到 8（64位）

### 手动控制对齐

```c
// 使用 #pragma pack（编译器相关）
#pragma pack(push, 1)   // 按 1 字节对齐
struct Packed {
    char a;
    int b;
    char c;
};
#pragma pack(pop)

printf("%zu\n", sizeof(struct Packed));   // 输出 6

// C11 标准方式
#include <stdalign.h>
struct Aligned {
    alignas(16) char data[64];   // 16 字节对齐
};
```

**注意**：过度压缩对齐会降低访问速度，某些平台（ARM）未对齐访问会崩溃。

### 结构体成员偏移

```c
#include <stddef.h>

struct Person {
    char name[20];
    int age;
    double salary;
};

printf("name offset: %zu\n", offsetof(struct Person, name));     // 0
printf("age offset: %zu\n", offsetof(struct Person, age));       // 20
printf("salary offset: %zu\n", offsetof(struct Person, salary)); // 24
```

## 结构体与指针

### 箭头运算符

```c
struct Point p = {10, 20};
struct Point *ptr = &p;

(*ptr).x = 30;     // 解引用后访问成员
ptr->x = 30;       // 等价，更简洁
```

### 自引用结构体

```c
struct Node {
    int data;
    struct Node *next;   // 不能是 struct Node next（无限递归）
};
```

### 结构体指针的陷阱

```c
struct Point *p = NULL;
p->x = 10;   // 段错误！解引用空指针

// 安全做法
if (p != NULL) {
    p->x = 10;
}
```

## 结构体与函数

### 传值 vs 传指针

```c
// 传值：复制整个结构体
void move_point(struct Point p, int dx, int dy) {
    p.x += dx;   // 只修改副本
}

// 传指针：修改原结构体
void move_point_ptr(struct Point *p, int dx, int dy) {
    p->x += dx;   // 修改原结构体
}

// 传 const 指针：只读访问
void print_point(const struct Point *p) {
    printf("(%d, %d)\n", p->x, p->y);
    // p->x = 10;   // 编译错误！
}
```

**选择建议**：
- 小结构体（如 Point，16字节）：传值或传指针均可
- 大结构体：始终传指针，避免复制开销
- 不需要修改：传 `const` 指针

### 返回结构体

```c
struct Point create_point(int x, int y) {
    struct Point p = {x, y};
    return p;   // 复制返回，小结构体可接受
}

// 大结构体用指针参数返回
void create_point_ptr(int x, int y, struct Point *p) {
    p->x = x;
    p->y = y;
}
```

## 联合体（Union）

### 基本用法

```c
union Data {
    int i;
    float f;
    char str[20];
};

union Data d;
d.i = 10;       // 使用整数成员
d.f = 3.14;     // 现在使用浮点成员，i 的值被破坏
```

**特点**：
- 所有成员共享同一块内存
- 大小等于最大成员的大小
- 同时只能有效使用一个成员

### 内存布局

```c
union Data {
    int i;       // 4字节
    float f;     // 4字节
    char c;      // 1字节
};

printf("%zu\n", sizeof(union Data));   // 4（最大成员 int/float 的大小）
```

### 类型双关（Type Punning）

```c
union Converter {
    float f;
    int i;
};

union Converter c;
c.f = 3.14f;
printf("0x%08X\n", c.i);   // 查看浮点数的二进制表示
```

**注意**：C99 起通过联合体进行类型双关是合法的（严格别名规则的例外）。

### 联合体的应用场景

```c
// 变体类型（Tagged Union）
struct Variant {
    enum { INT, FLOAT, STRING } type;
    union {
        int i;
        float f;
        char *s;
    } value;
};

void print_variant(struct Variant *v) {
    switch (v->type) {
        case INT:    printf("%d\n", v->value.i); break;
        case FLOAT:  printf("%f\n", v->value.f); break;
        case STRING: printf("%s\n", v->value.s); break;
    }
}
```

## 位域（Bit Fields）

### 基本语法

```c
struct Flags {
    unsigned int flag1 : 1;   // 1 位
    unsigned int flag2 : 1;   // 1 位
    unsigned int flag3 : 1;   // 1 位
    unsigned int value : 5;   // 5 位（0-31）
    unsigned int : 2;         // 2 位填充（无名位域）
};

printf("%zu\n", sizeof(struct Flags));   // 通常 4 字节（一个 int）
```

### 位域的应用

```c
// 网络协议头（如 IP 头）
struct IPHeader {
    unsigned int version : 4;      // IP 版本
    unsigned int ihl : 4;          // 头部长度
    unsigned int tos : 8;          // 服务类型
    unsigned int total_length : 16; // 总长度
    // ...
};
```

**注意事项**：
- 位域必须是整数类型
- 不能取位域的地址（`&flags.flag1` 非法）
- 位域布局依赖实现（大端/小端、分配方向）
- 无名位域用于填充对齐

## 结构体数组

```c
struct Student {
    char name[20];
    int score;
};

struct Student class[30] = {
    {"Alice", 90},
    {"Bob", 85},
    {"Charlie", 95}
};

// 访问
class[0].score = 95;
strcpy(class[1].name, "Robert");
```

## 嵌套结构体

```c
struct Date {
    int year;
    int month;
    int day;
};

struct Person {
    char name[20];
    struct Date birthday;   // 嵌套结构体
};

struct Person p = {"Alice", {1990, 5, 15}};
printf("%d\n", p.birthday.year);   // 1990
```

## 常见错误

### 1. 结构体赋值 vs 比较

```c
struct Point p1 = {1, 2};
struct Point p2 = {1, 2};

if (p1 == p2) { }      // 错误！结构体不能用 == 比较

// 正确做法：逐成员比较或 memcmp
if (p1.x == p2.x && p1.y == p2.y) { }
```

### 2. 结构体中的柔性数组成员位置错误

```c
// 错误！柔性数组必须是最后一个成员
struct Bad {
    char data[];   // 柔性数组
    int count;     // 错误！后面还有成员
};

// 正确
struct Good {
    int count;
    char data[];   // 必须是最后一个成员
};
```

### 3. 未初始化的结构体指针

```c
struct Point *p;
p->x = 10;   // 野指针！未初始化

// 正确
struct Point *p = malloc(sizeof(struct Point));
if (p != NULL) {
    p->x = 10;
}
```

### 4. 联合体成员混淆

```c
union Data d;
d.i = 10;
printf("%f\n", d.f);   // 读取未初始化的成员，未定义行为！
```

## 学习要点总结

1. 结构体成员按对齐规则排列，总大小是最大成员大小的整数倍
2. 大结构体传参用指针，小结构体可传值；只读访问用 const 指针
3. 联合体所有成员共享内存，同时只能有效使用一个成员
4. 位域用于紧凑存储标志位，布局依赖实现，不能取地址
5. 结构体不能用 == 比较，需要逐成员比较或 memcmp
