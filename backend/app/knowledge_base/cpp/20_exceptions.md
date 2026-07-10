# C++ 异常处理

## 异常机制概览

C 语言错误处理通常靠**返回码**（`-1`、`NULL`、`errno`），调用者容易忽略检查。C++ 异常提供**自动传播**的错误路径，与正常控制流分离。

```cpp
try {
    if (error_condition) {
        throw std::runtime_error("Something went wrong");
    }
    // 正常逻辑
} catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << std::endl;
} catch (...) {
    std::cerr << "Unknown error" << std::endl;
}
```

**执行流程**：

```
throw 抛出
    ↓
栈展开 (stack unwinding)：沿调用链向上
    ↓
自动析构路径上的局部对象（RAII）
    ↓
匹配 catch 子句（按顺序，派生类在前）
    ↓
执行 handler 或继续传播
```

**与 C 对比**：

| | C 返回码 | C++ 异常 |
|:---|:---|:---|
| 错误传播 | 每层手动检查 | 自动向上传播 |
| 与正常流混合 | 是 | 分离（try/catch） |
| 构造函数失败 | 难以表达 | throw 天然支持 |
| 性能 | 无额外开销 | 正常路径零开销（table-based） |
| 忽略错误 | 容易 | throw 不捕获则 terminate |

## 标准异常层次

```
std::exception
├── std::logic_error          （逻辑/编程错误，可预见）
│   ├── std::invalid_argument
│   ├── std::domain_error
│   ├── std::length_error
│   └── std::out_of_range
├── std::runtime_error        （运行时错误）
│   ├── std::overflow_error
│   ├── std::underflow_error
│   ├── std::range_error
│   └── std::system_error     (C++11)
└── std::bad_alloc            (new 失败)
    └── std::bad_array_new_length (C++11)
```

```cpp
#include <stdexcept>
#include <vector>

std::vector<int> v = {1, 2, 3};
v.at(100);   // 抛出 std::out_of_range

throw std::invalid_argument("Negative value not allowed");
throw std::runtime_error("File not found");
```

| 类型 | 典型场景 |
|:---|:---|
| `invalid_argument` | 参数语义错误（如负数开方） |
| `out_of_range` | 索引越界（`vector::at`） |
| `length_error` | 容器超过 max_size |
| `bad_alloc` | `new` 内存不足 |
| `runtime_error` | 通用运行时失败 |

## 按值抛出，按 const 引用捕获

```cpp
try {
    throw std::runtime_error("fail");
} catch (const std::runtime_error& e) {   // 推荐：派生类在前
    std::cerr << e.what() << '\n';
} catch (const std::exception& e) {        // 基类在后
    std::cerr << e.what() << '\n';
} catch (...) {                            // 捕获任意类型
    std::cerr << "Unknown\n";
}
```

**不要** `catch (exception e)` 按值捕获：

1. **对象切片**：派生类部分被截断
2. **拷贝开销**：异常对象可能较大

**捕获顺序**：派生类必须在基类**之前**，否则派生类 handler 永远 unreachable。

## RAII 与异常安全

异常发生时，已构造的局部对象按**逆序析构**，RAII 保证资源释放：

```cpp
void func() {
    std::fstream file("data.txt");
    std::vector<int> v(1000);
    risky_operation();   // 若抛异常，file 和 v 自动析构
}
```

**C 对比**：C 需在每条错误路径手动 `free`/`fclose`，极易泄漏：

```c
void bad_c() {
    int *p = malloc(100 * sizeof(int));
    FILE *f = fopen("data.txt", "r");
    if (!f) { free(p); return; }   // 每条路径都要清理
    if (error) { free(p); fclose(f); return; }
    // ...
}
```

### 异常安全保证级别

| 级别 | 含义 | 实现手段 |
|:---|:---|:---|
| 无保证 | 可能泄漏或数据损坏 | 避免 |
| 基本保证 | 不泄漏，对象处于有效（可能改变）状态 | RAII |
| 强保证 | 失败则状态不变 | copy-and-swap |
| 无抛保证 | 绝不抛异常 | `noexcept` |

**copy-and-swap 示例**：

```cpp
class Widget {
    int* data;
    size_t size;
public:
    Widget& operator=(const Widget& other) {
        Widget temp(other);   // 拷贝可能抛，原对象未改
        swap(temp);           // swap 通常 noexcept
        return *this;         // temp 析构旧资源
    }
    void swap(Widget& other) noexcept {
        std::swap(data, other.data);
        std::swap(size, other.size);
    }
};
```

## noexcept

```cpp
void safe_func() noexcept {
    // 承诺不抛异常；若抛则 std::terminate
}

void maybe_func() noexcept(false) { }

// 条件 noexcept
template<typename T>
void swap(T& a, T& b) noexcept(noexcept(a.swap(b)));
```

**用途**：
1. 移动构造/析构标记 `noexcept` → 容器扩容用移动
2. 表达接口契约
3. `noexcept` 表达式用于 trait（如 `std::is_nothrow_move_constructible`）

**析构函数**默认 `noexcept`（C++11 起）。析构函数抛异常 → `std::terminate`。

## 何时用异常，何时不用

**适合异常**：
- 真正**异常**的错误，无法局部恢复
- 构造函数失败（无法返回错误码）
- 错误需跨多层传播
- 库代码，调用者策略未知

