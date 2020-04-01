#include "../pptlib.h"

int factorial(int i) {
    if (i == 0) return 1;
    return i * factorial(i-1);
}

int main() {
    ppt_putint(factorial(4));
    ppt_putc('\n');
    return 0;
}