// 求最大值 — 函数 + if-else
int max2(int x, int y) {
    if (x > y) {
        return x;
    }
    return y;
}

int max3(int a, int b, int c) {
    int m;
    m = max2(a, b);
    return max2(m, c);
}

print(max3(12, 45, 23));
