# C++ 迭代器与算法

## 迭代器：泛化的指针

C 语言遍历数组靠下标或指针算术；不同数据结构（链表、树）访问方式各异。STL 用**迭代器**统一接口，使算法与容器解耦。

```cpp
std::vector<int> v = {1, 2, 3, 4, 5};

// 正向迭代器
for (auto it = v.begin(); it != v.end(); ++it) {
    std::cout << *it << ' ';
}

// 范围 for（语法糖，底层用 begin/end）
for (int x : v) { std::cout << x << ' '; }

// 反向迭代器
for (auto it = v.rbegin(); it != v.rend(); ++it) {
    std::cout << *it << ' ';   // 5 4 3 2 1
}

// 常量迭代器
for (auto it = v.cbegin(); it != v.cend(); ++it) {
    // *it = 10;   编译错误
}
```

**与 C 指针对比**：

| C | C++ 迭代器 |
|:---|:---|
| `int *p = arr` | `auto it = v.begin()` |
| `*(p + i)` | `it + i`（随机访问迭代器） |
| `p++` | `++it` |
| 无统一 end 概念 | `it != v.end()` |
| 不同类型无共同接口 | 所有容器都有 begin/end |

## 迭代器类别（Trait 层次）

```
输入 → 输出
  ↓
前向 → 双向 → 随机访问 → 连续（C++20）
```

| 类别 | 能力 | 支持操作 | 典型容器 |
|:---|:---|:---|:---|
| 输入 | 读、单遍 | `++`, `*`, `==` | `istream_iterator` |
| 输出 | 写、单遍 | `++`, `*` | `ostream_iterator` |
| 前向 | 读、多遍 | 上述 + 保存副本 | `forward_list` |
| 双向 | 双向移动 | 上述 + `--` | `list`, `map`, `set` |
| 随机访问 | 跳跃 | 上述 + `+n`, `-n`, `[]`, `<` | `vector`, `deque`, `array` |
| 连续（C++20） | 内存连续 | 上述 + `data()` 兼容 | `vector`, `array`, `string` |

**算法对迭代器的要求**：

| 算法 | 最低迭代器要求 |
|:---|:---|
| `find`, `for_each` | 输入 |
| `reverse` | 双向 |
| `sort`, `nth_element` | 随机访问 |
| `binary_search`, `lower_bound` | 随机访问 + 有序 |

## 常用算法（`<algorithm>`）

### 查找

```cpp
#include <algorithm>

std::vector<int> v = {1, 2, 3, 4, 5};

// 线性查找 O(n)
auto it = std::find(v.begin(), v.end(), 3);
if (it != v.end()) {
    std::cout << "Found at index " << (it - v.begin()) << '\n';
}

// 条件查找
auto it2 = std::find_if(v.begin(), v.end(),
    [](int x) { return x > 3; });

// 二分查找 O(log n)，要求有序
std::sort(v.begin(), v.end());
bool found = std::binary_search(v.begin(), v.end(), 3);
auto lb = std::lower_bound(v.begin(), v.end(), 3);   // 第一个 ≥3
auto ub = std::upper_bound(v.begin(), v.end(), 3);   // 第一个 >3
auto [lo, hi] = std::equal_range(v.begin(), v.end(), 3);  // [lb, ub)
```

**C 对比**：`bsearch` 需要 `void*` 和比较函数；C++ 算法类型安全且内联优化更好。

### 排序

```cpp
std::sort(v.begin(), v.end());                    // 升序，不稳定
std::stable_sort(v.begin(), v.end());             // 稳定，O(n log n) 或 O(n log² n)
std::partial_sort(v.begin(), v.begin() + 3, v.end());  // 只排序前 3 个
std::nth_element(v.begin(), v.begin() + 2, v.end());   // 第 3 小放正确位置
```

**比较函数必须满足严格弱序**：

```cpp
// 正确：a < b 和 b < a 不能同时为 true
auto good = [](int a, int b) { return a < b; };

// 错误：a <= b 不满足严格弱序
auto bad = [](int a, int b) { return a <= b; };
// sort 可能崩溃或结果未定义
```

