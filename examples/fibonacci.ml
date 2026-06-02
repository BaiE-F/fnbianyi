// 递归斐波那契 — 函数 + 条件 + 递归调用
int fib(int n) {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}

int result;
result = fib(10);
print(result);
