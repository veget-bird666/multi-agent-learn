# C++ 指针与引用

## 指针的本质

### 什么是指针

指针是**存储内存地址的变量**。每个对象在内存中有唯一地址，指针保存该地址，通过解引用访问目标对象。

```cpp
int x = 42;
int* p = &x;        // p 保存 x 的地址
std::cout << *p;    // 42，解引用
*p = 100;           // 通过指针修改 x
```

### 内存模型

```
地址         内容
0x1000  →   [ 42 ]     ← int x
0x2000  →   [0x1000]   ← int* p（存的是 x 的地址）

*p 的含义：取 p 的值（0x1000），访问该地址处的 int → 42
```

**深层理解**：
- 指针本身也占内存（64 位系统通常 8 字节）
- 指针有**类型**：`int*` 与 `char*` 步长不同（指针算术单位是 `sizeof(T)`）
- 未初始化的指针是**野指针**，解引用是未定义行为

## C vs C++ 指针对比

| 特性 | C | C++ |
|:---|:---|:---|
| 空指针 | `NULL`（可能是 `#define 0`） | `nullptr`（类型安全） |
| void* | 隐式转任意指针 | 需 `static_cast` |
| 内存释放 | `free` | `delete` / 智能指针 |
| 引用 | 无 | 有 `T&` |
| 默认初始化 | 不初始化（危险） | 仍不初始化，但可用 `{}` 或智能指针 |
| 推荐实践 | 初始化 + 配对 free | 智能指针 + 引用传参 |

```c
// C：NULL 可能导致重载歧义（若在 C++ 中）
void f(int);
void f(int*);
f(NULL);   // 可能调用 f(int)！
```

```cpp
// C++：nullptr 类型明确
void g(int*);
g(nullptr);   // 一定调用 g(int*)
```

## nullptr（C++11）

```cpp
int* p = nullptr;   // 类型为 std::nullptr_t

if (p == nullptr) { /* 空 */ }
if (p) { /* 非空 */ }

// 不要再用 NULL 或 0 表示空指针
```

**原因**：`NULL` 在 C++ 中常被定义为 `0` 或 `(void*)0`，参与重载解析时可能匹配 `int` 参数而非指针参数。

## 指针与 const

```cpp
int x = 10, y = 20;

const int* p1 = &x;       // 指向常量的指针：不能通过 p1 修改 *p1
int* const p2 = &x;       // 常量指针：p2 不能改指向
const int* const p3 = &x; // 两者都 const

p1 = &y;      // OK，p1 可改指向
// *p1 = 5;   // 错误
// p2 = &y;   // 错误
// *p2 = 5;   // OK
```

**记忆口诀**：`const` 在 `*` **左边**修饰**指向的内容**；在 `*` **右边**修饰**指针本身**。

**防御性编程**：只读访问用 `const T*` 或 `const T&`，防止误修改：

```cpp
void print(const std::string* ps) {
    // ps->clear();   // 编译错误
    std::cout << *ps;
}
```

## 引用的本质

引用是对象的**别名（alias）**，不是新对象，不占用额外存储（实现上可能是指针的语法糖）。

```cpp
int x = 42;
int& ref = x;     // ref 就是 x 的另一个名字
ref = 100;        // x 变为 100

int& r1 = x;      // OK
// int& r2;       // 错误！引用必须初始化
// int& r3 = 10;  // 错误！不能绑定非 const 引用到临时量
```

### 引用 vs 指针

| 特性 | 指针 `T*` | 引用 `T&` |
|:---|:---|:---|
| 可否为空 | 可以（`nullptr`） | 不可以，必须绑定有效对象 |
| 可否重新绑定 | 可以 | 不可以 |
| 语法 | 需 `*p` 解引用 | 直接使用，像原变量 |
| sizeof | 指针大小（8 字节） | 不单独占空间 |
| 算术运算 | 支持 | 不支持 |
| 典型用途 | 可选、动态内存、数组 | 函数参数、返回值 |