| 算法 | 平均复杂度 | 最坏 | 稳定 | 前提 |
|:---|:---|:---|:---|:---|
| `sort` | O(n log n) | O(n log n) | 否 | 随机访问 |
| `stable_sort` | O(n log n) | O(n log² n) | 是 | 随机访问 |
| `partial_sort` | O(n log k) | O(n log k) | 否 | k = 部分长度 |
| `nth_element` | O(n) | O(n) | 否 | 随机访问 |

### 变换与拷贝

```cpp
std::vector<int> src = {1, 2, 3};
std::vector<int> dst(3);

std::transform(src.begin(), src.end(), dst.begin(),
    [](int x) { return x * 2; });   // dst = {2, 4, 6}

std::copy(src.begin(), src.end(), dst.begin());
std::copy_if(src.begin(), src.end(), dst.begin(),
    [](int x) { return x % 2 == 0; });
std::fill(v.begin(), v.end(), 0);
std::generate(v.begin(), v.end(), []() { return rand() % 100; });
std::replace(v.begin(), v.end(), 3, 99);
std::swap_ranges(v.begin(), v.end(), dst.begin());
```

**注意**：`copy` 目标区间必须足够大，否则越界。用 `back_inserter` 可自动扩容。

### 删除：erase-remove 惯用法

```cpp
// 删除所有值为 3 的元素
v.erase(std::remove(v.begin(), v.end(), 3), v.end());

// remove 并不真正删除，而是把要保留的元素前移，返回新逻辑 end
// erase 才真正缩短容器
```

**原理图解**：

```
原: [1, 3, 2, 3, 4]
remove(3): [1, 2, 4, 3, 4]  返回指向第二个4的迭代器
erase(该位置, end): [1, 2, 4]
```

C++20 简化：

```cpp
std::erase(v, 3);                              // 按值删除
std::erase_if(v, [](int x) { return x % 2 == 0; });
```

### 聚合与统计

```cpp
#include <numeric>

int sum = std::accumulate(v.begin(), v.end(), 0);
int product = std::accumulate(v.begin(), v.end(), 1, std::multiplies<>());
int cnt = std::count(v.begin(), v.end(), 3);
int cnt_if = std::count_if(v.begin(), v.end(), [](int x) { return x > 3; });
auto [min_it, max_it] = std::minmax_element(v.begin(), v.end());
bool allPositive = std::all_of(v.begin(), v.end(), [](int x) { return x > 0; });
bool anyNegative = std::any_of(v.begin(), v.end(), [](int x) { return x < 0; });
bool noneZero = std::none_of(v.begin(), v.end(), [](int x) { return x == 0; });
```

### 排列与集合操作

```cpp
std::next_permutation(v.begin(), v.end());   // 下一个字典序
std::prev_permutation(v.begin(), v.end());

std::set<int> a = {1, 2, 3}, b = {2, 3, 4};
std::vector<int> result;
std::set_intersection(a.begin(), a.end(), b.begin(), b.end(),
                      std::back_inserter(result));
```

## 数值算法（`<numeric>`）

```cpp
#include <numeric>

int sum = std::reduce(v.begin(), v.end());   // C++17，可并行，无 guaranteed 顺序
std::partial_sum(v.begin(), v.end(), dst.begin());   // 前缀和
std::adjacent_difference(v.begin(), v.end(), dst.begin());
std::iota(v.begin(), v.end(), 0);   // 0, 1, 2, ...
std::inner_product(a.begin(), a.end(), b.begin(), 0);  // 点积
```

| | `accumulate` | `reduce` (C++17) |
|:---|:---|:---|
| 顺序 | 保证从左到右 | 无顺序保证（可并行） |
| 自定义操作 | 支持 | 支持 |
| 浮点累加 | 确定性 | 可能因并行顺序不同 |

## 迭代器适配器

### insert_iterator

```cpp
std::vector<int> src = {1, 2, 3};
std::vector<int> dst;

std::copy(src.begin(), src.end(), std::back_inserter(dst));
// 等价于 for (x : src) dst.push_back(x);

std::list<int> lst;
std::copy(src.begin(), src.end(), std::front_inserter(lst));  // push_front

std::set<int> s;
std::copy(src.begin(), src.end(), std::inserter(s, s.end()));  // insert
```

### stream iterator

```cpp
// 从 cin 读入直到 EOF
std::vector<int> v(std::istream_iterator<int>(std::cin),
                   std::istream_iterator<int>());

// 输出到 cout，空格分隔
std::copy(v.begin(), v.end(),
          std::ostream_iterator<int>(std::cout, " "));
```

