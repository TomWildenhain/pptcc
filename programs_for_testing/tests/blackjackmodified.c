#include "../pptlib.h"
#include <string.h>
#include <stdbool.h>

typedef struct {
    bool high_ace;
    int total;
} score;

int test_const[] = {1, 2, 3, 'H', "Hello", "World"};

char s2[4] = { 'a','a',3, 'b' };

void update_score(score *p, int c) {
    int v = (c % 13) + 1;
    if (v == 1) {
        p->high_ace = true;
        p->total += 11;
    }
    else {
        p->total += v < 10 ? v : 10;
    }
    if (p->total > 21 && p->high_ace) {
        p->high_ace = false;
        p->total -= 10;
    }
}

int test_ptr = &test_const[-1];

void put_card(int c) {
    int v = (c % 13) + 1;
    if (v == 1) {
        ppt_putc('A');
    }
    if (v == 0) {
        ppt_putc('X');
        v += 3000;
        v = v >> 3;
        if (v == 2000) {
            ppt_putc('X');
        }
    }
    else if (v > 10) {
        ppt_putc("JQK"[v-11]);
    }
    else  {
        ppt_putint(v);
    }
}

int main() {
    int deck[52];
    int i;
    int j;
    int top;
    int dealer1;
    int dealer2;
    int player1;
    int player2;
    char move[2];
    int c;
    score dealer_score = {false, 0};
    score player_score = {false, 0};

    deck[0] = 0;
    for (i = 1; i < 52; i++) {
        j = ppt_rand(i);
        deck[i] = deck[j];
        deck[j] = i;
    }
    top = 0;

    ppt_puts("D: ");
    dealer1 = deck[top++];
    update_score(&dealer_score, dealer1);
    put_card(dealer1);
    ppt_putc(',');
    dealer2 = deck[top++];
    update_score(&dealer_score, dealer2);
    if (dealer_score.total == 21) {
        put_card(dealer2);
        ppt_puts("\n=>21\n");
    }
    else {
        ppt_puts("?\n");
    }

    ppt_puts("P: ");
    player1 = deck[top++];
    update_score(&player_score, player1);
    put_card(player1);
    ppt_putc(',');
    player2 = deck[top++];
    update_score(&player_score, player2);
    put_card(player2);

    if (player_score.total == 21) {
        ppt_puts("\n=>21\n");
        if (dealer_score.total == 21) {
            ppt_puts("Tie!\n");
            return 0;
        }
        else {
            ppt_puts("Player wins!\n");
            return 0;
        }
    }

    if (dealer_score.total == 21) {
        ppt_puts("\nDealer wins!\n");
        return 0;
    }

    ppt_puts("\nH/S?\n");
    ppt_gets(move);
    while (move[0] == 'H' || move[0] == 'h') {
        c = deck[top++];
        put_card(c);
        ppt_putc('\n');
        update_score(&player_score, c);
        if (player_score.total > 21) {
            ppt_puts("=>bust\nDealer wins!\n");
            return 0;
        }
        else if (player_score.total == 21) {
            break;
        }
        ppt_gets(move);
    }
    ppt_puts("=>");
    ppt_putint(player_score.total);

    ppt_puts("\nD: ");
    put_card(dealer1);
    ppt_putc(',');
    put_card(dealer2);
    while (dealer_score.total < 17) {
        c = deck[top++];
        ppt_putc(',');
        put_card(c);
        update_score(&dealer_score, c);
    }
    if (dealer_score.total > 21) {
        ppt_puts("\n=>bust\nPlayer wins!\n");
        return 0;
    }
    else {
        ppt_puts("\n=>");
        ppt_putint(dealer_score.total);
    }

    if (dealer_score.total > player_score.total) {
        ppt_puts("\nDealer wins!\n");
    }
    else if (dealer_score.total == player_score.total) {
        ppt_puts("\nTie!\n");
    }
    else {
        ppt_puts("\nPlayer wins!\n");
    }
    return 0;
}

int cool_sum(a, b, c, d, e, f, g) {
    return a + b + c+d+e+f+g;
}

int (*global_fn_ref)() = &cool_sum;

int test_sum() {
    int (*x)() = &cool_sum;
    if (x > 0) {
        global_fn_ref();
    }
    return cool_sum(1, 2, 3, 4, 5, test_const[3], 7);
}