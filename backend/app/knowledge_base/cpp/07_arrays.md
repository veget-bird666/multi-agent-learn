# C++ 数组与 std::array / vector

## 数组的本质

数组是**相同类型元素的连续内存块**。C++ 继承了 C 的数组语法，但提供了 `std::array` 和 `std::vector` 作为更安全、更现代的替代。理解数组在内存中的布局和**退化（decay）**规则，是掌握指针、迭代器和 STL 的基础。

### 内存布局

```cpp
int arr[5] = {1, 2, 3, 4, 5};
```

```
地址:  低 ──────────────────────────────→ 高
       ┌───┬───┬───┬───┬───┐
arr:   │ 1 │ 2 │ 3 │ 4 │ 5 │
       └───┴───┴───┴───┴───┘
       ↑
     arr[0] 的地址 = arr 的值（在大多数表达式中）
```

**关键**：元素在内存中**连续**存储，`arr[i]` 等价于 `*(arr + i)`（指针算术以 `sizeof(int)` 为单位）。

## C 风格数组

```cpp
int arr[5] = {1, 2, 3, 4, 5};
int zeros[10] = {};          // 全部初始化为 0（值初始化）
int matrix[2][3] = {{1, 2, 3}, {4, 5, 6}};
```

**特点**：
- 大小在**编译期**确定（VLA 可变长数组**不是** C++ 标准）
- 数组名在大多数表达式中**退化为指向首元素的指针**
- **不记录长度**，必须手动维护或传参时额外传递

```cpp
int arr[] = {1, 2, 3};   // 大小由初始化器推导为 3
std::size_t n = sizeof(arr) / sizeof(arr[0]);  // 3，仅当 arr 是数组名时有效
```

### 数组名退化的三个例外

```cpp
int arr[5] = {1, 2, 3, 4, 5};

int *p = arr;              // 退化：arr → &arr[0]

sizeof(arr);               // 例外1：20（整个数组，5×4）
int (*pa)[5] = &arr;       // 例外2：指向整个数组的指针
char str[] = "Hello";      // 例外3：字符串字面量初始化，复制内容到数组
```

**原因**：函数参数、指针算术等场景需要指针；`sizeof` 和 `&` 需要保留数组类型信息。

## 数组作为函数参数

```cpp
void print(int arr[], int n) {   // 等价于 void print(int* arr, int n)
    for (int i = 0; i < n; ++i) {
        std::cout << arr[i] << " ";
    }
}

// 多维数组必须指定除第一维外的所有维度
void print_matrix(int mat[][3], int rows) {  // 等价于 int (*mat)[3]
    for (int i = 0; i < rows; ++i) {
        for (int j = 0; j < 3; ++j) {
            std::cout << mat[i][j] << " ";
        }
    }
}
```

**与 C 完全相同**：数组参数**退化为指针**，函数内 `sizeof(arr)` 是指针大小（通常 8），不是数组大小。

```
调用 print(arr, 5):
  arr（数组名）→ 退化为 int*，仅传递首地址
  长度信息丢失！必须显式传 n
```

**记忆口诀**（与 C 相同）：
- `int *p[10]`：指针数组（10 个 `int*`）
- `int (*p)[10]`：数组指针（指向 `int[10]`）

## std::array（C++11，固定大小推荐）

```cpp
#include <array>

std::array<int, 5> arr = {1, 2, 3, 4, 5};

arr.size();          // 5，编译期常量
arr.at(2);           // 带边界检查，越界抛 std::out_of_range
arr[2];              // 不检查，越界未定义行为
arr.front(); arr.back();
arr.data();          // 底层指针，与 C API 互操作
```

**优势**：
- **栈上分配**，无堆开销，无分配失败
- 大小是类型的一部分（`array<int,5>` ≠ `array<int,10>`）
- 支持迭代器、范围 for、STL 算法
- `size()` 始终可用，不会像 C 数组那样丢失长度

```cpp
for (const auto& x : arr) {
    std::cout << x << " ";
}

#include <algorithm>
std::sort(arr.begin(), arr.end());
```