**深层理解**：
- 引用必须在定义时初始化，且之后不能改绑到其他对象
- `const T&` 可以绑定临时量（延长临时对象生命周期到引用所在作用域）
- 编译器可能用指针实现引用，但对程序员语义是"别名"

```cpp
const int& cr = 42;   // OK：临时 int(42) 的生命周期延长到 cr 的作用域
```

## 引用作为函数参数

```cpp
void swap(int& a, int& b) {
    std::swap(a, b);   // 直接修改实参，等价于 C 的指针传参但语法更简洁
}

void print(const std::string& s) {   // 无拷贝，只读
    std::cout << s << std::endl;
}
```

### C 传指针 vs C++ 传引用

```c
// C：需显式取地址，函数内解引用
void increment(int *p) {
    if (p != NULL) (*p)++;
}
increment(&x);
```

```cpp
// C++：语法自然，不能为空（除非用指针）
void increment(int& n) { ++n; }
increment(x);
```

**现代 C++ 建议**：
- 必选、不可为空 → `T&` 或 `const T&`
- 可选、可为空 → `T*` 或 `std::optional<T&>`（C++17 无直接 optional 引用，常用指针）
- 不修改 → `const T&`

## 引用作为返回值

```cpp
int& get_element(std::vector<int>& v, size_t i) {
    return v.at(i);   // 返回 vector 内元素的引用
}

std::vector<int> vec = {1, 2, 3};
get_element(vec, 0) = 99;   // vec[0] == 99
```

### 生命周期陷阱

```cpp
int& bad() {
    int x = 10;
    return x;   // 未定义行为！返回栈上局部变量的引用
}

std::string& bad2() {
    return std::string("temp");   // 临时对象销毁，引用悬空
}
```

**生命周期图**：

```
栈帧 func():
  x [10]  ←── ref 绑定
  ↓ 函数返回，x 销毁
  ref 悬空 → 任何使用都是 UB
```

**防御性编程**：返回引用时，确保被引用对象的生命周期长于引用使用期（如容器元素、成员变量、静态存储）。

## 指针算术与数组

```cpp
int arr[] = {10, 20, 30, 40};
int* p = arr;       // arr 在大多数表达式中退化为 int*

*(p + 1);           // 20
p++;                // 指向下一个 int（地址 +4，假设 int 为 4 字节）
p - arr;            // 偏移元素个数

arr[2];             // 等价于 *(arr + 2)
```

**重要区别**：

```cpp
sizeof(arr);   // 整个数组大小（如 5*4=20）
sizeof(p);     // 指针大小（8）
```

**注意**：指针算术仅在**同一数组对象**内有意义，跨数组的指针比较/运算是未定义行为。

## 指针与数组（C 兼容性）

```cpp
// 以下等价
arr[i];
*(arr + i);
*(p + i);
p[i];
```

C++ 中更推荐 `std::array` 或 `std::vector` 替代 C 风格数组，但理解指针-数组关系对读 C 代码和底层逻辑至关重要。

## 多级指针

```cpp
int x = 10;
int* p = &x;
int** pp = &p;

**pp = 20;   // x = 20
```

**典型用途**：动态二维数组、C 风格字符串数组、某些 C API。

```cpp
char* names[] = {"Alice", "Bob"};   // 指针数组
char (*matrix)[10];                  // 指向数组的指针
```

## 智能指针预览

原始指针需手动 `delete`，异常路径易泄漏。现代 C++ 用 RAII 智能指针（详见内存管理章节）：

```cpp
#include <memory>

auto p = std::make_unique<int>(42);     // 独占所有权
auto sp = std::make_shared<int>(42);    // 共享所有权

// 裸指针仅作"非拥有观察者"
void observe(const Widget* w);   // 不 delete，不拥有
```

**所有权语义图**：

