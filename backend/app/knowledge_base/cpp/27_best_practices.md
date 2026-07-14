# C++ 编程最佳实践

## 核心理念

现代 C++ 强调：

- **RAII** 管理资源
- **值语义** 与明确所有权
- **类型安全** 替代宏与 void*
- **标准库** 替代手写轮子
- **const 正确性** 与 **constexpr**
- **异常安全** 与可测试设计

以下实践来自社区共识、C++ Core Guidelines 和工程经验。

## 资源管理

### RAII 优先

```cpp
// 不好
void bad() {
    int* p = new int[1000];
    process(p);
    delete[] p;   // 若 process 抛异常，泄漏
}

// 好
void good() {
    std::vector<int> v(1000);
    process(v.data());
}   // 自动释放
```

**规则**：资源（内存、文件、锁、句柄）的获取与释放绑定到对象生命周期。

### 智能指针所有权

```cpp
// 独占所有权
auto widget = std::make_unique<Widget>();

// 共享所有权（确实需要共享时）
auto shared = std::make_shared<Resource>();

// 观察者：不拥有
void observe(const Widget* w) { /* 不 delete */ }
void observeWeak(std::weak_ptr<Resource> wp) {
    if (auto sp = wp.lock()) { /* 使用 */ }
}
```

| 类型 | 语义 |
|:---|:---|
| `unique_ptr` | 独占，默认选择 |
| `shared_ptr` | 共享，注意循环引用 |
| `weak_ptr` | 打破循环，观察 shared |
| 裸指针 | 非拥有、可选、C 互操作 |

**Rule of Zero**：若类成员均为 RAII 类型，不必手写三五法则。

```cpp
class Document {
    std::string title;
    std::vector<Page> pages;
    // 编译器生成的特殊成员通常足够
};
```

## 接口设计

### 参数传递

```cpp
void read(const std::string& s);           // 只读，大对象
void modify(std::string& s);               // 修改
void take(std::string s);                  // 小对象或明确拷贝
void take(std::string_view sv);            // 只读，零拷贝视图（C++17）
void consume(std::unique_ptr<Widget> w);   // 转移所有权
template<typename... Args>
void emplace(Args&&... args);              // 完美转发
```

**经验法则**：
- 输入 + 只读 + 大 → `const T&` 或 `string_view`
- 输入 + 需拷贝 → 按值传递 `T`（配合移动）
- 输出 → 优先**返回值**，少用输出参数

### 返回值

```cpp
// 大对象：移动或 RVO（不要对局部变量 std::move 返回）
std::vector<int> createVector();

// 可选
std::optional<User> findUser(int id);

// 错误处理
User getUser(int id);              // 找不到抛异常
std::expected<User, Error> tryGet(int id);   // C++23

// 不可拷贝但可移动
std::unique_ptr<Widget> createWidget();
```

**RVO/NRVO**：编译器常省略拷贝，返回局部对象即可，无需 `std::move`。

### 输出参数 vs 返回

```cpp
// 不推荐
void parse(const std::string& s, int& outVal, std::string& outErr);

// 推荐
struct ParseResult { int value; std::optional<std::string> error; };
ParseResult parse(const std::string& s);
```

Core Guidelines **F.20**：输出参数用 return 代替。

## const 正确性

```cpp
class Account {
    double balance{};
public:
    double getBalance() const { return balance; }
    void deposit(double amount) { balance += amount; }
};

void printAccount(const Account& acc) {
    std::cout << acc.getBalance();
}
```

- 不修改成员的方法加 `const`
- 只读参数用 `const T&`
- 能加 `const` 就加，编译器帮你防止意外修改

## 避免裸 new/delete

```cpp
// 不好
Widget* w = new Widget();
delete w;

// 好
auto w = std::make_unique<Widget>();

// 容器
std::vector<std::unique_ptr<Widget>> widgets;
widgets.push_back(std::make_unique<Widget>());
```

**例外**：自定义内存池、Placement new、与 C API 互操作——仍应用 RAII 包装。

## 使用 STL 而非 reinvent

```cpp
// 不好
void bubbleSort(std::vector<int>& v) { /* O(n²) */ }

// 好
std::sort(v.begin(), v.end());

// 查找
auto it = std::find(v.begin(), v.end(), target);

// 累加
int sum = std::accumulate(v.begin(), v.end(), 0);

// 字符串格式化（C++20）
std::string msg = std::format("Hello, {}!", name);
```

**原则**：表达意图，利用已测试的标准库实现。

## 头文件与编译

```cpp
// widget.h — 最小依赖
#ifndef WIDGET_H
#define WIDGET_H

#include <string>

class Dependency;   // 前向声明

class Widget {
    std::string name;
public:
    void use(const Dependency& dep);
};

#endif

// widget.cpp
#include "widget.h"
#include "dependency.h"   // 实现文件中 include
```

- 头文件 guard 或 `#pragma once`
- 不在头文件 `using namespace std`
- 实现放 `.cpp`，减少编译依赖
- 模板实现放 `.hpp` 或在头文件末尾 `#include "foo.inl"`

## 错误处理策略

