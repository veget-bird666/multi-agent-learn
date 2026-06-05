# C语言指针与数组进阶

## 数组名的本质

数组名在大多数表达式中会**退化为指向首元素的指针**，但有三个例外：

```c
int arr[5] = {1, 2, 3, 4, 5};

int *p = arr;           // arr 退化为 &arr[0]

// 例外1：sizeof(arr) 返回整个数组大小
printf("%zu\n", sizeof(arr));       // 20 (5 * 4)

// 例外2：&arr 得到整个数组的地址
int (*pa)[5] = &arr;    // pa 的类型是 int (*)[5]，指向整个数组

// 例外3：字符串字面量初始化字符数组
char str[] = "Hello";   // 不是退化，是复制内容
```

## 指针数组 vs 数组指针

### 指针数组（Array of Pointers）

```c
char *names[] = {
    "Alice",
    "Bob",
    "Charlie"
};
// names 的类型：char *[3]
// names[i] 是指向字符串的指针

printf("%s\n", names[1]);   // 输出 Bob
```

### 数组指针（Pointer to Array）

```c
int arr[3][4] = {
    {1, 2, 3, 4},
    {5, 6, 7, 8},
    {9, 10, 11, 12}
};

int (*p)[4] = arr;      // p 指向 int[4] 数组
// p + 1 跳过 4 个 int（16字节）

printf("%d\n", p[1][2]);    // 等价于 *(*(p + 1) + 2)，输出 7
```

**记忆口诀**：
- `int *p[10]`：先结合 `[10]`，是指针数组（10个 `int*`）
- `int (*p)[10]`：先结合 `*p`，是数组指针（指向 `int[10]`）

## 多维数组的内存布局

```c
int matrix[3][4];
```

内存中是**连续存储**的：

```
地址:  &matrix[0][0]  &matrix[0][1]  ...  &matrix[0][3]  &matrix[1][0]  ...
值:    [0][0]        [0][1]         ...  [0][3]        [1][0]         ...
```

因此可以线性遍历：

```c
int *p = &matrix[0][0];
for (int i = 0; i < 12; i++) {
    printf("%d ", p[i]);   // 输出所有元素
}
```

## 指针运算的深层理解

### 指针算术的单位

```c
int arr[5];
int *p = arr;

p + 1;      // 地址增加 sizeof(int) 字节，不是 1 字节！
p + n;      // 地址增加 n * sizeof(int) 字节
```

**为什么这样设计？**

因为指针算术的语义是"移动到第 n 个元素"，而不是"移动 n 字节"。这让代码与类型无关：

```c
void *p = arr;
// p + 1;   // 错误！void* 不知道元素大小

char *cp = (char *)arr;
cp + 1;     // 正确，移动 1 字节
```

### 指针相减

```c
int arr[10];
int *p1 = &arr[3];
int *p2 = &arr[7];

ptrdiff_t diff = p2 - p1;   // 4，表示相隔 4 个元素
```

**注意**：
- 只有指向同一数组的指针才能相减
- 结果是 `ptrdiff_t` 类型（有符号，因为可能为负）
- 结果单位是"元素个数"，不是字节

### 指针比较

```c
int arr[10];
int *p1 = &arr[3];
int *p2 = &arr[7];

if (p1 < p2) { }   // 合法，比较的是数组中的位置
```

只有指向同一数组（或数组末尾后一个位置）的指针才能比较。

## 数组参数传递

### 一维数组

```c
// 以下三种声明完全等价
void func(int arr[]);
void func(int arr[10]);   // 10 被忽略
void func(int *arr);       // 最准确的写法

// 调用
int a[10];
func(a);   // 数组退化为指针
```

### 二维数组

```c
// 必须指定除第一维外的所有维度
void func(int matrix[][10]);
void func(int (*matrix)[10]);   // 等价写法，更明确

// 调用
int m[5][10];
func(m);
```

**为什么不能只传 `int **matrix`？**

```c
void func(int **matrix);   // 这是指针的指针，不是二维数组！

int m[5][10];
func(m);   // 编译错误！类型不匹配

int *rows[5];   // 指针数组
for (int i = 0; i < 5; i++) {
    rows[i] = m[i];   // 每行是一个 int*
}
func(rows);   // 合法，因为 rows 是 int**
```

## 函数指针数组

```c
int add(int a, int b) { return a + b; }
int sub(int a, int b) { return a - b; }
int mul(int a, int b) { return a * b; }
int div(int a, int b) { return a / b; }

// 函数指针数组
int (*operations[])(int, int) = {add, sub, mul, div};

// 使用
int result = operations[2](4, 5);   // 调用 mul(4, 5)，result = 20
```

**应用场景**：状态机、命令分发、策略模式。

## 复杂声明解读

### 右左法则（The Right-Left Rule）

解读复杂声明的步骤：
1. 找到标识符
2. 向右看，遇到 `)` 停止
3. 向左看，遇到 `(` 停止
4. 重复 2-3，直到解析完毕

```c
int (*(*func_array[10])(int))[5];
```

解析：
1. `func_array` —— 标识符
2. `[10]` —— `func_array` 是大小为 10 的数组
3. `*` —— 数组元素是指针
4. `(int)` —— 指针指向接受 `int` 参数的函数
5. `*` —— 函数返回指针
6. `[5]` —— 指针指向大小为 5 的数组
7. `int` —— 数组元素是 `int`

**结论**：`func_array` 是包含 10 个元素的数组，每个元素是指向"接受 `int` 参数并返回指向 `int[5]` 的指针"的函数的指针。

### typedef 简化

```c
typedef int (*FuncPtr)(int);
FuncPtr func_array[10];   // 清晰多了
```

## 常见错误

### 1. 数组越界

```c
int arr[5] = {1, 2, 3, 4, 5};
int *p = arr + 5;   // p 指向 arr[5]，这是允许的（末尾后一个位置）
int x = *p;         // 未定义行为！不能解引用
```

### 2. 指针类型不匹配

```c
int arr[5];
short *sp = (short *)arr;
sp[1] = 0x1234;     // 破坏内存对齐，未定义行为
```

### 3. 混淆指针数组和二维数组

```c
char *names[] = {"Alice", "Bob"};   // 指针数组
char names2[][10] = {"Alice", "Bob"}; // 二维字符数组

sizeof(names);     // 指针数组总大小（如 16 字节）
sizeof(names2);    // 20 字节（2 * 10）
```

## 学习要点总结

1. 数组名在表达式中退化为指针，但 `sizeof`、取地址、字符串初始化时例外
2. `int *p[10]` 是指针数组，`int (*p)[10]` 是数组指针
3. 多维数组在内存中是连续存储的，可以线性遍历
4. 指针算术的单位是"元素大小"，不是字节
5. 二维数组参数必须指定除第一维外的所有维度
