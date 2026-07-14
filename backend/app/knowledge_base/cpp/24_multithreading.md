# C++ 多线程

## 为什么需要多线程

现代 CPU 多为多核，单线程程序无法充分利用硬件。多线程用于：

- **并行计算**：分块处理数据、矩阵运算
- **并发 I/O**：网络请求、文件读写与计算重叠
- **响应性**：GUI 主线程保持响应，后台线程处理耗时任务
- **流水线**：生产者-消费者、任务队列

C++11 起标准库提供 `<thread>`、`<mutex>`、`<atomic>`、`<future>` 等，无需依赖平台 API（但底层仍由 OS 实现）。

## 线程基础

```cpp
#include <thread>
#include <iostream>

void worker(int id) {
    std::cout << "Thread " << id << " running\n";
}

int main() {
    std::thread t1(worker, 1);
    std::thread t2([]() {
        std::cout << "Lambda thread\n";
    });

    t1.join();   // 等待 t1 结束
    t2.join();
    return 0;
}
```

**必须**对 `std::thread` 调用 `join()` 或 `detach()` 之一，否则析构时调用 `std::terminate()`。

| 操作 | 含义 |
|:---|:---|
| `join()` | 阻塞直到线程结束，回收资源 |
| `detach()` | 分离线程，主线程不再等待（线程在后台独立运行） |

**detach 风险**：若线程仍访问已销毁的局部变量 → 未定义行为。优先 `join()`。

### 传递参数

```cpp
void process(std::string data);   // 按值接收，避免悬空引用

std::thread t(process, std::move(data));   // 移动传递

// 错误：传递引用给局部变量
int x = 42;
std::thread t2([&x]() { std::cout << x; });
t2.detach();   // main 可能先结束，x 已销毁
```

### thread 不可拷贝

```cpp
std::thread t1(worker);
// std::thread t2 = t1;   // 错误：不可拷贝
std::thread t2 = std::move(t1);   // 可移动
```

## C++20 jthread 与 stop_token

```cpp
#include <thread>
#include <stop_token>

void worker(std::stop_token st) {
    while (!st.stop_requested()) {
        // 工作...
    }
}

int main() {
    std::jthread t(worker);   // 析构时自动 request_stop + join
    // ...
}   // 离开作用域自动 join
```

`std::jthread` 析构时自动请求停止并 join，减少忘记 join 的错误。

## 互斥与锁

### mutex 基本用法

```cpp
#include <mutex>

std::mutex mtx;
int sharedCounter = 0;

void incrementUnsafe() {
    for (int i = 0; i < 100000; ++i) {
        mtx.lock();
        ++sharedCounter;
        mtx.unlock();   // 若中间抛异常，可能永不 unlock
    }
}
```

### lock_guard（RAII，推荐）

```cpp
void incrementSafe() {
    for (int i = 0; i < 100000; ++i) {
        std::lock_guard<std::mutex> lock(mtx);
        ++sharedCounter;
    }   // 析构时自动 unlock，异常安全
}
```

### unique_lock（更灵活）

```cpp
std::unique_lock<std::mutex> lock(mtx);
lock.unlock();
doSomethingWithoutLock();
lock.lock();

// 配合条件变量（必须 unique_lock）
std::condition_variable cv;
cv.wait(lock, [] { return dataReady; });
```

### scoped_lock（C++17，多锁）

```cpp
std::mutex m1, m2;

void transfer() {
    std::scoped_lock lock(m1, m2);   // 等价于 std::lock(m1, m2)，避免死锁
    // 同时持有两把锁
}
```

### shared_mutex（C++17，读写锁）

```cpp
#include <shared_mutex>

std::shared_mutex rwMtx;
std::map<int, std::string> cache;

std::string read(int key) {
    std::shared_lock lock(rwMtx);   // 多读共享
    return cache.at(key);
}

void write(int key, std::string val) {
    std::unique_lock lock(rwMtx);   // 写独占
    cache[key] = std::move(val);
}
```