**不适合异常**：
- **预期**的控制流（文件不存在、用户输入错误）→ `optional`、错误码
- 性能极度敏感的热路径（如游戏物理每帧）
- 嵌入式/无异常支持的环境（`-fno-exceptions`）

```cpp
// 预期失败：optional
std::optional<int> parseInt(const std::string& s) {
    try {
        return std::stoi(s);
    } catch (...) {
        return std::nullopt;
    }
}

// 真正意外：异常
void access(std::vector<int>& v, size_t i) {
    if (i >= v.size()) throw std::out_of_range("index");
    // 或使用 v.at(i)
}
```

## 自定义异常

```cpp
class NetworkError : public std::runtime_error {
    int errorCode;
public:
    NetworkError(const std::string& msg, int code)
        : std::runtime_error(msg), errorCode(code) {}
    int code() const { return errorCode; }
};

try {
    throw NetworkError("Connection refused", 111);
} catch (const NetworkError& e) {
    std::cerr << e.what() << " (code: " << e.code() << ")\n";
}
```

**设计建议**：
- 继承 `std::exception` 或其子类
- 实现 `what()`（基类已提供）
- 添加领域特定信息（错误码、上下文）

## 构造函数与异常

构造函数没有返回值，失败只能 throw：

```cpp
class Resource {
    int* data;
    std::fstream file;
public:
    Resource(const std::string& path) : data(new int[100]) {
        file.open(path);
        if (!file.is_open()) {
            delete[] data;   // 手动清理——容易遗漏
            throw std::runtime_error("Cannot open file");
        }
    }
    ~Resource() { delete[] data; }
};
```

**更好的做法**：成员全是 RAII，编译器自动清理已构造成员：

```cpp
class BetterResource {
    std::vector<int> data;
    std::fstream file;
public:
    BetterResource(const std::string& path) {
        file.open(path);
        if (!file.is_open()) throw std::runtime_error("Cannot open file");
        data.resize(100);   // 若抛异常，file 自动关闭
    }
    // 无需自定义析构
};
```

**两阶段构造**：若构造逻辑复杂，可用工厂函数返回 `optional`/`unique_ptr`，或 `init()` 方法（但对象可能处于未初始化状态，不推荐）。

## std::optional 与 std::expected

### optional（C++17）

```cpp
#include <optional>

std::optional<double> divide(double a, double b) {
    if (b == 0) return std::nullopt;
    return a / b;
}

if (auto result = divide(10, 2)) {
    std::cout << *result << '\n';
}
```

### expected（C++23）

同时携带**值或错误信息**，是错误码的现代替代：

```cpp
#include <expected>

std::expected<int, std::string> parse(const std::string& s) {
    if (s.empty()) return std::unexpected("empty string");
    return std::stoi(s);
}

auto r = parse("42");
if (r) {
    std::cout << *r << '\n';
} else {
    std::cerr << r.error() << '\n';
}
```

| 机制 | 携带成功值 | 携带错误信息 | 传播方式 |
|:---|:---|:---|:---|
| 返回码 | 输出参数 | int 码 | 手动 |
| optional | ✓ | 无（仅空） | 手动 |
| expected | ✓ | ✓ | 手动 |
| 异常 | — | what() 字符串 | 自动 |

## 常见错误与陷阱

### 1. 析构函数抛异常

```cpp
~Resource() {
    cleanup();   // 若抛异常且已有异常传播中 → std::terminate
}
```

**原因**：栈展开过程中再抛异常无法处理。**修复**：析构函数内 catch 并吞掉，或标记 `noexcept` 确保不抛。

### 2. 捕获顺序错误

```cpp
try { /* ... */ }
catch (const std::exception& e) { }      // 基类在前——错误！
catch (const std::runtime_error& e) { }  // 永远执行不到
```

**原因**：`runtime_error` 是 `exception` 派生类，第一个 catch 已匹配。

### 3. 按值 catch 导致切片

```cpp
catch (std::exception e) {   // 派生类信息丢失
    std::cout << e.what();
}
```

### 4. 非 RAII 导致泄漏

```cpp
void bad() {
    int* p = new int[100];
    risky();        // 抛异常 → 泄漏
    delete[] p;
}
```

**修复**：用 `vector` 或 `unique_ptr`。

### 5. 异常规格过时

C++11 前 `void f() throw(int);` 动态异常规格已**废弃**；C++11 起用 `noexcept`。

### 6. 滥用异常做控制流

```cpp
// 反模式：用异常遍历
try {
    while (true) process(queue.pop());   // pop 空队列抛异常
} catch (const EmptyException&) { }
```

**原因**：异常开销远高于正常分支；破坏代码可读性。**修复**：用 `optional` 或检查空。

### 7. throw 临时字符串

```cpp
throw "error";   // 抛出 const char*，catch 需精确匹配
throw std::string("error");   // 更好
throw std::runtime_error("error");   // 最佳
```

## 学习要点总结

1. 异常用于**不可恢复或难局部处理**的错误；预期失败用 `optional`/错误码
2. **RAII** 保证异常时资源自动释放，是异常安全的基础
3. 按 **const 引用** 捕获，**派生类 catch 在前**
4. 移动操作和析构函数尽量 `noexcept`
5. 构造函数中优先 RAII 成员，避免手动清理
6. 析构函数**绝不能**抛异常；非 RAII 资源是异常安全的主要敌人
