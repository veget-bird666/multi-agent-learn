# 信号量与管程

## 信号量 (Semaphore)

信号量是一个整型变量 + 两个**原子操作**：

| 操作 | 名称 | 行为 |
|:---|:---|:---|
| P() / wait() | Proberen（测试） | sem--，若 sem < 0 则阻塞 |
| V() / signal() | Verhogen（增加） | sem++，若 sem ≤ 0 则唤醒一个等待者 |

### 两种信号量

- **二进制信号量**：取值 0 或 1（等价于互斥锁）
- **计数信号量**：取值 ≥ 0（用于资源计数）

### 用途1：互斥

```c
Semaphore *mutex = new Semaphore(1);

mutex->P();    // 进入临界区
// ... 共享数据操作 ...
mutex->V();    // 离开临界区
```

### 用途2：条件同步

```c
Semaphore *condition = new Semaphore(0);

// 线程 A：等待条件
condition->P();  // 阻塞，直到 B 发出信号

// 线程 B：条件满足
condition->V();  // 唤醒 A
```

## 经典问题：生产者-消费者

有界缓冲区，容量为 n：

```cpp
class BoundedBuffer {
    Semaphore *mutex = new Semaphore(1);       // 互斥
    Semaphore *fullBuffers = new Semaphore(0); // 已填充数
    Semaphore *emptyBuffers = new Semaphore(n);// 空位数
};

void Deposit(char c) {
    emptyBuffers->P();  // 等待空位
    mutex->P();
    Add c to buffer;
    mutex->V();
    fullBuffers->V();   // 通知消费者
}

void Remove(char &c) {
    fullBuffers->P();   // 等待数据
    mutex->P();
    Remove c from buffer;
    mutex->V();
    emptyBuffers->V();  // 通知生产者
}
```

**三个约束，三个信号量**：
1. 互斥访问缓冲区 → `mutex`
2. 缓冲区空时消费者等待 → `fullBuffers`
3. 缓冲区满时生产者等待 → `emptyBuffers`

### 信号量的陷阱

- P/V 顺序错误 → 死锁
- 忘记 V() → 永久阻塞
- 难以推理复杂同步逻辑

## 管程 (Monitor)

**目的**：将互斥和条件同步分离，降低编程难度。

### 管程结构

```
┌─────────────────────────────┐
│  Lock（保证互斥）             │
│  共享数据                    │
│  Condition Variable(s)       │
│    .Wait()  → 释放锁并睡眠   │
│    .Signal() → 唤醒等待者    │
│  方法1(), 方法2(), ...       │
└─────────────────────────────┘
同一时刻最多一个线程在管程内
```

### 管程实现生产者-消费者

```cpp
class BoundedBuffer {
    Lock lock;
    int count = 0;
    Condition notFull, notEmpty;
};

void Deposit(char c) {
    lock.Acquire();
    while (count == n)
        notFull.Wait(&lock);  // 释放锁，睡眠
    Add c to buffer;
    count++;
    notEmpty.Signal();
    lock.Release();
}

void Remove(char &c) {
    lock.Acquire();
    while (count == 0)
        notEmpty.Wait(&lock);
    Remove c from buffer;
    count--;
    notFull.Signal();
    lock.Release();
}
```

比信号量版本更清晰——**互斥由 Lock 保证，等待条件由 Condition 表达**。

## 经典同步问题

### 读者-写者问题

- **读者**：只读，可多个同时读
- **写者**：读写，同一时刻只允许一个

**读者优先**：有读者活跃时，新读者直接进入，写者可能饥饿

**写者优先**：写者就绪时优先执行，读者可能饥饿

### 哲学家就餐问题

5 个哲学家围坐，5 根筷子，每人需要左右两根才能就餐。

```c
#define N 5
semaphore fork[N] = {1,1,1,1,1};  // 每根筷子一个信号量
semaphore mutex = 1;

void philosopher(int i) {
    while (TRUE) {
        think();
        take_forks(i);   // 取左右筷子
        eat();
        put_forks(i);    // 放下筷子
    }
}
```

朴素方案（先左后右）可能**死锁**——所有人同时拿起左筷子。

**解决方案**：
- 限制同时就餐人数 ≤ 4
- 奇数哲学家先左后右，偶数先右后左
- 使用管程 + 状态检测

## 同步结构总结

| 结构 | 用途 |
|:---|:---|
| Lock | 互斥 |
| Condition Variable | 条件同步 |
| Semaphore | 互斥 + 条件同步（更底层） |

## 学习要点总结

1. 信号量 P/V 是经典的同步原语，但容易用错
2. 生产者-消费者是有界缓冲区的标准模型
3. 管程将互斥和条件等待封装在高层抽象中，更易用
4. 读者-写者和哲学家就餐是检验同步方案的经典问题
5. 并行程序调试难——设计严格的同步策略比事后调试更重要