**与 C 数组对比**：零开销抽象（无额外内存），语义更安全。

## std::vector（动态数组，最常用）

```cpp
#include <vector>

std::vector<int> v = {1, 2, 3, 4, 5};
std::vector<int> v2(10, 0);      // 10 个 0
std::vector<int> v3(v.begin(), v.end());  // 拷贝构造
```

### 内存模型

```
vector 对象（通常在栈上）:
  ┌─────────────┐
  │ ptr ────────┼──→ 堆上连续元素 [1][2][3][4][5]...
  │ size = 5    │
  │ capacity=8  │     （capacity ≥ size，预留空间减少 reallocate）
  └─────────────┘
```

**本质**：`vector` 是 RAII 包装：构造时分配（或空），析构时 `delete[]`，自动管理堆内存。C 需手动 `malloc`/`free`。

### 常用操作

```cpp
v.push_back(6);          // 尾部追加，均摊 O(1)
v.pop_back();            // 删除尾部 O(1)
v.size();                // 元素个数
v.capacity();            // 已分配容量
v.empty();
v.clear();               // 清空元素，不保证释放 capacity
v.reserve(100);          // 预分配，减少 reallocate
v.resize(20);            // 改变 size，新元素值初始化
v.shrink_to_fit();       // 请求释放多余 capacity（非强制）
```

### 访问元素

```cpp
v[0];                    // 不检查边界
v.at(0);                 // 带边界检查
v.front(); v.back();
```

**防御式编程**：对外部输入的下标用 `at()`；性能关键且已验证边界用 `[]`。

### 迭代器失效（重要）

```cpp
std::vector<int> v = {1, 2, 3};
auto it = v.begin();
v.push_back(4);   // 可能触发 reallocate，it 失效
// *it;           // 未定义行为！
```

**规则**：以下操作可能导致迭代器、指针、引用失效：
- `push_back`、`insert`（容量不足时 reallocate）
- `erase`、`clear`
- `resize`、`reserve`（可能 reallocate）

**原因**：reallocate 在新堆块复制元素，释放旧块，旧指针/迭代器指向已释放内存。

## 数组 vs std::array vs std::vector

| 特性 | C 数组 | std::array | std::vector |
|:---|:---|:---|:---|
| 大小 | 编译期固定 | 编译期固定 | 运行时可变 |
| 存储 | 栈/静态 | 通常栈 | 堆（对象本身可在栈） |
| 边界检查 | 无 | `at()` 有 | `at()` 有 |
| 知悉长度 | 易丢失 | `size()` | `size()` |
| 与 C 互操作 | 原生 | `data()` | `data()` |
| 迭代器 | 指针 | 有 | 有 |
| 推荐度 | 避免 | 固定大小首选 | 动态大小首选 |

## 初始化列表（C++11）

```cpp
std::vector<int> v{1, 2, 3};
std::array<std::string, 2> names{"Alice", "Bob"};

void print(std::initializer_list<int> list) {
    for (int x : list) std::cout << x << " ";
}
print({1, 2, 3, 4});
```

**陷阱**：

```cpp
std::vector<int> v1(10, 0);    // 10 个 0
std::vector<int> v2{10, 0};    // 两个元素：10 和 0！
```

**原因**：`{10, 0}` 匹配 `initializer_list` 构造函数，不是 `(count, value)`。

## 二维数组

### C 风格与 std::array

```cpp
int mat[2][3] = {{1,2,3}, {4,5,6}};   // 内存连续，行优先

std::array<std::array<int, 3>, 2> m = {{
    {1, 2, 3},
    {4, 5, 6}
}};
```

### vector of vector（动态二维）

```cpp
std::vector<std::vector<int>> matrix(3, std::vector<int>(4, 0));
// 3 行 4 列，全 0

matrix[1][2] = 42;
```

**注意**：`vector<vector<int>>` 各行**不一定**内存连续（每行独立堆块），与 C 二维数组/cache 友好性不同。高性能数值计算考虑一维 `vector` + 索引映射 `i * cols + j`。

