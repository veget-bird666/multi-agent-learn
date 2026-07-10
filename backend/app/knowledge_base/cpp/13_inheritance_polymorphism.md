# C++ 继承与多态

## 继承的本质

### 从 C 到 C++：代码复用与类型关系

C 语言无继承，复用靠**组合**、**函数指针**模拟多态：

```c
struct Animal {
    void (*speak)(struct Animal*);
    const char *name;
};
void dog_speak(struct Animal *a) { printf("%s: woof\n", a->name); }
```

C++ 继承在语言层面建立 **is-a** 关系，编译器自动布局基类子对象、支持隐式向上转型：

```cpp
class Animal {
public:
    std::string name;
    virtual void speak() const { std::cout << name << " makes a sound\n"; }
    virtual ~Animal() = default;
};

class Dog : public Animal {
public:
    void speak() const override { std::cout << name << " says woof!\n"; }
    void fetch() { std::cout << name << " fetches\n"; }
};
```

**深层理解**：派生类对象**包含**完整的基类子对象，加上自己的成员。继承是编译期类型关系 + 运行期多态（虚函数）的组合。

## 继承基础

```cpp
Dog d;
d.name = "Buddy";
d.speak();    // 静态类型 Dog → Dog::speak
d.fetch();

Animal& ref = d;   // 向上转型，隐式允许
ref.speak();       // 动态类型 Dog → Dog::speak（多态）
// ref.fetch();    // 编译错误：Animal 无 fetch
```

### 对象内存布局（单继承）

```
Dog 对象内存:
┌─────────────────────────────┐
│ Animal 子对象               │
│   vptr ──→ vtable           │
│   name (string)             │
├─────────────────────────────┤
│ Dog 特有成员                │
└─────────────────────────────┘
```

## 继承方式

```cpp
class Base {};

class PublicDerived    : public Base    {};   // 最常用
class ProtectedDerived : protected Base {};
class PrivateDerived   : private Base   {};
```

| 基类成员 | public 继承 | protected 继承 | private 继承 |
|:---|:---|:---|:---|
| public | public | protected | private |
| protected | protected | protected | private |
| private | 不可访问 | 不可访问 | 不可访问 |

**实际开发几乎只用 public 继承**，表示 "is-a" 关系。protected/private 继承表示 "implemented-in-terms-of"（实现继承），较少见。

**C 对比**：C 无继承，类似关系需手动嵌入基类结构体：

```c
struct Dog {
    struct Animal base;   // 组合模拟继承
};
```

## 构造函数与析构函数

```cpp
class Base {
public:
    Base(int x) { std::cout << "Base(" << x << ")\n"; }
    virtual ~Base() { std::cout << "~Base()\n"; }
};

class Derived : public Base {
    int extra;
public:
    Derived(int x, int e) : Base(x), extra(e) {
        std::cout << "Derived(" << extra << ")\n";
    }
    ~Derived() override { std::cout << "~Derived()\n"; }
};
```

**构造顺序**：基类 → 成员（声明顺序）→ 派生类构造函数体  
**析构顺序**：派生类析构函数体 → 成员（逆序）→ 基类

```
Derived d(1, 2):
  Base(1) → extra 初始化 → Derived 体
  ~Derived 体 → ~Base
```

### 虚析构函数

基类析构函数应声明为 `virtual`，确保通过基类指针 `delete` 派生对象时正确调用派生析构：

```cpp
Animal* p = new Dog();
delete p;   // virtual ~Animal → ~Dog → ~Animal
            // 若非 virtual，只 ~Animal，Dog 部分泄漏
```

**原因**：`delete p` 先调用析构，再释放内存；若只析构 Base 部分，Derived 成员（如额外指针）不会释放。

## 函数重写（Override）

