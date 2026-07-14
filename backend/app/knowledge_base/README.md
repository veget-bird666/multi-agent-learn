# 知识库目录

将学习资料按学科放入对应子目录，构建脚本会自动扫描所有 `.md` 文件。

运行构建：

```bash
cd backend
python -m scripts.build_knowledge_base
```

`scripts/build_knowledge_base.py` 会遍历 `app/knowledge_base/` 下**所有子目录**中的 `.md` 文件，按 Markdown 标题切片后写入 ChromaDB 向量库。新增或修改 `.md` 文件后重新运行即可更新索引，无需手动注册文件名。

```
knowledge_base/
├── c_programming/       # C 语言相关
│   ├── 01_hello_c.md
│   └── ...
├── cpp/                 # C++ 相关
│   ├── 01_hello_cpp.md
│   └── ...
├── operating_systems/   # 操作系统相关
│   ├── 01_os_overview.md
│   └── ...
├── python/              # Python 相关
│   ├── 01_getting_started.md
│   └── ...
└── data_structure/      # 数据结构相关（待添加）
```

---

## cpp/ — C++ 编程（27 章）

| 文件 | 主题 | 简介 |
|:---|:---|:---|
| `01_hello_cpp.md` | 环境搭建与第一个程序 | C++ 简介、编译流程、Hello World、开发环境 |
| `02_data_types.md` | 数据类型与变量 | 基本类型、auto/decltype、const/constexpr、枚举 |
| `03_operators.md` | 运算符 | 算术、逻辑、位运算、类型转换、优先级 |
| `04_io_streams.md` | 输入输出流 | iostream 模型、格式化 I/O、流状态与错误处理 |
| `05_control_flow.md` | 控制流 | if/switch、循环、范围 for、跳转语句 |
| `06_functions.md` | 函数 | 参数传递、重载、默认参数、inline、constexpr |
| `07_arrays.md` | 数组与 vector | C 数组、std::array、std::vector 及常用操作 |
| `08_strings.md` | 字符串 | std::string、string_view、转换与性能 |
| `09_pointers_references.md` | 指针与引用 | 指针基础、nullptr、引用、const 与指针 |
| `10_memory_management.md` | 内存管理 | 栈与堆、RAII、智能指针、泄漏与循环引用 |
| `11_classes_oop.md` | 类与面向对象 | 封装、访问控制、静态成员、友元、设计原则 |
| `12_constructors_destructors.md` | 构造与析构 | 初始化列表、拷贝/移动、三五法则、explicit |
| `13_inheritance_polymorphism.md` | 继承与多态 | 继承方式、虚函数、override、dynamic_cast |
| `14_operator_overloading.md` | 运算符重载 | 成员 vs 非成员、比较、下标、`<=>` |
| `15_templates.md` | 模板 | 函数/类模板、特化、SFINAE、concepts |
| `16_stl_containers.md` | STL 容器 | vector、map、unordered_map、适配器与选择指南 |
| `17_iterators_algorithms.md` | 迭代器与算法 | 迭代器类别、algorithm、numeric、ranges |
| `18_lambda_functional.md` | Lambda 与函数式 | 捕获、STL 配合、std::function、bind |
| `19_move_semantics.md` | 移动语义 | 左值/右值、std::move、完美转发、三五法则 |
| `20_exceptions.md` | 异常处理 | try/catch、异常安全、noexcept、optional |
| `21_namespaces.md` | 命名空间 | 定义与使用、ADL、匿名与 inline 命名空间 |
| `22_file_io.md` | 文件 I/O | fstream、文本/二进制、filesystem、缓冲与错误处理 |
| `23_preprocessor.md` | 预处理器 | 宏、条件编译、头文件组织、static_assert、模块概览 |
| `24_multithreading.md` | 多线程 | thread、mutex、atomic、条件变量、async/future |
| `25_debugging.md` | 调试与测试 | GDB、Sanitizer、断言、单元测试、静态分析 |
| `26_cpp_standards.md` | C++ 标准与现代特性 | C++11–23 特性概览、编译器支持、ABI 与迁移 |
| `27_best_practices.md` | 编程最佳实践 | RAII、接口设计、Core Guidelines、反模式与代码审查 |

建议按编号顺序学习：先掌握语法与 OOP，再深入 STL、内存与模板，最后学习文件 I/O、预处理器、多线程及工程化实践。

---

## c_programming/ — C 语言

（章节列表见 `c_programming/` 目录，构建脚本同样自动扫描。）

## operating_systems/ — 操作系统

（章节列表见 `operating_systems/` 目录。）

## python/ — Python

（章节列表见 `python/` 目录。）

## data_structure/ — 数据结构

（待添加。）
