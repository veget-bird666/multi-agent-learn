# C++ STL 容器

## STL 架构概览

标准模板库（Standard Template Library）由 Alexander Stepanov 设计，核心思想是**分离数据结构与算法**，通过迭代器解耦：

```
┌─────────────┐     迭代器      ┌─────────────┐
│   容器       │ ──────────────→ │   算法       │
│ vector, map │                 │ sort, find  │
└─────────────┘                 └─────────────┘
       ↑                               ↑
       └──────── 函数对象 / Lambda ─────┘
```

**与 C 对比**：

| C 语言 | C++ STL |
|:---|:---|
| `int arr[100]` 固定数组 | `std::array<int, 100>` 带 size、迭代器 |
| `malloc` + 手动扩容 | `std::vector` 自动管理 |
| 手写链表节点 | `std::list` 开箱即用 |
| `qsort` + 函数指针 | `std::sort` + 迭代器 + Lambda |
| 无标准哈希表 | `std::unordered_map` |

## 序列容器

### vector（动态数组）—— 默认首选

```cpp
std::vector<int> v = {1, 2, 3};
v.push_back(4);           // 尾部追加，均摊 O(1)
v.pop_back();             // 尾部删除 O(1)
v[0];                     // 随机访问 O(1)，不检查边界
v.at(0);                  // 随机访问 O(1)，越界抛 out_of_range
v.size(); v.capacity();   // size ≤ capacity
v.reserve(1000);          // 预分配，避免多次 realloc
v.shrink_to_fit();        // 请求释放多余 capacity（非强制）
```

**内存模型**：

```
v = {1, 2, 3, _, _}   size=3, capacity=5
     ↑           ↑
   begin()      end()（指向最后一个元素之后）
```

**扩容策略**：通常按 1.5 或 2 倍增长（实现定义）。`push_back` 触发扩容时，所有元素移动/拷贝到新内存，**迭代器全部失效**。

| 操作 | 时间复杂度 | 迭代器影响 |
|:---|:---|:---|
| `push_back` / `pop_back` | 均摊 O(1) | 扩容时全部失效 |
| `insert` / `erase` 中间 | O(n) | 插入/删除点及之后失效 |
| `[]` / `at` | O(1) | 无 |
| `reserve` | O(n) 若扩容 | 失效 |

### deque（双端队列）

```cpp
std::deque<int> dq;
dq.push_front(1);   // 头插 O(1)
dq.push_back(2);    // 尾插 O(1)
dq.pop_front();
dq[0];              // 随机访问 O(1)
```

**与 vector 对比**：

| | vector | deque |
|:---|:---|:---|
| 内存布局 | 连续一块 | 分段连续（中控 map） |
| 中间插入 | O(n) | O(n) |
| 头插 | O(n) | O(1) |
| 缓存友好 | 最好 | 较好 |
| 迭代器 | 随机访问 | 随机访问 |

**注意**：`deque` 的迭代器不如 `vector` 简单，某些操作中迭代器失效规则更复杂。

### list / forward_list（链表）

```cpp
std::list<int> lst = {1, 2, 3};
lst.push_front(0);
auto it = lst.begin();
++it;
lst.insert(it, 99);   // 在 it 前插入 O(1)

std::forward_list<int> flst = {1, 2, 3};   // 单向，更省内存
flst.insert_after(flst.before_begin(), 0);
```

| 操作 | list | vector |
|:---|:---|:---|
| 任意位置插入/删除 | O(1)（已有迭代器） | O(n) |
| 随机访问 | 不支持 | O(1) |
| 内存开销 | 每节点额外指针 | 仅 capacity 冗余 |

**适用**：频繁中间插入删除，且不需要随机访问。多数场景 `vector` 仍更快（缓存局部性）。

### array（固定数组，C++11）

```cpp
#include <array>
std::array<int, 5> arr = {1, 2, 3, 4, 5};
arr.size();    // 5，编译期常量
arr.at(10);    // 抛异常
```

