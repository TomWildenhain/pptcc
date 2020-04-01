#include "../pptlib.h"

int fib(int x) {
    if (x <= 1) return 1;
    return fib(x-1) + fib(x-2);
}

int main() {
    ppt_putint(fib(7));
    ppt_putc('\n');
    return 0;
}
