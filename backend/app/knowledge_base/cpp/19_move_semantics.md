# C++ 移动语义与完美转发

## 为什么需要移动语义

C++ 拷贝语义对含堆资源的类型代价高昂：

```cpp
std::vector<int> createLarge() {
    std::vector<int> v(1'000'000, 42);
    return v;   // C++11 前：可能深拷贝；C++11 后：可移动
}
```

**C 对比**：C 只能 `memcpy` 浅拷贝（危险）或手动深拷贝（慢），没有"转移所有权"的标准语义。C++ 移动语义让**资源转移**成为语言一等公民。

## 左值与右值

**值类别**决定能绑定哪种引用、调用拷贝还是移动：

| 表达式 | 分类 | 说明 |
|:---|:---|:---|
| 变量名 `x` | 左值 (lvalue) | 有名字，可取地址 |
| 字面量 `42`, `"hi"` | 右值 (prvalue) | 临时量 |
| 函数返回的临时对象 | 右值 | `getString()` |
| `std::move(x)` | 将 x 转为右值 (xvalue) | 只是 cast，不移动 |
| 左值引用 `T&` | — | 绑定左值 |
| 右值引用 `T&&` | — | 绑定右值 |

```cpp
int x = 10;        // x 是左值
int& lref = x;     // OK
int&& rref = 10;   // OK，绑定到临时量
// int& bad = 10;  // 错误！非 const 左值引用不能绑定右值

const int& cref = 10;   // OK，const 左值引用可绑定右值
// 延长临时对象生命周期到 cref 作用域结束
```

### 值类别层次（C++11 起）

```
         表达式
        /      \
    glvalue   rvalue
    /    \     /    \
 lvalue  xvalue  prvalue
```

日常只需区分：**有名字能取地址 → 左值；临时量 → 右值**。

## 拷贝 vs 移动

```cpp
class Buffer {
    size_t size;
    int* data;
public:
    Buffer(size_t n) : size(n), data(new int[n]) {}

    ~Buffer() { delete[] data; }

    // 拷贝构造：深拷贝
    Buffer(const Buffer& other) : size(other.size), data(new int[size]) {
        std::copy(other.data, other.data + size, data);
    }

    // 移动构造：窃取资源
    Buffer(Buffer&& other) noexcept
        : size(other.size), data(other.data) {
        other.data = nullptr;
        other.size = 0;
    }

    // 拷贝赋值
    Buffer& operator=(const Buffer& other) {
        if (this == &other) return *this;
        delete[] data;
        size = other.size;
        data = new int[size];
        std::copy(other.data, other.data + size, data);
        return *this;
    }

    // 移动赋值
    Buffer& operator=(Buffer&& other) noexcept {
        if (this == &other) return *this;
        delete[] data;
        size = other.size;
        data = other.data;
        other.data = nullptr;
        other.size = 0;
        return *this;
    }
};
```

**移动后源对象**：处于**有效但未指定状态**——可安全销毁、可重新赋值，但不应再依赖其内容。

| 操作 | 拷贝 | 移动 |
|:---|:---|:---|
| 资源 | 分配新内存 + 复制 | 转移指针，源置空 |
| 开销 | O(n) | O(1) |
| 源对象 | 不变 | 被掏空 |

## std::move

```cpp
std::vector<int> v1 = {1, 2, 3, 4, 5};
std::vector<int> v2 = std::move(v1);   // 调用移动构造

// v1 仍有效（可析构、可赋值），但内容不确定
v1.size();   // 可能为 0
```

`std::move` 本质是 `static_cast<T&&>(x)`，**不实际移动任何东西**，只是告诉编译器"可以把 x 当右值用"，真正移动发生在移动构造/赋值。

```cpp
template<typename T>
typename std::remove_reference<T>::type&& move(T&& arg) {
    return static_cast<typename std::remove_reference<T>::type&&>(arg);
}
```

## 返回值优化（RVO/NRVO）

```cpp
Buffer createBuffer() {
    Buffer b(1000);
    return b;   // NRVO：可能直接在调用者空间构造
}

auto buf = createBuffer();   // C++17 起某些情况强制 copy elision
```

**Copy Elision 规则**：
- **RVO**：返回临时对象 `return Buffer(1000);`
- **NRVO**：返回命名局部对象 `return b;`
- C++17 起部分场景**强制**省略拷贝/移动，即使拷贝/移动构造函数有副作用

```cpp
Buffer create() {
    Buffer b;
    return std::move(b);   // 错误做法！阻止 NRVO，可能更慢
    return b;              // 推荐：让编译器优化
}
```

## 三五法则与零法则

**三五法则**：若自定义以下任一，通常需考虑全部五个：
- 析构函数
- 拷贝构造
- 拷贝赋值
- 移动构造（C++11）
- 移动赋值（C++11）

**零法则**：若所有成员都是 RAII 类型（`string`、`vector`、`unique_ptr`），**不要**自定义特殊成员，编译器生成的通常正确：

```cpp
class Modern {
    std::string name;
    std::vector<int> data;
    std::unique_ptr<Foo> ptr;
    // 编译器自动生成拷贝/移动/析构，遵循零法则
};
```

**C 对比**：C 结构体含指针时需手写"拷贝/释放"函数；C++ RAII + 零法则自动处理。

## 完美转发

模板中如何保持参数原有的值类别（左值/右值）？

```cpp
template<typename T>
void wrapper(T&& arg) {          // 转发引用（万能引用），不是右值引用！
    process(std::forward<T>(arg));
}

int x = 10;
wrapper(x);      // T=int&,  arg 类型 int&,  调用 process(int&)
wrapper(10);     // T=int,   arg 类型 int&&, 调用 process(int&&)
```

