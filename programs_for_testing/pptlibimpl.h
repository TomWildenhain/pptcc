#include <stdio.h>
#include <stdbool.h>
#include <limits.h>
#include <stdlib.h> 
#include <time.h>

void ppt_puts(char* s) {
    printf("%s", s);
}

void ppt_putint(int i) {
    printf("%d", i);
}

void ppt_putc(char c) {
    putc(c, stdout);
}

void ppt_gets(char *buf) {
    fgets(buf, INT_MAX, stdin);
    char *c = buf;
    while (*c != '\0') {
        c++;
    }
    c[-1] = '\0';
}

int ppt_getint() {
    int i;
    scanf("%d", &i);
    return i;
}

int seeded = false;

int ppt_rand() {
    if (!seeded) {
        srand(time(0));
        seeded = true;
    }
    return rand();
}