# C++ 字符串 std::string

## 字符串的本质

### C 语言视角：以 `\0` 结尾的字符序列

C 语言没有独立的字符串类型，字符串是**以空字符 `\0` 结尾的连续字符存储**：

```c
char str1[] = "Hello";    // 栈上数组，6 字节（含 '\0'），可修改
char *str2 = "Hello";     // 指针指向只读数据段，不可修改内容
```

程序员必须手动追踪长度、保证终止符、分配/释放内存——这是 C 字符串 bug 的主要来源。

### C++ 视角：带长度信息的字符串对象

`std::string` 是一个**类类型**，内部同时维护**字符数据**和**长度/容量**信息：

```cpp
#include <string>

std::string s = "Hello";
// s 内部大致等价于（概念模型，非标准实现）：
//   char* data_   → 指向字符存储
//   size_t size_  → 当前字符数（不含 '\0'）
//   size_t cap_   → 已分配容量
```

**关键区别**：`std::string` 知道自身长度，不需要扫描 `\0` 来确定 `size()`；与 C 字符串互操作时仍保证 `c_str()` 返回以 `\0` 结尾的 C 风格字符串。

| 特性 | C `char*` / `char[]` | C++ `std::string` |
|:---|:---|:---|
| 类型 | 指针或数组 | 完整类类型 |
| 长度 | 需 `strlen`，O(n) | `size()`，O(1) |
| 内存管理 | 手动（栈/堆/静态） | RAII 自动管理 |
| 拼接 | `strcat`（易溢出） | `+` / `+=`（自动扩容） |
| 比较 | `strcmp` | `==` / `compare` |
| 安全性 | 低（无边界检查） | 较高（`at()` 有检查） |
| 可修改性 | 取决于声明方式 | 始终可修改 |

## 内存布局与 SSO（小字符串优化）

### 典型堆分配模型

当字符串较长时，`std::string` 通常在堆上分配字符缓冲区：

```
std::string s = "Hello, World!";   // 假设超过 SSO 阈值

对象内存（栈上，约 24~32 字节）:
┌─────────────────────────────────────┐
│ data_  ──────────→  堆内存           │
│ size_  = 13                          │     ┌───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┬───┐
│ cap_   = 15 (或更大)                 │     │ H │ e │ l │ l │ o │ , │   │ W │ o │ r │ l │ d │ ! │\0 │
└─────────────────────────────────────┘     └───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┴───┘
```

### SSO（Small String Optimization）

多数标准库实现对**短字符串**直接在 `string` 对象内部存储字符，**不触发堆分配**：

```
短字符串 s = "Hi"（SSO 启用时）:

对象内存（全部在栈上）:
┌─────────────────────────────────────┐
│ [ H ][ i ][ \0 ] ... (内联缓冲区)    │
│ size_ = 2                            │
│ cap_  = 内联容量（如 15 或 22）       │
└─────────────────────────────────────┘
         ↑ 无堆指针，无额外 malloc
```

**深层理解**：
- SSO 使短字符串操作极快，但 `sizeof(std::string)` 比 `sizeof(char*)` 大得多
- 不同编译器/标准库的 SSO 阈值不同（常见 15~22 字节）
- 移动 `string` 时，若源是 SSO 字符串，可能仍须拷贝（无法"窃取"内联缓冲区）

### 生命周期图

```cpp
void func() {
    std::string local = "temp";
    const char* p = local.c_str();   // p 指向 local 内部数据
}   // local 析构，p 变为悬空指针！

// 正确：在 string 存活期间使用 c_str()
std::string s = "Hello";
process(s.c_str());   // s 仍存活，安全
```

```
时间线:
  构造 s ──→ s.c_str() 有效 ──→ s 被修改/析构 ──→ c_str() 指针失效
                                    ↑
                          任何 insert/append/+= 都可能使旧 c_str() 失效
```

## 构造与初始化

```cpp
std::string empty;                          // 空字符串 ""
std::string s1 = "Hello";                   // 从字面量
std::string s2("World", 3);                 // "Wor"（前 3 个字符）
std::string s3(5, 'a');                     // "aaaaa"
std::string s4(s1, 1, 3);                   // 子串 "ell"
std::string s5(s1.begin() + 1, s1.end());   // 迭代器范围
std::string s6 = s1 + ", " + s2;            // 拼接
```

### C vs C++ 初始化对比

```c
// C：必须关心缓冲区大小
char buf[20];
strncpy(buf, "Hello", sizeof(buf) - 1);
buf[sizeof(buf) - 1] = '\0';
```