**与 C 数组对比**：栈上分配、大小固定，但有 `size()`、迭代器、不 decay 为指针。

## 关联容器

### set / multiset（有序集合）

```cpp
std::set<int> s = {3, 1, 4, 1, 5};   // {1, 3, 4, 5}，去重且有序
s.insert(2);
s.count(3);       // 0 或 1
s.find(3);        // 迭代器，未找到则 end()
s.lower_bound(3); // ≥3 的第一个
s.erase(3);
```

底层**红黑树**，元素始终有序。

### map / multimap（有序映射）

```cpp
std::map<std::string, int> scores;
scores["Alice"] = 90;                    // 插入或修改
scores.insert({"Bob", 85});
scores.emplace("Charlie", 88);           // 原地构造，避免临时对象

for (const auto& [name, score] : scores) {   // C++17 结构化绑定
    std::cout << name << ": " << score << '\n';
}

scores.at("Alice");    // 90，键不存在抛 out_of_range
scores["Unknown"];     // 插入 {"Unknown", 0} 并返回 0 的引用！
```

**`operator[]` 陷阱**：

```cpp
if (scores["Bob"] > 80) { }   // Bob 不存在时会插入默认值 0
// 正确做法：
if (auto it = scores.find("Bob"); it != scores.end() && it->second > 80) { }
// 或 C++20 contains：
if (scores.contains("Bob") && scores.at("Bob") > 80) { }
```

**原因**：`operator[]` 设计要求键必须存在，不存在则**默认插入**。

## 无序关联容器（C++11）

```cpp
#include <unordered_map>
std::unordered_map<std::string, int> um;
um["Alice"] = 90;
um.bucket_count();     // 桶数量
um.load_factor();      // 元素数/桶数
um.rehash(100);        // 调整桶数量
```

底层**哈希表**，通过 `std::hash<Key>` 和 `operator==` 工作。

| 容器 | 底层 | 有序 | 平均查找 | 最坏查找 | 内存 |
|:---|:---|:---|:---|:---|:---|
| `map`/`set` | 红黑树 | 是 | O(log n) | O(log n) | 较低 |
| `unordered_map`/`set` | 哈希表 | 否 | O(1) | O(n) | 较高 |

**自定义键类型**需提供：

```cpp
struct Point { int x, y; };

namespace std {
template<>
struct hash<Point> {
    size_t operator()(const Point& p) const {
        return hash<int>()(p.x) ^ (hash<int>()(p.y) << 1);
    }
};
}

// 还需 operator== 用于桶内比较
bool operator==(const Point& a, const Point& b) {
    return a.x == b.x && a.y == b.y;
}
```

## 容器适配器

适配器**不提供迭代器**，限制底层容器的接口：

```cpp
#include <stack>
#include <queue>

std::stack<int> stk;                    // 默认底层 deque
std::stack<int, std::vector<int>> stk2; // 指定底层 vector

std::queue<int> q;                      // 默认底层 deque
std::priority_queue<int> pq;            // 默认大顶堆，底层 vector
std::priority_queue<int, std::vector<int>, std::greater<int>> minHeap;
```

| 适配器 | 接口 | 默认底层 |
|:---|:---|:---|
| `stack` | push, pop, top | `deque` |
| `queue` | push, pop, front, back | `deque` |
| `priority_queue` | push, pop, top | `vector` + 堆 |

## pair、tuple 与 optional

### pair 与 tuple

```cpp
#include <utility>
#include <tuple>

auto p = std::make_pair("Alice", 90);
p.first; p.second;

auto t = std::make_tuple(1, "hello", 3.14);
std::get<0>(t);
auto [a, b, c] = t;   // C++17 结构化绑定
```

### optional（C++17）