### 引用折叠

| T 的推导 | T&& 实际类型 |
|:---|:---|
| `int&` | `int&` |
| `int` | `int&&` |
| `int&&` | `int&&` |

### std::forward

```cpp
template<typename T>
T&& forward(typename std::remove_reference<T>::type& arg) {
    return static_cast<T&&>(arg);
}
```

- 若 `T` 是左值引用 → 转发为左值
- 若 `T` 是非引用 → 转发为右值

### 工厂函数示例

```cpp
template<typename T, typename... Args>
std::unique_ptr<T> makeUnique(Args&&... args) {
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}

auto p = makeUnique<std::vector<int>>(100, 42);   // 完美转发构造参数
```

**注意**：`T&&` 仅在**类型推导**的模板参数中是转发引用；`void f(int&& x)` 中的 `int&&` 就是普通右值引用。

## noexcept 与移动

```cpp
Buffer(Buffer&& other) noexcept { /* ... */ }
```

`std::vector` 扩容时：若元素类型的移动构造是 `noexcept`，则用**移动**；否则退化为**拷贝**（强异常安全）。

**原因**：移动过程中若抛异常，源对象可能已部分转移，难以保证强保证。

| 函数 | 建议 |
|:---|:---|
| 移动构造/赋值 | `noexcept`（若不抛） |
| 析构函数 | 隐式 `noexcept` |
| `swap` | 通常 `noexcept` |

## 移动语义与 STL

标准库大量容器、字符串支持移动：

```cpp
std::string s1 = "hello world";
std::string s2 = std::move(s1);   // s1 可能被掏空

std::vector<std::string> vec;
vec.push_back(std::move(s2));     // 移动而非拷贝

vec.emplace_back("direct");       // 原地构造，避免临时对象
```

## 常见错误与陷阱

### 1. 对 const 对象 std::move

```cpp
const std::vector<int> v = {1, 2, 3};
auto v2 = std::move(v);   // 调用拷贝构造，不是移动！
```

**原因**：移动构造/赋值通常接受非 const 右值引用 `T&&`，const 对象只能匹配 const 左值引用 → 拷贝。

### 2. 移动后继续使用源对象

```cpp
auto v2 = std::move(v1);
v1.push_back(4);   // 合法但 v1 内容不确定
v1[0];             // 可能崩溃或得到垃圾值
```

**原因**：移动后源对象处于有效但未指定状态。**修复**：移动后立刻重新赋值或不再读取。

### 3. 返回局部变量的 std::move

见 RVO 一节。**原因**：显式 `move` 阻止 NRVO，可能多一次移动。

### 4. 混淆 std::move 与 std::forward

| | std::move | std::forward |
|:---|:---|:---|
| 用途 | 无条件转右值 | 条件转发，保持原值类别 |
| 场景 | 已知不再需要源对象 | 模板转发参数 |
| 典型错误 | 对 const 使用 | 对非转发引用使用 |

### 5. 忘记定义移动操作导致拷贝

```cpp
class Resource {
    int* p;
public:
    Resource() : p(new int) {}
    ~Resource() { delete p; }
    Resource(const Resource& o) : p(new int(*o.p)) {}
    // 未定义移动 → 编译器可能=delete 移动，退化为拷贝
};
```

**修复**：显式定义移动或遵循零法则（用 `unique_ptr`）。

### 6. 右值引用变量本身是左值

```cpp
void consume(std::string&& s);

std::string&& rref = std::string("hi");   // rref 是左值（有名字）
// consume(rref);   // 错误！绑定不到右值引用
consume(std::move(rref));   // 正确
```

**原因**：有名字的变量无论声明类型都是左值。

## 只可移动类型（Move-Only）

某些类型禁止拷贝、只允许移动，典型如 `std::unique_ptr`：

```cpp
std::unique_ptr<int> p1 = std::make_unique<int>(42);
// std::unique_ptr<int> p2 = p1;           // 编译错误！拷贝被 delete
std::unique_ptr<int> p2 = std::move(p1);   // OK，转移所有权
// p1 现为 nullptr
```

**实现方式**：

```cpp
class MoveOnly {
    int* data;
public:
    MoveOnly() : data(new int) {}
    ~MoveOnly() { delete data; }

    MoveOnly(const MoveOnly&) = delete;            // 禁止拷贝
    MoveOnly& operator=(const MoveOnly&) = delete;

    MoveOnly(MoveOnly&& other) noexcept
        : data(other.data) { other.data = nullptr; }
    MoveOnly& operator=(MoveOnly&& other) noexcept { /* ... */ return *this; }
};
```

**C 对比**：C 无语言级"禁止拷贝"机制，只能靠文档约定或运行时检查。

## 移动语义与容器 realloc

`vector` 扩容时的决策树：

```
需要更大 capacity
    ↓
元素类型的移动构造是 noexcept？
    ├── 是 → 移动元素到新内存（快）
    └── 否 → 拷贝元素（安全，强异常保证）
```

因此自定义类型的移动操作应标记 `noexcept`，否则 `vector<MyType>` 扩容始终拷贝。

## 学习要点总结

1. **移动**转移资源所有权，避免深拷贝，O(1) 代价
2. `std::move` 是 cast，不移动；移动发生在移动构造/赋值
3. 返回值优化（RVO/NRVO）优于显式 `std::move` 返回局部对象
4. 模板转发参数用 `T&&` + `std::forward`，区分转发引用与右值引用
5. RAII 类型遵循**零法则**；移动操作标记 `noexcept` 以优化容器
6. 移动后源对象有效但未指定，不应再依赖其内容
7. **只可移动类型**（如 `unique_ptr`）通过 `= delete` 拷贝操作实现独占所有权