```cpp
// C++：无需预设大小
std::string s = "Hello";   // 自动分配正确大小
```

## 基本操作

```cpp
std::string s = "Hello";

s.size();       // 5，与 length() 完全等价
s.empty();      // false
s.capacity();   // 已分配容量（可能 >= size）

s[0];           // 'H'，不检查边界，越界未定义行为
s.at(0);        // 'H'，越界抛 std::out_of_range
s.front();      // 'H'（C++11）
s.back();       // 'o'（C++11）

s += " World";  // 修改自身
s.append("!");
s.push_back('?');
s.pop_back();
s.clear();      // 清空，size=0，通常不释放 capacity
s.shrink_to_fit();  // 请求释放多余 capacity（C++11，非强制）
```

**防御性编程**：对外部输入或不可信索引，用 `at()` 而非 `[]`：

```cpp
try {
    char c = s.at(index);
} catch (const std::out_of_range& e) {
    // 处理越界
}
```

## 比较与查找

```cpp
std::string a = "apple", b = "banana";

a == b;              // false，比较内容（C 中 == 比较指针地址！）
a < b;               // true，字典序
a.compare(b);        // < 0 表示 a < b

auto pos = a.find("pp");              // 1
auto pos2 = a.rfind("p");             // 2，从右查找
auto pos3 = a.find_first_of("aeiou"); // 0，第一个元音
auto pos4 = a.find_last_of("xyz");    // npos 表示未找到

// C++20
a.starts_with("app");   // true
a.ends_with("le");      // true

// C++23
a.contains("pl");       // true
```

**C 常见错误对比**：

```c
if (str1 == str2) { }     // 错误！比较地址
if (strcmp(str1, str2) == 0) { }  // 正确
```

```cpp
if (s1 == s2) { }         // 正确！直接比较内容
```

## 子串与修改

```cpp
std::string s = "Hello, World!";

s.substr(7, 5);              // "World"（返回新 string，拷贝）
s.replace(7, 5, "C++");      // "Hello, C++!"
s.insert(5, " beautiful");   // 在索引 5 插入
s.erase(5, 10);                // 删除从索引 5 开始的 10 个字符
s.resize(20, '-');             // 扩展到 20 字符，新位置填 '-'
```

**注意**：`substr` 返回**新对象**（拷贝），频繁使用考虑 `string_view` 避免分配。

## 与 C 字符串互操作

```cpp
std::string s = "Hello";

const char* cstr = s.c_str();    // 保证以 '\0' 结尾
const char* data = s.data();     // C++17 起与 c_str() 等价（均保证 '\0'）

// 从 C 字符串构造
std::string s2(cstr);
std::string s3(cstr, strlen(cstr));   // 指定长度，可含 '\0'

// 与 printf 配合
printf("%s\n", s.c_str());

// 写入 C 缓冲区
char buf[64];
snprintf(buf, sizeof(buf), "%s", s.c_str());
```

### 常见互操作陷阱

```cpp
// 危险：临时对象的 c_str()
const char* p = (s1 + s2).c_str();   // s1+s2 是临时 string，语句结束后销毁，p 悬空

// 危险：修改 string 后仍使用旧 c_str()
const char* p = s.c_str();
s += " more";    // 可能重新分配，p 失效
// printf("%s", p);  // 未定义行为
```

## 输入输出

```cpp
std::string name;

std::cin >> name;                // 读到空白符为止（不含空格）
std::getline(std::cin, name);    // 读整行（推荐）
std::getline(std::cin, name, ',');  // 以 ',' 为分隔符

std::cout << s << std::endl;
```

**防御性编程**：读取后检查流状态：

```cpp
if (!std::getline(std::cin, line)) {
    if (std::cin.eof()) { /* EOF */ }
    else { std::cin.clear(); /* 处理错误 */ }
}
```

## 数值转换（C++11）

```cpp
#include <string>

// 字符串 → 数值（失败抛异常）
int n = std::stoi("42");
double d = std::stod("3.14");
long long ll = std::stoll("9223372036854775807");

// 带位置信息
size_t pos;
int val = std::stoi("123abc", &pos);   // val=123, pos=3

// 数值 → 字符串
std::string s1 = std::to_string(42);
std::string s2 = std::to_string(3.14);
```

**对比 C 的 `atoi`**：`stoi` 解析失败抛 `std::invalid_argument`，溢出抛 `std::out_of_range`；`atoi` 失败时返回 0 且无明确错误指示。

**防御性编程**：

```cpp
try {
    int n = std::stoi(input);
} catch (const std::exception& e) {
    // 处理非法输入
}
```

