# C语言循环结构

## 三种循环对比

| 循环 | 适用场景 | 特点 |
|:---|:---|:---|
| `for` | 已知迭代次数 | 初始化、条件、更新集中在一行 |
| `while` | 未知迭代次数 | 先判断后执行 |
| `do-while` | 至少执行一次 | 先执行后判断 |

## for 循环

### 标准形式

```c
for (初始化; 条件; 更新) {
    // 循环体
}
```

执行顺序：**初始化 → 条件检查 → 循环体 → 更新 → 条件检查 → ...**

### 逗号运算符在 for 中的应用

```c
for (int i = 0, j = 10; i < j; i++, j--) {
    printf("i=%d, j=%d\n", i, j);
}
```

### 省略部分表达式

```c
int i = 0;
for (; i < 10; ) {    // 省略初始化和更新
    i++;
}

for (;;) {            // 无限循环，等价于 while (1)
    // ...
}
```

### for 循环的作用域（C99）

```c
for (int i = 0; i < 10; i++) { }
// i 在这里不可见，C99 特性

int i;
for (i = 0; i < 10; i++) { }
// i 在这里仍然可见
```

## while 循环

### 基本形式

```c
while (条件) {
    // 循环体
}
```

### 读取直到 EOF

```c
int c;
while ((c = getchar()) != EOF) {
    putchar(c);
}
```

**注意括号**：`c = getchar()` 的赋值必须在括号内，否则先比较再赋值：

```c
while (c = getchar() != EOF)   // 错误！等价于 c = (getchar() != EOF)，c 变成 0 或 1
```

## do-while 循环

```c
do {
    // 至少执行一次
} while (条件);
```

**注意分号**：`while` 后面必须有分号。

### 典型应用：菜单循环

```c
int choice;
do {
    printf("1. 选项一\n");
    printf("2. 选项二\n");
    printf("0. 退出\n");
    printf("请选择: ");
    scanf("%d", &choice);

    switch (choice) {
        case 1: /* ... */ break;
        case 2: /* ... */ break;
    }
} while (choice != 0);
```

## 循环控制语句

### break

立即终止**最内层**循环：

```c
for (int i = 0; i < 100; i++) {
    if (arr[i] == target) {
        index = i;
        break;   // 找到后立即退出
    }
}
```

### continue

跳过当前迭代，进入下一次：

```c
for (int i = 0; i < 100; i++) {
    if (arr[i] < 0) {
        continue;   // 跳过负数
    }
    process(arr[i]);
}
```

### goto

```c
for (int i = 0; i < 10; i++) {
    for (int j = 0; j < 10; j++) {
        if (error_condition) {
            goto cleanup;   // 跳出多层循环的唯一简洁方式
        }
    }
}

cleanup:
    free_resources();
    return -1;
```

**goto 的合理使用场景**：
- 跳出多层嵌套循环
- 统一的错误处理出口（资源释放）

**goto 的滥用场景**：
- 构造循环（用 while/for 替代）
- 跳转到前面的代码（ spaghetti code）

## 循环优化

### 循环展开

```c
// 原始
for (int i = 0; i < 100; i++) {
    sum += arr[i];
}

// 展开4次，减少循环开销
for (int i = 0; i < 100; i += 4) {
    sum += arr[i];
    sum += arr[i + 1];
    sum += arr[i + 2];
    sum += arr[i + 3];
}
```

现代编译器通常自动优化，手动展开需谨慎。

### 循环不变量外提

```c
// 低效
for (int i = 0; i < n; i++) {
    int len = strlen(str);   // 每次循环都计算，但 str 不变
    process(str, len);
}

// 高效
int len = strlen(str);       // 移到循环外
for (int i = 0; i < n; i++) {
    process(str, len);
}
```

## 常见错误

### 1. 边界错误

```c
int arr[10];
for (int i = 0; i <= 10; i++) {   // 错误！应该是 i < 10
    arr[i] = i;                     // arr[10] 越界！
}
```

**记忆口诀**：左闭右开 `[0, n)` 是最安全的模式。

### 2. 浮点数循环

```c
for (double d = 0.0; d != 1.0; d += 0.1) {
    // 可能永远不会结束！0.1 累加有误差
}

// 正确做法
for (int i = 0; i < 10; i++) {
    double d = i * 0.1;
}
```

### 3. 修改循环变量

```c
for (int i = 0; i < 10; i++) {
    if (some_condition) {
        i++;   // 危险！跳过下一个元素
    }
}
```

### 4. 空循环体

```c
while (getchar() != '\n');   // 分号在下一行，看起来像循环体是空语句
    ;                         // 实际循环体在这里

// 更好的写法
while (getchar() != '\n') {
    // 空循环体
}
```

## 嵌套循环

### 时间复杂度

```c
for (int i = 0; i < n; i++) {
    for (int j = 0; j < n; j++) {
        // O(n²)
    }
}

for (int i = 0; i < n; i++) {
    for (int j = i + 1; j < n; j++) {
        // 内层执行 n-1 + n-2 + ... + 1 = n(n-1)/2 次，仍是 O(n²)
    }
}
```

### 二维数组遍历

```c
int matrix[ROWS][COLS];

// 行优先（缓存友好）
for (int i = 0; i < ROWS; i++) {
    for (int j = 0; j < COLS; j++) {
        matrix[i][j] = i * j;   // 内存连续访问
    }
}

// 列优先（缓存不友好）
for (int j = 0; j < COLS; j++) {
    for (int i = 0; i < ROWS; i++) {
        matrix[i][j] = i * j;   // 跳跃式访问，缓存失效
    }
}
```

C语言数组是**行优先存储**，按行遍历有更好的缓存局部性。

## 学习要点总结

1. `for` 适合已知次数，`while` 适合未知次数，`do-while` 适合至少执行一次
2. 循环边界使用左闭右开 `[0, n)` 避免越界
3. 不要用浮点数作为循环变量
4. `break` 只跳出最内层循环，多层跳出考虑 `goto` 或重构
5. 二维数组遍历时按行优先以提高缓存命中率