读多写少场景可提升性能。

## 条件变量

```cpp
#include <condition_variable>
#include <mutex>
#include <queue>

std::mutex mtx;
std::condition_variable cv;
std::queue<int> queue;
bool done = false;

void producer() {
    for (int i = 0; i < 10; ++i) {
        {
            std::lock_guard lock(mtx);
            queue.push(i);
        }
        cv.notify_one();
    }
    {
        std::lock_guard lock(mtx);
        done = true;
    }
    cv.notify_all();
}

void consumer() {
    std::unique_lock lock(mtx);
    while (true) {
        cv.wait(lock, [&] { return !queue.empty() || done; });
        if (queue.empty() && done) break;
        int val = queue.front();
        queue.pop();
        lock.unlock();
        // 处理 val...
        lock.lock();
    }
}
```

**注意**：
- `wait` 可能**虚假唤醒**，始终用谓词或循环检查条件
- 修改共享状态后再 `notify_one` / `notify_all`
- 条件变量必须与 `unique_lock` 配合

## atomic 原子操作

无锁原子操作，适合简单计数器、标志位：

```cpp
#include <atomic>

std::atomic<int> counter{0};
std::atomic<bool> ready{false};

void incrementAtomic() {
    for (int i = 0; i < 100000; ++i) {
        ++counter;   // 原子操作，线程安全
    }
}

void producerAtomic() {
    // 准备数据...
    ready.store(true, std::memory_order_release);
}

void consumerAtomic() {
    while (!ready.load(std::memory_order_acquire)) {
        std::this_thread::yield();
    }
    // 消费数据...
}
```

| 操作 | 说明 |
|:---|:---|
| `load()` / `store(v)` | 读 / 写 |
| `fetch_add(n)` | 原子加，返回旧值 |
| `compare_exchange_weak/strong` | CAS（比较并交换） |
| `exchange(v)` | 交换并返回旧值 |

### 内存序（简要）

| 顺序 | 用途 |
|:---|:---|
| `memory_order_relaxed` | 仅保证原子性，无顺序约束 |
| `memory_order_acquire` | 读端，看到 release 之前的写入 |
| `memory_order_release` | 写端，之前的写入对消费者可见 |
| `memory_order_seq_cst` | 默认，最强顺序，最易理解 |

初学者用默认 `seq_cst` 即可；性能关键路径再考虑放宽顺序。

## 异步任务

### std::async 与 future

```cpp
#include <future>

auto future = std::async(std::launch::async, []() {
    // 耗时计算
    return 42;
});
int result = future.get();   // 阻塞等待结果

// 延迟启动
auto lazy = std::async(std::launch::deferred, compute);
int val = lazy.get();   // 此时才在调用线程执行
```

**注意**：`std::async` 的线程池行为由实现定义，不保证一定创建新线程。

### promise / future 手动传值

```cpp
std::promise<int> prom;
auto fut = prom.get_future();

std::thread t([&prom]() {
    prom.set_value(100);
    // 或 prom.set_exception(std::make_exception_ptr(...));
});

int val = fut.get();
t.join();
```

### packaged_task

```cpp
std::packaged_task<int(int, int)> task([](int a, int b) { return a + b; });
auto fut = task.get_future();

std::thread t(std::move(task), 3, 4);
std::cout << fut.get() << "\n";   // 7
t.join();
```

## thread_local

```cpp
thread_local int tlsCounter = 0;

void worker() {
    ++tlsCounter;   // 每个线程有独立副本
}
```

适合线程私有缓存、随机数生成器状态等，避免锁竞争。

## 线程池概念

标准库无内置线程池，常用第三方库（Intel TBB、BS::thread_pool）或自行实现：

