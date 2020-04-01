#include <stdbool.h>
#include "../pptlib.h"

bool isprime(int p) {
    int i;
    if (p < 2) return false;
    for (i = 2; i*i <= p; i++) {
        if (p % i == 0) return false;
    }
    return true;
}

int main() {
    int i = 0;
    while (true) {
        if (isprime(i)) {
            ppt_putint(i);
            ppt_puts(" is prime!\n");
        }
        i++;
    }
    return 0;
}