```
unique_ptr:  [owner] ──→ [heap object]
             move 后原 owner 为空

shared_ptr:  [owner1] ──┐
             [owner2] ──┼──→ [heap object] (refcount=2)
             最后一个销毁时 delete
```

## void* 与类型转换

```cpp
int x = 42;
void* vp = &x;                          // 擦除类型
int* p2 = static_cast<int*>(vp);        // 转回原类型

// C 风格 cast 不推荐
// int* p3 = (int*)vp;
```

**C vs C++**：
- C 允许 `void*` 隐式赋值给任意 `T*`
- C++ 不允许，必须显式 `static_cast`

**dynamic_cast** 用于多态类型的安全向下转型（见继承章节），失败时指针版返回 `nullptr`。

## 函数指针

```cpp
int add(int a, int b) { return a + b; }

int (*func_ptr)(int, int) = add;
int result = func_ptr(3, 4);   // 7

// C++11 推荐 std::function 或 lambda
#include <functional>
std::function<int(int,int)> f = add;
auto g = [](int a, int b) { return a + b; };
```

## 常见错误

### 1. 野指针

```cpp
int* p;
*p = 10;
// 原因：p 未初始化，指向随机地址
// 修复：int* p = nullptr; 或立即赋有效地址
```

### 2. 悬空指针（Dangling Pointer）

```cpp
int* p = new int(5);
delete p;
// *p = 10;   // 未定义行为
// 原因：delete 后对象已销毁
// 修复：delete 后置 p = nullptr；更好的做法是用 unique_ptr
```

### 3. 返回局部变量地址/引用

```cpp
int* get() {
    int x = 10;
    return &x;   // UB：栈变量已销毁
}
// 原因：函数返回后栈帧销毁
```

### 4. 双重释放

```cpp
delete p;
delete p;   // 未定义行为，可能破坏堆结构
// 原因：同一块内存释放两次
// 修复：delete 后 p = nullptr；delete nullptr 安全
```

### 5. 混淆引用与指针语法

```cpp
int x = 10;
int& r = x;
// *r = 20;   // 错误！引用无需解引用
r = 20;       // 正确
```

### 6. 指针算术越界

```cpp
int arr[5] = {1,2,3,4,5};
int* p = arr + 10;   // 越界指针，即使不解引用也可能是 UB
// 原因：指针必须在数组对象范围内（或 one-past-end）
```

### 7. 用 == 比较 C 字符串

```cpp
const char* a = "hi";
const char* b = "hi";
a == b;   // 可能 false！比较的是地址，不是内容
// C++ 中字符串内容比较用 std::string 或 strcmp
```

## 防御性编程模式

### 1. 初始化指针

```cpp
int* p = nullptr;   // 默认初始化为空，而非野指针
```

### 2. 优先引用传递

```cpp
void process(const std::string& s);   // 而非 void process(std::string s) 若不需拷贝
```

### 3. 所有权明确

```cpp
// 拥有 → unique_ptr
// 观察 → 裸指针或 reference_wrapper
// 共享 → shared_ptr
```

### 4. 使用 at() / 边界检查

对容器索引，用 `vec.at(i)` 而非 `vec[i]` 当输入不可信时。

### 5. RAII 替代手动 new/delete

```cpp
auto p = std::make_unique<Widget>(args);
// 异常安全，自动释放
```

## 学习要点总结

1. 指针存地址，引用是别名；引用必须初始化且不可改绑
2. 用 `nullptr` 代替 `NULL`/`0` 表示空指针
3. 函数参数：不可空用引用，可空用指针或 `optional`；只读用 `const T&`
4. 绝不返回局部变量/临时对象的指针或引用
5. 动态内存优先智能指针，裸指针仅作非拥有观察者
6. `const` 在 `*` 左修饰指向内容，在右修饰指针本身
7. 指针算术单位是 `sizeof(T)`，仅在同一数组内有意义
