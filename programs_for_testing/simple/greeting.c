#include "../pptlib.h"

int main() {
    char buf[20];
    ppt_puts("What is your name?\n");
    ppt_gets(buf);
    ppt_puts("Hello ");
    ppt_puts(buf);
    ppt_puts("!\n");
    return 0;
}