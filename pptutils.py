def hex_to_int(hex):
    assert hex.startswith('0x')
    hex = hex[2:]
    total = 0
    for h in hex:
        total *= 16
        total += '0123456789abcdef'.index(h)
    return total

def byte_to_uint(byte):
    total = 0
    for c in byte:
        total *= 2
        if c == '1':
            total += 1
    return total

def byte_to_int(byte):
    total = 0
    for c in byte:
        total *= 2
        if c == '1':
            total += 1
    return total if byte[0] == '0' else total - 2**8

def word_to_int(word):
    total = 0
    for c in word:
        total *= 2
        if c == '1':
            total += 1
    return total if word[0] == '0' else total - 2**16

def dword_to_int(dword):
    total = 0
    for c in dword:
        total *= 2
        if c == '1':
            total += 1
    return total if dword[0] == '0' else total - 2**32

def word_to_uint(word):
    total = 0
    for c in word:
        total *= 2
        if c == '1':
            total += 1
    return total

def dword_to_uint(dword):
    total = 0
    for c in dword:
        total *= 2
        if c == '1':
            total += 1
    return total

def int_to_byte(x):
    if x < 0:
        x += 2**8
    res = ''
    for i in range(8):
        if x % 2 == 1:
            res = '1' + res
        else:
            res = '0' + res
        x = x // 2
    return res

def int_to_word(x):
    if x < 0:
        x += 2**16
    res = ''
    for i in range(16):
        if x % 2 == 1:
            res = '1' + res
        else:
            res = '0' + res
        x = x // 2
    return res

def uint_to_word(x):
    res = ''
    for i in range(16):
        if x % 2 == 1:
            res = '1' + res
        else:
            res = '0' + res
        x = x // 2
    return res

def uint_to_dword(x):
    res = ''
    for i in range(32):
        if x % 2 == 1:
            res = '1' + res
        else:
            res = '0' + res
        x = x // 2
    return res[:16], res[16:]

def int_to_dword(x):
    if x < 0:
        x += 2**32
    res = ''
    for i in range(32):
        if x % 2 == 1:
            res = '1' + res
        else:
            res = '0' + res
        x = x // 2
    return res[:16], res[16:]

def uint_to_byte(x):
    res = ''
    for i in range(8):
        if x % 2 == 1:
            res = '1' + res
        else:
            res = '0' + res
        x = x // 2
    return res

def split_on_spaces(s):
    parts = s.replace('\t', ' ').split(' ')
    parts = [p.strip() for p in parts if p.strip()]
    return parts

def condense_spaces(s):
    return ' '.join(split_on_spaces(s))

def pad_to_length(s, l):
    assert l >= len(s)
    return s + ' ' * (l - len(s))