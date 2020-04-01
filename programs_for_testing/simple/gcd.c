#include "../pptlib.h"

int gcd(int x, int y) {
    if (x == 0) return y;
    if (y == 0) return x;
    return gcd(y, x % y);
}

int main() {
    int x;
    int y;
    int g;
    ppt_puts("x = ?\n");
    x = ppt_getint();
    ppt_puts("y = ?\n");
    y = ppt_getint();
    g = gcd(x, y);
    ppt_puts("gcd(x, y) = ");
    ppt_putint(g);
    ppt_puts("\n");
    return 0;
}