## std::string_view（C++17）

`string_view` 是**非拥有的只读字符串视图**，包含 `(指针, 长度)` 二元组：

```cpp
#include <string_view>

void print(std::string_view sv) {   // 可接受 string、字面量、char*
    std::cout << sv << std::endl;
}

print("Hello");           // 不拷贝
print(std::string("Hi")); // 不拷贝，只引用
print(s.substr(0, 3));    // 危险！substr 返回临时 string，表达式结束后 view 悬空
```

**适用场景**：
- 函数参数只读访问字符串 → 优先 `string_view`
- 需要拥有/修改字符串 → 用 `std::string`
- 需要以 `\0` 结尾保证 → 用 `std::string` 或确保 view 来源可靠

## 编码与 Unicode

```cpp
std::string utf8 = "中文";   // UTF-8 编码
utf8.size();                  // 字节数（中文每字通常 3 字节），不是字符数！

// C++20
#include <locale>
// 处理 Unicode 需 u8string、codecvt 或第三方库（如 ICU）
```

**深层理解**：`std::string` 是**字节容器**，不感知 Unicode 字符边界。与 C 一样，`size()` 返回字节数而非"字符"数。

## 性能优化

```cpp
std::string result;
result.reserve(1000);   // 预分配，避免多次 realloc

for (int i = 0; i < 10000; ++i) {
    result += std::to_string(i);   // O(n) 均摊，因 reserve
}

// 错误：O(n²)
for (int i = 0; i < 10000; ++i) {
    result = result + std::to_string(i);   // 每次创建新 string
}

// C++20 格式化
#include <format>
std::string msg = std::format("{} is {} years old", name, age);
```

## 防御性编程模式

### 1. 优先 string 而非 char*

```cpp
// 不推荐
void process(const char* s);   // 不知道是否为空，不知道长度

// 推荐
void process(std::string_view s);   // 明确长度，可接受多种来源
void process(const std::string& s); // 需要保证对象存活时
```

### 2. 安全复制到 C 缓冲区

```cpp
void copy_to_buffer(const std::string& s, char* buf, size_t buf_size) {
    if (buf_size == 0) return;
    size_t n = std::min(s.size(), buf_size - 1);
    std::copy_n(s.data(), n, buf);
    buf[n] = '\0';   // 保证终止符
}
```

### 3. 避免不必要的拷贝

```cpp
// 传 const 引用
void foo(const std::string& s);

// 只读且兼容多种来源
void foo(std::string_view sv);

// 需要拷贝时显式
void foo(std::string s);   // 按值 = 调用者知道会拷贝
```

## 常见错误

### 1. 使用已失效的 c_str()

```cpp
const char* p = (s1 + s2).c_str();
// 原因：临时 string 在完整表达式结束后析构，p 指向已释放内存
```

### 2. 用 + 拼接导致 O(n²)

```cpp
std::string s;
for (int i = 0; i < 10000; ++i)
    s = s + std::to_string(i);
// 原因：每次 + 创建新 string 并拷贝全部内容
// 修复：s += ... 并 reserve
```

### 3. string_view 指向临时对象

```cpp
std::string_view sv = std::string("temp");
// 原因：临时 string 销毁后 view 悬空
// 修复：延长 string 生命周期，或直接绑定到字面量
```

### 4. 混淆字节数与字符数

```cpp
std::string s = "你好";
s.size();   // 6（UTF-8 每字 3 字节），不是 2
// 原因：string 不感知 Unicode 码点
```

### 5. 越界访问用 operator[]

```cpp
char c = s[s.size()];   // 未定义行为
// 原因：[] 不检查边界
// 修复：用 at() 或先检查 index < s.size()
```

### 6. 在 C API 回调中捕获 string 的 c_str()

```cpp
// 若回调异步执行，string 可能已销毁
register_callback(s.c_str());   // 危险，除非保证 s 生命周期覆盖回调
```

## 学习要点总结

1. `std::string` 是带长度与容量的 RAII 字符串类，比 C 字符串更安全、更易用
2. 短字符串可能使用 SSO，数据内联在对象内，无堆分配
3. `c_str()` / `data()` 指针在 string 修改或销毁后失效，勿长期保存
4. 只读参数优先 `string_view`（C++17），避免不必要拷贝
5. 大量拼接用 `+=` + `reserve`，避免 `s = s + x` 的 O(n²)
6. `size()` 返回字节数，处理 UTF-8 多字节字符需专门方案
7. 与 C 互操作用 `c_str()`，但注意生命周期；比较内容用 `==` 而非指针比较