```cpp
class Shape {
public:
    virtual double area() const = 0;   // 纯虚函数
    virtual void draw() const {
        std::cout << "Drawing shape\n";
    }
    virtual ~Shape() = default;
};

class Circle : public Shape {
    double radius;
public:
    Circle(double r) : radius(r) {}
    double area() const override { return 3.14159 * radius * radius; }
    void draw() const override { std::cout << "Drawing circle\n"; }
};
```

- `virtual`：允许派生类重写，通过基类指针/引用调用时动态绑定
- `override`（C++11）：显式标记重写，签名不匹配时编译错误
- `= 0`：纯虚函数，类变为**抽象类**，不能实例化

**C 对比**：C 用函数指针 + 手动分发；C++ 虚函数由编译器生成 vtable/vptr，自动分发。

## 多态与虚函数表

```cpp
std::vector<std::unique_ptr<Shape>> shapes;
shapes.push_back(std::make_unique<Circle>(5.0));

for (const auto& s : shapes) {
    std::cout << "Area: " << s->area() << std::endl;
    s->draw();
}
```

**运行时多态**：编译时类型是 `Shape*`，运行时根据**实际对象类型**调用对应虚函数。

### vtable 机制

```
Circle 对象的 vptr ──→ Circle vtable:
                         [0] → Circle::area()
                         [1] → Circle::draw()
                         [2] → Circle::~Circle()

Shape 对象的 vptr ──→ Shape vtable:
                        [0] → Shape::area() 或纯虚占位
                        ...
```

**调用过程**：`s->area()` → 取 `s` 的 vptr → 查 vtable 第 area 槽 → 跳转执行。

**开销**：每次虚调用多一次间接寻址；非多态场景不必滥用 `virtual`。

## final 关键字（C++11）

```cpp
class Base {
public:
    virtual void func();
};

class Derived : public Base {
    void func() override final;   // 派生类不能再 override
};

class FinalClass final : public Base {};   // 不能再被继承
```

## 访问控制与继承

派生类可访问基类 `public` 和 `protected` 成员，不能访问 `private` 成员：

```cpp
class Base {
protected:
    int value;
private:
    int secret;
};

class Derived : public Base {
    void f() {
        value = 1;    // OK
        // secret = 2; // 编译错误
    }
};
```

**protected 的设计意图**：允许派生类访问，对外隐藏。

## 类型转换

### 向上转型（Upcasting）

```cpp
Derived d;
Base* bp = &d;       // 隐式、安全
Base& ref = d;       // 隐式、安全
```

### 向下转型（Downcasting）

```cpp
Base* bp = new Circle(5.0);

// static_cast：程序员保证类型正确，无运行时检查
Circle* cp = static_cast<Circle*>(bp);

// dynamic_cast：需要多态基类（有虚函数），运行时检查
Circle* cp2 = dynamic_cast<Circle*>(bp);
if (cp2) { /* 转换成功 */ }
```

**dynamic_cast 失败**：
- 指针版本：返回 `nullptr`
- 引用版本：抛 `std::bad_cast`

**C 对比**：C 只能强制 cast，无运行时类型检查。

## 对象切片（Slicing）

```cpp
Derived d;
Base b = d;   // 只拷贝 Base 部分，Derived 特有成员丢失
b.speak();    // 调用 Base::speak，非多态
```

**原因**：`Base b = d` 是**按值拷贝**，目标类型是 `Base`，大小只够 Base 部分。

**正确做法**：多态通过指针或引用

```cpp
Base& ref = d;   // OK，无切片
Base* ptr = &d;  // OK
```

```
切片:
  Derived [ Base部分 | Dog部分 ]  ──拷贝──→  Base [ Base部分 ]
                                              Dog部分丢失
```

## 抽象类与接口

```cpp
class Drawable {
public:
    virtual void draw() const = 0;
    virtual ~Drawable() = default;
};

class Button : public Drawable {
public:
    void draw() const override { /* 绘制按钮 */ }
};
```

**接口设计**：纯虚类定义契约，派生类必须实现。C++ 无 `interface` 关键字，用全纯虚类模拟。

