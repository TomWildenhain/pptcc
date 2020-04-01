#include "../pptlib.h"

int a = 7;

int main() {
    int b;

    ppt_puts("A=\n");
    a = ppt_getint();
    ppt_puts("B=\n");
    b = ppt_getint();
    ppt_puts("A+B=");
    ppt_putint(a+b);
    ppt_putc('\n');
    ppt_puts("A-B=");
    ppt_putint(a-b);
    ppt_putc('\n');
    ppt_puts("A/B=");
    ppt_putint(a/b);
    ppt_putc('\n');
    ppt_puts("A%B=");
    ppt_putint(a%b);
    ppt_putc('\n');
    ppt_puts("A*B=");
    ppt_putint(a*b);
    ppt_putc('\n');
    ppt_puts("A<B=");
    ppt_putint(a<b);
    ppt_putc('\n');
    ppt_puts("A==B=");
    ppt_putint(a==b);
    ppt_putc('\n');
}