| 场景 | 推荐 |
|:---|:---|
| 编程错误（不变量违反） | `assert` |
| 预期失败（文件不存在） | `optional`、错误码、`expected` |
| 无法局部恢复的错误 | 异常 |
| 构造函数失败 | 异常（无返回值可报告） |
| 析构函数 | **绝不**抛异常 |

**一致性**：项目内统一策略，避免同一模块混用异常与错误码且无文档。

## 性能意识

```cpp
// 预分配
v.reserve(expectedSize);

// 避免不必要的拷贝
void process(const LargeObject& obj);
for (const auto& item : container) { }

// 移动大对象
std::vector<int> v2 = std::move(v1);

// 字符串拼接大量内容
std::ostringstream ss;
for (const auto& s : parts) ss << s;
// 或 C++20 format
```

**Knuth**："Premature optimization is the root of all evil."

1. 写正确清晰的代码
2. 测量瓶颈（profiler、benchmark）
3. 针对性优化热点

## 代码可读性

```cpp
// 不好
int* p = new int(d());

// 好
auto value = computeValue();
auto stored = std::make_unique<int>(value);

// 早 return 减少嵌套
std::optional<User> findUser(int id) {
    if (id <= 0) return std::nullopt;
    auto it = db.find(id);
    if (it == db.end()) return std::nullopt;
    return it->second;
}
```

- 有意义的命名（`userCount` 而非 `n`）
- 函数做一件事
- 避免过深嵌套
- 注释解释**为什么**，而非**做什么**

## 命名与风格

- 类型：`PascalCase`（`class UserAccount`）
- 函数/变量：`camelCase` 或 `snake_case`（团队统一即可）
- 常量：`kMaxSize` 或 `MAX_SIZE`
- 成员变量：`name_` 或 `m_name`（二选一）
- 宏：全大写 `MAX_BUFFER`

**关键**：项目内一致，超过个人偏好。

## Core Guidelines 要点（精选）

[Bjarne Stroustrup 与 ISO C++ 委员会维护](https://isocpp.github.io/CppCoreGuidelines/)：

| 编号 | 要点 |
|:---|:---|
| P.1 | 代码应表达意图 |
| I.11 | 非拥有指针不单独表示所有权 |
| F.20 | 输出参数用 return 代替 |
| F.21 | 多返回值用 struct 或 tuple |
| ES.20 | 始终初始化对象 |
| ES.23 | 优先 `{}` 初始化 |
| R.1 | 管理资源用 RAII |
| R.11 | 避免调用 new 和 delete |
| Con.1 | 默认 immutable（const） |
| Con.2 | 默认 const 成员函数 |
| T.1 | 用模板提高抽象层次 |
| T.10 | concepts 约束模板（C++20） |
| CP.1 | 假定代码会用于多线程 |
| CP.2 | 避免数据竞争 |
| E.1 | 用异常而非错误码处理不可恢复错误（按项目） |

## 常见反模式

| 反模式 | 替代 |
|:---|:---|
| C 风格 C++ | STL + RAII + 现代特性 |
| 裸指针所有权 | unique_ptr / shared_ptr |
| 宏做常量/函数 | constexpr / inline / template |
| using namespace std 在头文件 | 显式 std:: 或 cpp 内局部 using |
| void main() | int main() |
| 忽略编译器警告 | -Wall -Wextra，CI 中 -Werror |
| 手动资源管理 | RAII 包装 |
| 过度继承 | 组合优先 |
| 返回局部引用 | 返回值或 shared_ptr |
| 全局 mutable 状态 | 封装、thread_local、依赖注入 |

## 测试与质量保障

- **单元测试**覆盖核心逻辑与边界
- **Sanitizer**（ASan、UBSan、TSan）在 CI 中运行
- **静态分析**（clang-tidy、cppcheck）
- **代码审查**关注所有权、异常安全、API 设计
- **格式化**（clang-format）统一风格

## 学习路径建议

```
1. 基础语法（类型、控制流、函数）
2. 面向对象（类、继承、多态）
3. STL 容器与算法
4. 内存管理（RAII、智能指针、移动语义）
5. 模板与泛型编程
6. 工程实践（构建、调试、测试、多线程）
7. 阅读 Effective Modern C++、C++ Core Guidelines
8. 参与开源或实战项目巩固
```

## 代码审查清单（简要）

- [ ] 是否有裸 new/delete 或可改为智能指针？
- [ ] 接口是否明确 const 与所有权？
- [ ] 是否有资源泄漏路径（异常、早 return）？
- [ ] 是否检查了文件/指针/边界？
- [ ] 多线程共享数据是否有同步？
- [ ] 头文件依赖是否最小？
- [ ] 是否有单元测试？

## 学习要点总结

1. **RAII + 智能指针** 是现代 C++ 资源管理基石
2. 接口设计明确所有权、const 语义与错误处理策略
3. 优先 STL 和标准算法，保持代码简洁可测
4. 头文件最小化依赖，禁止污染命名空间
5. 先正确后快速，用 sanitizer、测试、profiler 保障质量
6. 遵循 Core Guidelines，团队内统一命名与风格
7. 持续学习新标准和工具，但不过度追新牺牲可维护性
