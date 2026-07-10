# C++ 内存管理

## 内存布局回顾

程序运行时，操作系统分配虚拟地址空间。C 与 C++ 共享同一底层模型：

```
高地址
┌──────────────────┐
│     栈区 (Stack)  │ ← 局部变量、函数参数，自动分配/释放，向下增长
│                  │
├──────────────────┤
│     堆区 (Heap)   │ ← new/malloc 分配，向上增长
│                  │
├──────────────────┤
│    数据段 (Data)   │ ← 全局/静态变量、字符串字面量
├──────────────────┤
│   代码段 (Text)    │ ← 机器指令，只读
└──────────────────┘
低地址
```

**栈 vs 堆**：

| 特性 | 栈 | 堆 |
|:---|:---|:---|
| 分配方式 | 自动（编译器） | 手动（`new`/`malloc`）或 RAII |
| 速度 | 极快 | 较慢 |
| 大小 | 有限（通常 1~8 MB） | 受物理内存+交换空间限制 |
| 生命周期 | 跟随作用域 | 程序员或智能指针控制 |
| 碎片 | 无 | 可能产生 |

```cpp
void func() {
    int x = 10;              // 栈
    int* p = new int(20);    // 堆
    delete p;                // 必须手动释放（或用智能指针）
}   // x 自动销毁
```

## C vs C++ 动态内存

| 操作 | C | C++ |
|:---|:---|:---|
| 分配 | `malloc` / `calloc` / `realloc` | `new` / `new[]` |
| 释放 | `free` | `delete` / `delete[]` |
| 构造 | 不调用构造函数 | 调用构造函数 |
| 类型 | 返回 `void*` | 返回 `T*` |
| 失败 | 返回 `NULL` | 抛 `std::bad_alloc`（默认） |
| 推荐 | C 库交互 | RAII + 智能指针 |

**绝对不要混用**：

```cpp
int* p = new int(42);
free(p);        // 未定义行为！

int* q = (int*)malloc(sizeof(int));
delete q;       // 未定义行为！
```

## new 与 delete

```cpp
// 单个对象
int* p = new int(42);       // 分配 + 构造
delete p;                   // 析构 + 释放

// 数组
int* arr = new int[10]{};   // 10 个 int，值初始化（全 0）
delete[] arr;               // 必须用 delete[]

// 配对规则
// new    ↔ delete
// new[]  ↔ delete[]
```

**delete[] 与 delete 混用的后果**：

```cpp
int* arr = new int[10];
delete arr;     // 未定义行为！只调用一次析构，内存可能泄漏或堆损坏
```

### new 的变体

```cpp
int* p1 = new int;          // 默认初始化（内置类型未定义）
int* p2 = new int();        // 值初始化（0）
int* p3 = new int(42);      // 直接初始化

// C++17：不抛异常的 new
int* p4 = new (std::nothrow) int(42);
if (!p4) { /* 分配失败 */ }
```

## RAII：资源获取即初始化

**RAII** 是 C++ 资源管理的核心：**资源的生命周期绑定到对象的生命周期**。

```cpp
{
    std::vector<int> v(1000);     // 构造时分配
    std::fstream file("data.txt"); // 构造时打开
    std::lock_guard<std::mutex> lock(m);  // 构造时加锁
}   // 离开作用域，析构函数自动释放所有资源
```

**深层理解**：
- 构造函数获取资源
- 析构函数释放资源
- 异常发生时栈展开（stack unwinding）仍会调用析构函数 → **异常安全**
- C 语言需手动 `free` + 每个 return 路径检查，C++ RAII 自动处理

**对比 C 的泄漏风险**：

```c
void leaky(void) {
    int *p = malloc(sizeof(int) * 100);
    if (error_condition) return;   // 忘记 free！
    free(p);
}
```

```cpp
void safe(void) {
    auto v = std::make_unique<int[]>(100);
    if (error_condition) return;   // 自动释放
}
```

## 智能指针

### std::unique_ptr（独占所有权）

