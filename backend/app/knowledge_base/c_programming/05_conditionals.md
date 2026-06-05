# C语言条件语句

## if 语句的深层理解

### 语法结构

```c
if (表达式) {
    // 表达式为真（非0）时执行
} else if (另一个表达式) {
    // 上一个为假，这个为真时执行
} else {
    // 所有条件都不满足时执行
}
```

### 条件表达式的本质

C语言没有真正的布尔类型（C99前），条件判断基于**整数零值测试**：

```c
if (x) { }           // 等价于 if (x != 0)
if (!x) { }          // 等价于 if (x == 0)
if (ptr) { }         // 等价于 if (ptr != NULL)
if (a - b) { }       // 如果 a == b，结果为0，条件为假
```

**陷阱**：浮点数和指针的零值测试

```c
double d = 0.0;
if (d) { }           // 假，正确

// 但！
if (d == 0) { }      // 危险！浮点数可能有微小误差

// 正确做法
if (fabs(d) < 1e-9) { }
```

### 悬空 else 问题

```c
if (condition1)
    if (condition2)
        printf("A\n");
    else
        printf("B\n");   // 这个 else 属于哪个 if？
```

**规则**：`else` 总是与**最近的未匹配**的 `if` 配对。上面的代码等价于：

```c
if (condition1) {
    if (condition2) {
        printf("A\n");
    } else {
        printf("B\n");
    }
}
```

**黄金规则**：始终使用大括号，即使只有一行代码。

### 防御式编程模式

```c
// 好的写法：先处理错误情况，减少嵌套
int process_file(const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (fp == NULL) {
        return -1;   // 提前返回，主逻辑不受干扰
    }

    // 主逻辑在这里，不需要嵌套在 if 里面
    // ...

    fclose(fp);
    return 0;
}

// 避免这种深层嵌套
int bad_process(const char *filename) {
    FILE *fp = fopen(filename, "r");
    if (fp != NULL) {
        // 嵌套一层
        if (some_check()) {
            // 嵌套两层
            if (another_check()) {
                // 嵌套三层——"箭头代码"
            }
        }
        fclose(fp);
    }
    return 0;
}
```

## switch 语句

### 基本语法

```c
switch (表达式) {
    case 常量1:
        // 代码
        break;
    case 常量2:
        // 代码
        break;
    default:
        // 默认代码
}
```

### switch 的底层实现

编译器通常将 `switch` 优化为**跳转表**（jump table），时间复杂度 O(1)：

```asm
; 伪代码
mov eax, [expression]    ; 加载表达式的值
jmp [jump_table + eax * 4]  ; 直接跳转到对应 case
```

因此当 case 值密集时，`switch` 比多个 `if-else` 更快。

### case 的陷阱

```c
int x = 1;
switch (x) {
    case 1:
        printf("One\n");
        // 忘记 break！
    case 2:
        printf("Two\n");   // 也会执行！
        break;
}
```

**输出**：
```
One
Two
```

这称为**fall-through**（穿透），有时是有意的：

```c
switch (c) {
    case 'a':
    case 'e':
    case 'i':
    case 'o':
    case 'u':
        printf("元音\n");
        break;
    default:
        printf("辅音\n");
}
```

### switch 的限制

1. **表达式必须是整数类型**：`char`、`short`、`int`、`long`、`enum`
2. **case 必须是编译时常量**：不能是变量

```c
int x = 5;
int y = 10;
switch (x) {
    case y:        // 错误！y 不是常量
        // ...
}
```

## 条件运算符

```c
int max = (a > b) ? a : b;
```

### 嵌套使用

```c
// 可读性差的写法
int result = (a > b) ? ((a > c) ? a : c) : ((b > c) ? b : c);

// 更好的写法
int result;
if (a > b && a > c) {
    result = a;
} else if (b > c) {
    result = b;
} else {
    result = c;
}
```

**原则**：条件运算符嵌套超过一层时，改用 if-else。

## 短路求值

```c
if (ptr != NULL && *ptr > 0) { }
// 如果 ptr 为 NULL，不会解引用，避免段错误

if (count > 0 && sum / count > 10) { }
// 如果 count 为 0，不会执行除法，避免除零错误
```

**利用短路求值进行条件执行**：

```c
// 如果文件打开成功才读取
FILE *fp = fopen("data.txt", "r");
fp && fgets(line, sizeof(line), fp);
```

## 常见错误

### 1. 赋值而非比较

```c
if (x = 5) { }      // 将 5 赋值给 x，然后判断 x（非0，为真）
if (x == 5) { }     // 正确：比较
```

**防御性写法**（Yoda条件）：

```c
if (5 == x) { }      // 如果写成 5 = x，编译器会报错
```

### 2. 浮点数比较

```c
if (d == 0.1) { }   // 危险！0.1 在二进制中不能精确表示

// 正确做法
if (fabs(d - 0.1) < 1e-9) { }
```

### 3. 位运算误用为逻辑运算

```c
if (flags & MASK) { }     // 位与，检查某一位是否设置
if (flags && MASK) { }    // 逻辑与，两个都非0则为真，语义完全不同
```

## 学习要点总结

1. C语言的条件基于整数零值测试，0为假，非0为真
2. `else` 总是与最近的未匹配 `if` 配对，用大括号避免歧义
3. `switch` 的 `case` 必须有 `break`，除非有意利用 fall-through
4. 利用 `&&` 和 `||` 的短路特性进行防御式编程
5. 浮点数不要用 `==` 比较，用差值小于阈值判断