## 多重继承与菱形问题（简介）

```cpp
class A { virtual void f(); };
class B : public A {};
class C : public A {};
class D : public B, public C {};   // D 有两份 A 子对象！
```

**菱形继承**：`D` 含两个 `A` 子对象，歧义：

```cpp
D d;
// d.f();   // 歧义：B::A::f 还是 C::A::f？
```

**修复**：虚继承

```cpp
class B : virtual public A {};
class C : virtual public A {};
class D : public B, public C {};   // 仅一份 A
```

**现代建议**：优先组合 over 多重继承；多重继承常用于 mixin 或接口组合。

## 常见错误

### 1. 基类析构非 virtual

```cpp
class Base { ~Base() {} };   // 非 virtual
Base* p = new Derived();
delete p;   // 只 ~Base，Derived 资源泄漏
// 原因：静态绑定析构函数
// 修复：virtual ~Base() = default;
```

### 2. 隐藏（Hide）而非重写（Override）

```cpp
class Base {
public:
    void func(int x);
};
class Derived : public Base {
public:
    void func(double x);   // 隐藏 Base::func(int)，不是重写！
};

Derived d;
d.func(1);        // 调用 Derived::func(double)，1 转为 1.0
// d.func(1); 若 Base 有 func(int)，被隐藏，不能直接调用
d.Base::func(1);  // 显式调用 Base 版本
// 原因：名称隐藏规则：派生类同名函数隐藏所有基类 overload
// 修复：用 override（签名必须匹配）或 using Base::func;
```

### 3. 对象切片

见上文。原因：按值赋值/传参/返回会截断派生部分。

### 4. 构造/析构中调用虚函数

```cpp
class Base {
public:
    Base() { init(); }
    virtual void init() { /* Base */ }
};
class Derived : public Base {
    void init() override { /* Derived 成员可能未初始化 */ }
};
// Base 构造时，虚函数绑定到 Base::init
// 原因：派生部分尚未构造，调用 Derived::init 不安全
```

### 5. 忽略 override 导致拼写错误

```cpp
void draw() overide { }   // 编译错误（故意拼错）
// 若无 override，可能变成隐藏而非重写，静默错误
```

## 防御性编程模式

### 1. 多态基类虚析构

```cpp
class Base {
public:
    virtual ~Base() = default;
};
```

### 2. 用 override 标记所有重写

```cpp
void draw() const override;
```

### 3. 多态用指针/引用，避免切片

```cpp
void process(const Shape& s);   // 而非 void process(Shape s);
```

### 4. 向下转型用 dynamic_cast 并检查

```cpp
if (auto* c = dynamic_cast<Circle*>(sp)) {
    // 安全使用 c
}
```

### 5. 抽象接口 + 工厂

```cpp
std::unique_ptr<Shape> createShape(const std::string& type);
```

## C 函数指针 vs C++ 虚函数

| 特性 | C 函数指针 | C++ virtual |
|:---|:---|:---|
| 机制 | 手动结构体 + 函数指针 | 编译器 vtable/vptr |
| 类型安全 | 弱 | 较强 |
| 运行时开销 | 一次间接调用 | 一次间接调用 + vptr |
| 扩展 | 手动维护 | 继承 + override |
| 析构 | 手动 | 虚析构自动链式调用 |

## 学习要点总结

1. public 继承表示 "is-a"；多态基类析构函数必须 `virtual`
2. 用 `override` 标记重写，用 `final` 禁止进一步重写/继承
3. 抽象类含纯虚函数，不能实例化，用于定义接口
4. 多态通过基类指针/引用 + 虚函数实现；避免对象切片
5. 向下转型优先 `dynamic_cast` 并检查返回值
6. 构造/析构期间虚函数不会多态到派生类
7. 名称隐藏：派生同名函数会隐藏基类所有 overload，注意 `using` 声明