```cpp
#include <memory>

auto p = std::make_unique<int>(42);
// std::unique_ptr<int> p(new int(42));  // 可以，但 make_unique 更安全（异常）

*p = 100;
auto p2 = std::move(p);   // 转移所有权
// p 现在为 nullptr
// *p;                     // 未定义行为！

auto arr = std::make_unique<int[]>(10);   // C++14 起支持数组
```

**特点**：
- 不可拷贝，只能移动
- 零开销抽象（与裸指针大小相同，无额外控制块）
- 默认 deleter 调用 `delete` 或 `delete[]`

**所有权转移图**：

```
move 前:  p ──→ [object]
move 后:  p ──→ nullptr
          p2 ──→ [object]
```

### std::shared_ptr（共享所有权）

```cpp
auto sp1 = std::make_shared<int>(42);
auto sp2 = sp1;              // 引用计数 +1
std::cout << sp1.use_count(); // 2

sp2.reset();                 // 计数 -1
// 计数为 0 时自动 delete
```

**内存布局**（典型实现）：

```
sp1, sp2 ──→ [控制块: refcount=2, weakcount=1] ──→ [int: 42]
             make_shared 可能将控制块与对象一次分配（更高效）
```

**注意**：
- 有引用计数原子操作开销
- 循环引用导致泄漏，需 `weak_ptr` 打破

### std::weak_ptr

```cpp
std::weak_ptr<int> wp = sp1;
if (auto locked = wp.lock()) {
    // 对象仍存在，locked 是 shared_ptr
    std::cout << *locked;
} else {
    // 对象已销毁
}
```

**典型场景**：打破 `shared_ptr` 循环引用、缓存观察。

### 循环引用与修复

```cpp
struct Node {
    std::shared_ptr<Node> next;
    std::shared_ptr<Node> prev;   // 双向 shared_ptr → 循环引用，永不释放
};

// 修复：弱引用一侧
struct NodeFixed {
    std::shared_ptr<NodeFixed> next;
    std::weak_ptr<NodeFixed> prev;   // 不增加 refcount
};
```

```
循环引用:
  A (ref=1) ──next──→ B (ref=1)
  A ←──prev── B
  外部引用消失后 A、B 互相持有，refcount 永不为 0
```

## 常见内存错误

### 1. 内存泄漏

```cpp
void leak() {
    int* p = new int(10);
    if (some_condition) return;   // 忘记 delete
    delete p;
}
// 原因：堆内存无引用后无法回收
// 检测：Valgrind、AddressSanitizer
```

### 2. 使用已释放内存（Use-after-free）

```cpp
int* p = new int(5);
delete p;
*p = 10;        // 未定义行为
// 原因：对象已销毁，内存可能已归还分配器或被复用
```

### 3. 双重释放（Double Free）

```cpp
delete p;
delete p;       // 未定义行为，可能破坏堆管理结构
// 修复：delete 后 p = nullptr
```

### 4. 越界访问

```cpp
int* arr = new int[10];
arr[10] = 0;    // 越界写入
delete[] arr;
```

### 5. delete 与 delete[] 混用

见上文 new/delete 章节。

### 6. 从 this 创建 shared_ptr

```cpp
class Bad {
public:
    std::shared_ptr<Bad> getPtr() {
        return std::shared_ptr<Bad>(this);   // 双重 delete！
    }
};

// 正确：继承 enable_shared_from_this
class Good : public std::enable_shared_from_this<Good> {
public:
    std::shared_ptr<Good> getPtr() {
        return shared_from_this();
    }
};
```

## 移动语义预览

```cpp
std::vector<int> create_large() {
    std::vector<int> v(1000000, 42);
    return v;   // RVO/NRVO 或移动，避免拷贝百万元素
}

auto v = create_large();
auto v2 = std::move(v);   // v 被"掏空"，资源转移给 v2
```

**资源转移图**：

```
move 前:  v ──→ [heap: 1M ints]
move 后:  v ──→ [empty]
          v2 ──→ [heap: 1M ints]
```