## 算法配合

```cpp
#include <algorithm>

std::vector<int> v = {5, 2, 8, 1, 9};
std::sort(v.begin(), v.end());
auto it = std::find(v.begin(), v.end(), 8);
if (it != v.end()) {
    std::cout << "Found at index " << (it - v.begin()) << std::endl;
}
```

**C 对比**：C 无标准通用算法库；C++ STL 算法与迭代器配合，适用于 array/vector 等。

## 常见错误

### 1. 数组越界

```cpp
int arr[3] = {1, 2, 3};
arr[5] = 0;   // 未定义行为！可能破坏栈上其他数据
```

**原因**：C/C++ 不检查边界（除非 `at()`）。可能静默 corrupt 内存或崩溃。

### 2. 返回局部数组

```cpp
int* bad() {
    int arr[10] = {};
    return arr;   // 错误！局部数组在栈上，返回后失效
}

// 正确：vector 或 static（注意线程安全）
std::vector<int> good() {
    return {1, 2, 3};   // 移动/拷贝到调用方
}
```

### 3. 用 sizeof 计算传递后的数组长度

```cpp
void func(int arr[]) {
    // sizeof(arr)/sizeof(arr[0]) → 8/4 = 2（64位），不是数组长度！
}
```

### 4. vector 迭代器失效

见上文。在循环中 `push_back` 需重新获取迭代器或预留 `reserve`。

### 5. 混淆指针数组与数组指针

```cpp
char *names[] = {"Alice", "Bob"};     // 指针数组
int (*p)[3] = &matrix;                // 指向 int[3] 的指针
```

### 6. 范围 for 中修改 vector 结构

```cpp
for (auto& x : v) {
    v.push_back(0);   // 可能 reallocate，x 悬垂 → UB
}
```

## C++20 std::span（数组视图）

```cpp
#include <span>

void process(std::span<const int> data) {
    for (int x : data) std::cout << x << " ";
}

int arr[] = {1, 2, 3};
std::vector<int> v = {4, 5, 6};
process(arr);                    // 从 C 数组
process(v);                      // 从 vector
process({arr, 3});               // 显式 span
```

**优势**：统一 C 数组、`std::array`、`std::vector` 的传参接口，携带**指针 + 长度**，避免退化丢失大小。不拥有内存，仅"视图"。

**与 C 对比**：C 只能传 `(int* arr, size_t n)`；span 是类型安全的等价物。

## 多维数组的内存布局（行优先）

```cpp
int matrix[2][3] = {{1,2,3}, {4,5,6}};
```

```
内存连续（行优先 Row-Major）:
[1][2][3][4][5][6]
 ↑ row0    ↑ row1

matrix[1][2] 的地址 = base + (1×3 + 2) × sizeof(int)
```

**Cache 友好性**：按行遍历（内层循环走列）连续访问内存，比列优先快。`vector<vector<int>>` 各行可能不连续，数值计算常扁平存储。

## 防御式编程建议

1. **固定大小**：`std::array<T, N>` 替代 C 数组
2. **动态大小**：`std::vector<T>` 替代 `new[]`/`delete[]`
3. **传参**：传 `span`（C++20）或 `(pointer, size)` / `const vector&`
4. **边界**：对外部索引用 `at()`；编译期已知安全用 `[]`
5. **C API**：`vec.data()` 获取连续指针，确保 `vec.size()` 一并传递

## 学习要点总结

1. 固定大小优先 `std::array`，动态大小用 `std::vector`，避免裸 C 数组
2. 数组名在大多数情况退化为指针；函数参数无法自动获知长度
3. `vector` 修改结构（push_back/insert/erase）可能导致迭代器失效
4. 访问元素：调试/外部输入用 `at()`，性能关键且安全用 `[]`
5. 二维动态结构用 `vector<vector<T>>`；追求 cache 局部性考虑扁平一维存储
6. 不要返回局部 C 数组的指针；用 vector 或智能指针管理堆数组
7. 理解 `{10, 0}` 与 `(10, 0)` 对 vector 初始化的不同语义
