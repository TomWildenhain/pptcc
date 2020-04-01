#include "../pptlib.h"

int main() {
    ppt_putint(ppt_rand() % 6 + 1);
    ppt_putc('\n');
    return 0;
}
