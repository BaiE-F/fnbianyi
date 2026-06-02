string s;
int n;
int i;
int top;
int stack[256];
string ch;
int ok;
int expect;

print("输入括号串:");
input(s, "> ");

n = len(s);
top = 0;
i = 0;
ok = 1;

while (i < n) {
    ch = s[i];
    if (ch == "(") {
        stack[top] = 1;
        top = top + 1;
    } else {
        if (ch == "[") {
            stack[top] = 2;
            top = top + 1;
        } else {
            if (ch == "{") {
                stack[top] = 3;
                top = top + 1;
            } else {
                if (ch == ")") {
                    top = top - 1;
                    if (top < 0) { ok = 0; break; }
                    expect = stack[top];
                    if (expect != 1) { ok = 0; break; }
                } else {
                    if (ch == "]") {
                        top = top - 1;
                        if (top < 0) { ok = 0; break; }
                        expect = stack[top];
                        if (expect != 2) { ok = 0; break; }
                    } else {
                        if (ch == "}") {
                            top = top - 1;
                            if (top < 0) { ok = 0; break; }
                            expect = stack[top];
                            if (expect != 3) { ok = 0; break; }
                        }
                    }
                }
            }
        }
    }
    i = i + 1;
}

if (ok == 1 && top == 0 {
    print("匹配");
} else {
    print("不匹配");
}


