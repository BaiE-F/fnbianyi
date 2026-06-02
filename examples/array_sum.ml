// 数组求和 — 数组 + for 循环 + break
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
print(total);
