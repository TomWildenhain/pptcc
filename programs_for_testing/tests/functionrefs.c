#include "../pptlib.h"

typedef int (*intfnptr)(int x);

int fn1(int x) {
    return x / 4; 
}

int fn2(int x) {
    return x * 50;
}

int fn3(int x) {
    return x + 1;
}

int main() {
    intfnptr fns[3] = { &fn3, &fn2, &fn1 };
    int res = 20;
    unsigned int i = 0;
    for (i = 0; i < 3; i++) {
        res = (*fns[3-i-1])(res);
    }
    ppt_putint(res);
    ppt_putc('\n');
}