**C 对比**：类似 `fscanf`/`fprintf` 循环，但类型安全且可组合。

### reverse / move 迭代器

```cpp
std::vector<int> v = {1, 2, 3};
std::copy(v.rbegin(), v.rend(), std::ostream_iterator<int>(std::cout, " "));

std::vector<std::string> src = {"a", "b", "c"};
std::vector<std::string> dst;
std::move(src.begin(), src.end(), std::back_inserter(dst));
// src 中字符串被移走，处于有效但未指定状态
```

## 范围库（C++20）

惰性视图，不立即计算，可组合：

```cpp
#include <ranges>
namespace views = std::views;

std::vector<int> v = {1, 2, 3, 4, 5, 6};

auto result = v
    | views::filter([](int x) { return x % 2 == 0; })
    | views::transform([](int x) { return x * 2; });

for (int x : result) {
    std::cout << x << ' ';   // 4 8 12
}

// 管道风格
auto evens = views::iota(0, 100) | views::filter([](int x) { return x % 2 == 0; });
```

**与算法对比**：ranges 视图**不拥有**数据，算法通常**就地**或写入输出迭代器。

## 算法复杂度参考

| 算法 | 复杂度 | 前提 |
|:---|:---|:---|
| `find`, `count` | O(n) | — |
| `sort` | O(n log n) | 随机访问 |
| `stable_sort` | O(n log n) ~ O(n log² n) | 随机访问 |
| `binary_search` | O(log n) | 有序 + 随机访问 |
| `lower_bound` | O(log n) | 有序 + 随机访问 |
| `merge` | O(n + m) | 两个有序序列 |
| `set_union` 等 | O(n + m) | 有序 |
| `nth_element` | O(n) 平均 | 随机访问 |
| `make_heap` | O(n) | 随机访问 |
| `push_heap` / `pop_heap` | O(log n) | — |

## 常见错误与陷阱

### 1. 对无序容器用 binary_search

```cpp
std::vector<int> v = {3, 1, 4};
std::binary_search(v.begin(), v.end(), 3);   // 结果不可靠！
```

**原因**：二分查找要求**随机访问 + 有序**。**修复**：先 `sort`，或用 `find` O(n)。

### 2. 迭代器失效后继续使用

```cpp
auto it = std::find(v.begin(), v.end(), 3);
v.push_back(99);          // 可能使 it 失效
if (it != v.end()) *it = 0;   // 未定义行为
```

**原因**：`vector` 扩容或插入删除会使迭代器失效。**修复**：在可能修改容器前完成操作，或重新获取迭代器。

### 3. 比较函数不满足严格弱序

见排序一节。**原因**：`sort` 内部假设 `<` 形成严格弱序，违反则未定义行为。

### 4. 对 list/map 用 std::sort

```cpp
std::list<int> lst = {3, 1, 4};
// std::sort(lst.begin(), lst.end());   // 编译错误！list 迭代器非随机访问
lst.sort();   // 成员函数，链表归并排序 O(n log n)
```

**原因**：`std::sort` 需要随机访问（通常用 introsort）。**修复**：`list::sort` 或拷贝到 `vector` 排序。

### 5. copy 目标空间不足

```cpp
std::vector<int> src = {1, 2, 3};
std::vector<int> dst(1);   // 只有 1 个元素
std::copy(src.begin(), src.end(), dst.begin());   // 越界写入！
```

**修复**：`dst.resize(src.size())` 或用 `back_inserter(dst)`。

### 6. remove 忘记 erase

```cpp
std::remove(v.begin(), v.end(), 3);   // 只移动，不缩短 size
// v 的 size 不变，末尾可能是垃圾值
```

**原因**：`remove` 是为**无法 erase** 的 C 数组设计的惯用法。**修复**：`v.erase(...)`.

## 学习要点总结

1. 迭代器是算法与容器的**桥梁**，理解类别决定能用哪些算法
2. 删除元素用 **erase-remove** 惯用法（C++20 用 `std::erase`）
3. `binary_search`、`lower_bound` 等要求**有序 + 随机访问**
4. 优先 STL 算法而非手写循环——更清晰、更少 bug、编译器可优化
5. 修改容器时注意**迭代器失效**，尤其 `vector`
6. C++20 **ranges** 提供惰性可组合视图，适合函数式风格数据处理