详见移动语义章节。

## 自定义删除器

```cpp
// unique_ptr 带自定义 deleter
auto deleter = [](FILE* f) { if (f) std::fclose(f); };
std::unique_ptr<FILE, decltype(deleter)> fp(fopen("data.txt", "r"), deleter);

// shared_ptr
std::shared_ptr<int> sp(new int(5), [](int* p) {
    std::cout << "custom delete\n";
    delete p;
});
```

**场景**：C API 资源（`FILE*`、`HANDLE`）、数组特殊释放、内存池回收。

## placement new（高级）

在**已分配内存**上构造对象，不分配新内存：

```cpp
alignas(int) char buffer[sizeof(int)];
int* p = new (buffer) int(42);   // 在 buffer 上构造
// ...
p->~int();   // 手动析构（不释放 buffer）
```

**用途**：内存池、嵌入式、标准容器 allocator、固定缓冲区。

**注意**：placement new 分配的内存不能用 `delete` 释放，只需显式调用析构函数。

## 与 C 内存函数互操作

```cpp
#include <cstdlib>

void* p = std::malloc(100);
if (p) {
    // 使用...
    std::free(p);
    p = nullptr;
}
```

**何时用 malloc/free**：
- 调用 C 库 API
- 需要 `realloc` 语义
- 与 C 代码共享所有权

**何时用 new/智能指针**：
- C++ 对象需要构造/析构
- 日常 C++ 代码

## 内存对齐

与 C 相同，硬件访问通常按字长对齐。C++17 提供：

```cpp
#include <memory>

void* p = std::aligned_alloc(64, 1024);   // 64 字节对齐
std::free(p);

// 或 alignas
struct alignas(64) CacheLine {
    char data[64];
};
```

未对齐访问在某些架构（ARM）会导致崩溃或性能下降。

## 防御性编程模式

### 1. 优先 make_unique / make_shared

```cpp
auto p = std::make_unique<Widget>(args);
// 避免 new 与智能指针构造之间的异常泄漏
```

### 2. 独占所有权默认 unique_ptr

```cpp
// 不需要共享时，不要用 shared_ptr（避免 refcount 开销和循环引用）
std::unique_ptr<Database> db;
```

### 3. 裸指针仅作观察者

```cpp
void process(Widget* w);   // 不拥有，不 delete
// 文档或命名约定：observer、view、raw 等
```

### 4. 容器替代 raw array

```cpp
std::vector<int> v(100);   // 而非 new int[100]
```

### 5. RAII 包装所有资源

文件、锁、socket、GDI 句柄等，全部用 RAII 类管理。

### 6. 检测工具

```bash
# Valgrind（Linux）
valgrind --leak-check=full ./program

# AddressSanitizer（编译选项）
# g++ -fsanitize=address -g program.cpp
```

## 常见错误原因汇总

| 错误 | 原因 | 修复 |
|:---|:---|:---|
| 泄漏 | 无 delete / 异常路径跳过 | 智能指针、RAII |
| use-after-free | delete 后继续使用 | delete 后置 nullptr；缩小指针作用域 |
| double free | 重复 delete 或混用所有权 | 单一 owner；智能指针 |
| 混用 new/free | 分配器不匹配 | 配对使用 |
| 循环引用 | shared_ptr 互相持有 | weak_ptr 打破环 |
| 过度 shared_ptr | 不需要共享 | 改用 unique_ptr |

## 学习要点总结

1. **RAII** 是 C++ 资源管理核心：构造获取，析构释放，异常安全
2. 独占所有权用 `unique_ptr`，共享用 `shared_ptr`，打破循环用 `weak_ptr`
3. 优先 `make_unique` / `make_shared`，避免裸 `new`/`delete`
4. `new[]` 必须配对 `delete[]`，且不可与 `free` 混用
5. 裸指针仅作非拥有观察者，所有权交给智能指针
6. C 的 `malloc`/`free` 仅在与 C 库交互时使用
7. 用 Valgrind / ASan 检测泄漏和内存错误