```cpp
#include <optional>

std::optional<int> find(const std::vector<int>& v, int target) {
    for (int x : v) {
        if (x == target) return x;
    }
    return std::nullopt;
}

if (auto result = find(v, 5)) {
    std::cout << *result << '\n';
} else {
    std::cout << "not found\n";
}
```

**对比 C**：C 用 `-1`、`NULL` 或输出参数表示"无值"，语义模糊；`optional` 类型安全。

### variant 与 any（C++17）

```cpp
#include <variant>
std::variant<int, std::string> v = 42;
v = "hello";
std::get<std::string>(v);

#include <any>
std::any a = 42;
a = std::string("hi");
std::any_cast<std::string>(a);
```

## 迭代器失效规则汇总

| 容器 | insert | erase | push_back 等 |
|:---|:---|:---|:---|
| `vector` | 插入点及之后失效；扩容则全部失效 | 删除点及之后失效 | 扩容时全部失效 |
| `deque` | 首尾不影响中间；中间插入全部可能失效 | 中间/尾删除可能全部失效 | 首尾操作不影响中间 |
| `list` | 不失效 | 仅被删元素失效 | — |
| `map`/`set` | 不失效 | 仅被删元素失效 | — |
| `unordered_*` | 可能触发 rehash 全部失效 | 仅被删元素失效 | rehash 时全部失效 |

## 容器选择指南

| 需求 | 推荐 | 原因 |
|:---|:---|:---|
| 默认序列容器 | `vector` | 缓存友好、接口简单、多数操作够快 |
| 频繁头尾插入 | `deque` | 头插 O(1) |
| 频繁中间插入删除且不需随机访问 | `list` | O(1) 插入删除 |
| 有序 + 范围查询 | `map`/`set` | O(log n) 且有序 |
| 快速查找、不需有序 | `unordered_map`/`set` | 平均 O(1) |
| 固定大小、栈上 | `array` | 零堆分配 |
| 栈/队列/堆 | 适配器 | 语义清晰 |
| 可选返回值 | `optional` | 避免 magic number |

## 常见错误与陷阱

### 1. vector 迭代器失效

```cpp
auto it = v.begin();
v.push_back(100);   // 可能扩容
*it = 99;          // 未定义行为！
```

**原因**：`push_back` 可能 reallocate，原内存释放。**修复**：重新获取迭代器，或用索引。

### 2. map 下标运算符副作用

见上文 `scores["Unknown"]` 示例。**原因**：`operator[]` 语义是"取或插入默认值"。

### 3. 比较 unordered 容器的遍历顺序

```cpp
for (auto& [k, v] : um1) { /* ... */ }
for (auto& [k, v] : um2) { /* ... */ }
// 相同内容的 um1、um2 遍历顺序可能不同
```

**原因**：哈希值和桶布局依赖实现与 rehash 历史。

### 4. vector<bool> 不是真正容器

`vector<bool>` 是**位压缩代理**，`operator[]` 返回代理对象而非 `bool&`，不能取地址、不能绑定到 `bool&`。

```cpp
std::vector<bool> vb = {true, false};
// bool& ref = vb[0];   // 错误！
auto it = vb.begin();
// bool& ref2 = *it;    // 错误！
```

**替代**：需要 `bool&` 时用 `vector<char>` 或 `deque<bool>`。

### 5. 空容器 front/back

```cpp
std::vector<int> v;
v.front();   // 未定义行为！
```

**修复**：先检查 `empty()`，或用 `at(0)`。

## 学习要点总结

1. **默认用 `vector`**，除非有明确理由选其他容器
2. 有序键值用 `map`/`set`，快速查找用 `unordered_*`
3. `optional` 表达可选值，比 C 的 magic number 更安全
4. 修改容器前查**迭代器失效表**，避免悬空迭代器
5. 理解各容器时间复杂度，选对数据结构比优化循环更重要
6. 容器适配器不提供迭代器，不能用于 STL 算法直接操作（除 priority_queue 底层可访问）
