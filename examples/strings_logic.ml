// 字符串与逻辑运算
string greeting;
int score;
int passed;

greeting = "Hello MiniLang";
print(greeting);

score = 85;
passed = 0;
if (score >= 60 && score <= 100) {
    passed = 1;
}
if (passed == 1 || score == 0) {
    print(999);
}