```cpp
#include <queue>
#include <functional>
#include <thread>
#include <mutex>
#include <condition_variable>
#include <vector>

class ThreadPool {
    std::vector<std::thread> workers;
    std::queue<std::function<void()>> tasks;
    std::mutex queueMtx;
    std::condition_variable taskCv;
    bool stop = false;

public:
    explicit ThreadPool(std::size_t n) {
        for (std::size_t i = 0; i < n; ++i) {
            workers.emplace_back([this] {
                while (true) {
                    std::function<void()> task;
                    {
                        std::unique_lock lock(queueMtx);
                        taskCv.wait(lock, [this] {
                            return stop || !tasks.empty();
                        });
                        if (stop && tasks.empty()) return;
                        task = std::move(tasks.front());
                        tasks.pop();
                    }
                    task();
                }
            });
        }
    }

    template<typename F>
    void enqueue(F&& f) {
        {
            std::lock_guard lock(queueMtx);
            tasks.emplace(std::forward<F>(f));
        }
        taskCv.notify_one();
    }

    ~ThreadPool() {
        {
            std::lock_guard lock(queueMtx);
            stop = true;
        }
        taskCv.notify_all();
        for (auto& w : workers) w.join();
    }
};
```

## 并行算法（C++17）

```cpp
#include <algorithm>
#include <execution>
#include <vector>

std::vector<int> v(1'000'000);
std::sort(std::execution::par, v.begin(), v.end());   // 可能并行
std::for_each(std::execution::par_unseq, v.begin(), v.end(), [](int& x) {
    x *= 2;
});
```

需要链接 TBB 或编译器支持的并行后端（因实现而异）。

## 死锁预防

```cpp
// 错误：两个线程以不同顺序加锁
// Thread 1: lock(m1); lock(m2);
// Thread 2: lock(m2); lock(m1);  → 死锁

// 修复 1：固定加锁顺序
// 修复 2：std::lock 同时加锁
std::lock(m1, m2);
std::lock_guard<std::mutex> l1(m1, std::adopt_lock);
std::lock_guard<std::mutex> l2(m2, std::adopt_lock);

// 修复 3：C++17 scoped_lock
std::scoped_lock lock(m1, m2);
```

**其他原则**：
- 持锁时间尽量短
- 避免在持锁时调用未知代码（回调、用户代码）
- 考虑无锁设计或无共享设计

## 数据竞争

多个线程同时访问同一内存，至少一个是写，且无同步 → **未定义行为**。

```cpp
int x = 0;
// 两个线程同时 x++ 无同步 → 数据竞争
```

**避免方式**：
- `mutex` 保护共享数据
- `atomic` 用于简单类型
- 不可变共享（只读）
- 消息传递代替共享内存

## 常见错误

### 1. 忘记 join/detach

```cpp
void func() {
    std::thread t(worker);
}   // 析构时 std::terminate
```

### 2. 捕获局部变量引用后 detach

```cpp
void bad() {
    int x = 42;
    std::thread t([&x]() { std::cout << x; });
    t.detach();   // x 可能已销毁
}
```

按值捕获或确保线程在变量生命周期内 join。

### 3. 持锁调用未知代码

在锁内调用可能再次加锁的回调 → 死锁。先 unlock 再调用。

### 4. 过度细粒度锁

锁竞争严重，性能下降。考虑合并临界区、读写锁或无共享设计。

### 5. 误用 volatile

`volatile` **不**提供线程同步，多线程用 `atomic` 或 `mutex`。

### 6. 条件变量丢失唤醒

在持有锁时检查条件并 wait，先改状态再 notify；或使用 C++20 的 `std::atomic` + wait/notify。

## 学习要点总结

1. 线程必须 `join` 或 `detach`；优先 `join`，C++20 可用 `jthread`
2. 共享数据用 `mutex` + `lock_guard`/`scoped_lock`，简单计数用 `atomic`
3. 条件变量配合 `unique_lock` 和谓词，防止虚假唤醒
4. `std::async` / `future` / `promise` 简化异步结果获取
5. 固定加锁顺序、`std::lock`/`scoped_lock` 预防死锁
6. 数据竞争是 UB，必须显式同步或避免共享
7. 无共享设计（消息队列、任务分发）往往比细粒度锁更简单可靠
