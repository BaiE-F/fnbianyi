# MiniLang 简单编译器

参考 [CompilationPrinciple](https://github.com/qianqianjun/CompilationPrinciple) 项目的词法/语法分析思路，实现一个**完整但精炼**的教学用编译器，涵盖编译原理课程的全部核心阶段。

## 编译流水线

```
源码 (.ml) → 词法分析 → 语法分析 → 语义分析 → 中间代码(TAC) → 优化 → 目标代码(Python)
```

| 阶段 | 模块 | 说明 |
|------|------|------|
| 词法分析 | `compiler/lexer.py` | 从 `grammar/tokens.json` 加载 Token 规则 |
| 语法分析 | `compiler/parser.py` | 递归下降，依据 `grammar/grammar.json` 的 BNF |
| 语义分析 | `compiler/semantic.py` | 符号表、作用域、类型检查 |
| 中间代码 | `compiler/tac.py` | 三地址码 (Three-Address Code) |
| 优化 | `compiler/optimizer.py` | 常量折叠、复制传播、死代码消除 |
| 目标代码 | `compiler/codegen.py` | 生成可执行的 Python 代码 |

## MiniLang 语法示例

```c
int a;
int b;
a = 10;
b = 20;
print(a + b);

while (i <= n) {
    result = result * i;
    i = i + 1;
}

if (x > 10) {
    y = 100;
} else {
    y = 0;
}
```

## 快速开始（桌面编辑器）

需要 Python 3.10+，**无需安装额外依赖**（使用内置 Tkinter）。

```bash
python -m compiler.main
```

在编辑器里：
1. 编写 MiniLang 代码（默认 `workspace/main.ml`）
2. **编译并运行**（`F5`）— 运行时会弹窗 `input` 读入
3. `print` 输出显示在下方，`write` 写入 `workspace/output/`
4. **Ctrl+S** 保存，**打开输出目录** 查看生成文件

支持：`int` / `float` / `string`、`input`、`print`、`write`、`string[i]` 字符访问、`len(s)` 长度、数组（栈/队列等基础结构）、函数、循环。

### 语言速查（写算法常用）

| 能力 | 写法 |
|------|------|
| 字符串读入 | `input(s, "提示: ");` |
| 取字符 | `ch = s[i];` |
| 长度 | `n = len(s);` |
| 栈（数组模拟） | `int stack[256];` + `top` 指针 |
| 字符串拼接 | `s = s + "x";` |
| 写文件 | `write("out.txt", x);` → `workspace/output/` |

括号匹配示例思路：`input` 读整串 → `while (i < len(s))` → `s[i]` 与 `(` `[` `{` 比较 → `int stack[]` 压弹栈。


```c
// 递归函数
int fib(int n) {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

// 数组 + for + break
int data[5];
int total;
int i;
for (i = 0; i < 5; i = i + 1) {
    data[i] = (i + 1) * 10;
}
total = 0;
for (i = 0; i < 5; i = i + 1) {
    total = total + data[i];
    if (total > 100) {
        break;
    }
}

// 字符串与逻辑运算
string msg;
msg = "Hello MiniLang";
if (score >= 60 && score <= 100) {
    print(msg);
}
```

### 命令行（可选）

```bash
# 编译并运行指定文件（终端内 input 从键盘读入）
python -m compiler.main workspace/main.ml --run

# 查看完整编译过程
python -m compiler.main examples/factorial.ml --dump all --run
```

## 项目结构

```
fnbianyi/
├── editor/gui.py            # 桌面代码编辑器（主入口）
├── workspace/               # 用户编写代码的工作区
│   ├── main.ml              # 默认源文件
│   └── output/              # write() 输出目录
├── grammar/                 # 语法规则库
├── compiler/                # 编译器各阶段
└── examples/                # 参考示例（可选）
```

> Web 版仍保留在 `web/` 目录，运行 `python -m compiler.main --web` 或 `python -m web.app`，访问 http://127.0.0.1:5000。**与桌面版同步**：空白工作区、`input`/`write`、`string[i]`、`len()`、运行输入框、保存到 `workspace/main.ml`。

## 与参考项目的对应关系

| 参考项目 | 本项目 |
|----------|--------|
| Java DFA 词法分析 | Python 正则词法分析 + `tokens.json` 规则库 |
| Python LL1/LR 分析器 | 递归下降语法分析 + `grammar.json` BNF 库 |
| （无） | 语义分析、TAC、优化、代码生成 |

## 扩展建议

- 在 `grammar/tokens.json` 中添加新关键字/运算符
- 在 `grammar/grammar.json` 中扩展产生式，并在 `parser.py` 中实现对应解析函数
- 将目标后端改为 x86 汇编或 LLVM IR
