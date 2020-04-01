import random
import argparse
from pptutils import *

class Instruction:
    def __init__(self, cmd, args):
        self.cmd = cmd
        self.args = args

class ByteRegister:
    def __init__(self, name):
        self.name = name
        self.value = '0' * 8

class MemRegister:
    def __init__(self, name):
        self.name = name
        self.low = '0' * 8
        self.high = '0' * 8

    def read(self):
        return self.high + self.low

    def assign(self, bits):
        self.high = bits[:8]
        self.low = bits[8:]

class Flags:
    def __init__(self):
        self.verdict = False
        self.carry = False
        self.zero = False
        self.sign = False
        self.overflow = False

def inc_bits(w):
    if w == '':
        return ''
    if w[-1] == '0':
        return w[:-1] + '1'
    else:
        return inc_bits(w[:-1]) + '0'

def dec_bits(w):
    if w == '':
        return ''
    if w[-1] == '1':
        return w[:-1] + '0'
    else:
        return dec_bits(w[:-1]) + '1'

def and_bits(x, y):
    if x == '0':
        return '0'
    else:
        return y

def or_bits(x, y):
    if x == '1':
        return '1'
    else:
        return y

def xor_bits(x, y):
    if x == y:
        return '0'
    else:
        return '1'

class MachineState:
    def __init__(self, text_dict, data_dict, const_dict):
        self.instructions = text_dict
        self.const = const_dict
        self.data = data_dict
        reg_names = [
            'AH', 'AL', 'BH', 'BL', 'CH', 'CL', 'DH', 'DL', 
            'M4H', 'M4L', 'M5H', 'M5L',
            'DIH', 'DIL', 'SIH', 'SIL', 'BPH', 'BPL', 'SPH', 'SPL']
        self.regs = { r: ByteRegister(r) for r in reg_names }
        self.flags = Flags()
        self.m1 = MemRegister('M1')
        self.m2 = MemRegister('M2')
        self.m3 = MemRegister('M3')
        self.ip = '0' * 16
        self.mp = '0' * 16

    def step(self):
        if self.ip not in self.instructions:
            raise Exception('ip out of range')
        assert self._read_reg('SP')[-1] == '0'
        assert len(self.m2.low) == 8
        assert len(self.m3.low) == 8
        inst = self.instructions[self.ip]
        self.ip = inc_bits(self.ip)
        if inst.cmd == 'LOAD1L':
            if inst.args[0] == 'M3H':
                self.m1.low = self.m3.high
            elif inst.args[0] == 'M3L':
                self.m1.low = self.m3.low
            else:
                self.m1.low = self.regs[inst.args[0]].value
        elif inst.cmd == 'LOAD1H':
            if inst.args[0] == 'M3H':
                self.m1.high = self.m3.high
            elif inst.args[0] == 'M3L':
                self.m1.high = self.m3.low
            else:
                self.m1.high = self.regs[inst.args[0]].value
        elif inst.cmd == 'LOAD2L':
            if inst.args[0] == 'M3H':
                self.m2.low = self.m3.high
            elif inst.args[0] == 'M3L':
                self.m2.low = self.m3.low
            else:
                self.m2.low = self.regs[inst.args[0]].value
        elif inst.cmd == 'LOAD2H':
            if inst.args[0] == 'M3H':
                self.m2.high = self.m3.high
            elif inst.args[0] == 'M3L':
                self.m2.high = self.m3.low
            else:
                self.m2.high = self.regs[inst.args[0]].value
        elif inst.cmd == 'COPYL':
            self.m3.low = self.m1.low
        elif inst.cmd == 'COPYH':
            self.m3.high = self.m1.high
        elif inst.cmd == 'STOREL':
            self.regs[inst.args[0]].value = self.m3.low
        elif inst.cmd == 'STOREH':
            self.regs[inst.args[0]].value = self.m3.high
        elif inst.cmd == 'CLEARL1':
            self.m1.low = '0' * 8
        elif inst.cmd == 'CLEARH1':
            self.m1.high = '0' * 8
        elif inst.cmd == 'CLEARL2':
            self.m2.low = '0' * 8
        elif inst.cmd == 'CLEARH2':
            self.m2.high = '0' * 8
        elif inst.cmd == 'CLEARL3':
            self.m3.low = '0' * 8
        elif inst.cmd == 'CLEARH3':
            self.m3.high = '0' * 8
        elif inst.cmd == 'CONSTL':
            self.m3.low = inst.args[0]
        elif inst.cmd == 'CONSTH':
            self.m3.high = inst.args[0]
        elif inst.cmd == 'EXEC':
            name = inst.args[0]
            assert name == name.upper()
            getattr(self, 'exec_' + name.lower())()

    def _assign_reg(self, letter, value):
        assert len(value) == 16
        self.regs[letter + 'H'].value = value[:8]
        self.regs[letter + 'L'].value = value[8:]

    def _read_reg(self, letter):
        return self.regs[letter + 'H'].value + self.regs[letter + 'L'].value

    def _addb(self, with_carry=False):
        res = ['0'] * 8
        carry = False
        if with_carry:
            carry = self.flags.carry
        for i in range(7, -1, -1):
            if i == 7:
                self.flags.overflow = carry
            total = 1 if self.m1.low[i] == '1' else 0
            total += 1 if self.m2.low[i] == '1' else 0
            if carry:
                total += 1
            if total == 0:
                carry = False
            elif total == 1:
                carry = False
                res[i] = '1'
            elif total == 2:
                carry = True
            elif total == 3:
                carry = True
                res[i] = '1'
            else:
                assert False
        self.flags.carry = carry
        self.flags.sign = res[0] == '1'
        self.m3.low = ''.join(res)
        self.flags.zero = self.m3.low == '0' * 8
    
    def exec_adcb(self):
        self._addb(with_carry=True)

    def _addw(self, with_carry=False):
        res = ['0'] * 16
        carry = False
        if with_carry:
            carry = self.flags.carry
        for i in range(15, -1, -1):
            if i == 15:
                self.flags.overflow = carry
            total = 1 if self.m1.read()[i] == '1' else 0
            total += 1 if self.m2.read()[i] == '1' else 0
            if carry:
                total += 1
            if total == 0:
                carry = False
            elif total == 1:
                carry = False
                res[i] = '1'
            elif total == 2:
                carry = True
            elif total == 3:
                carry = True
                res[i] = '1'
            else:
                assert False
        self.flags.carry = carry
        self.flags.sign = res[0] == '1'
        self.m3.assign(''.join(res))
        self.flags.zero = self.m3.read() == '0' * 16

    def exec_adcw(self):
        self._addw(with_carry=True)

    def exec_addb(self): # Used
        self._addb(with_carry=False)

    def exec_addw(self): # Used
        self._addw(with_carry=False)

    def _shiftaddr(self, n=1):
        addr = self.m1.read()
        addr = addr[n:] + '0' * n
        self.m3.assign(addr)

    def exec_shiftaddr1(self):
        self._shiftaddr(1)

    def exec_shiftaddr2(self):
        self._shiftaddr(2)

    def exec_shiftaddr3(self):
        self._shiftaddr(3)

    def exec_addaddr(self):
        res = ['0'] * 16
        carry = False
        for i in range(15, -1, -1):
            total = 1 if self.m1.read()[i] == '1' else 0
            total += 1 if self.m2.read()[i] == '1' else 0
            if carry:
                total += 1
            if total == 0:
                carry = False
            elif total == 1:
                carry = False
                res[i] = '1'
            elif total == 2:
                carry = True
            elif total == 3:
                carry = True
                res[i] = '1'
        self.m3.assign(''.join(res))

    def _bitwiseb(self, fn):
        res = ['0'] * 8
        for i in range(8):
            res[i] = fn(self.m1.low[i], self.m2.low[i])
        self.m3.low = ''.join(res)
        self.flags.zero = self.m3.low == '0' * 8
        self.flags.sign = self.m3.low[0] == '1'

    def _bitwisew(self, fn):
        res = ['0'] * 16
        for i in range(16):
            res[i] = fn(self.m1.read()[i], self.m2.read()[i])
        self.m3.assign(''.join(res))
        self.flags.zero = self.m3.read() == '0' * 16
        self.flags.sign = self.m3.high[0] == '1'

    def exec_andb(self):
        self._bitwiseb(and_bits)

    def exec_andw(self):
        self._bitwisew(and_bits)

    def exec_cbw(self):
        if self.regs['AL'].value[0] == '1':
            self.regs['AH'].value = '1' * 8
        else:
            self.regs['AH'].value = '0' * 8

    def exec_clc(self):
        self.flags.carry = False

    def exec_cmc(self):
        self.flags.carry = not self.flags.carry

    def exec_cmpb(self):
        m3 = self.m3.low
        self.exec_subb()
        self.m3.low = m3

    def exec_cmpw(self):
        m3 = self.m3.read()
        self.exec_subw()
        self.m3.assign(m3)

    def exec_decb(self):
        res = ['0'] * 8
        borrow = True
        for i in range(7, -1, -1):
            if i == 7:
                self.flags.overflow = borrow
            if borrow:
                if self.m1.low[i] == '1':
                    res[i] = '0'
                    borrow = False
                else:
                    res[i] = '1'
            else:
                res[i] = self.m1.low[i]
        self.m3.low = ''.join(res)
        self.flags.sign = self.m3.low[0]
        self.flags.carry = borrow
        self.flags.zero = self.m3.low == '0' * 8

    def exec_decw(self):
        res = ['0'] * 16
        borrow = True
        for i in range(15, -1, -1):
            if i == 15:
                self.flags.overflow = borrow
            if borrow:
                if self.m1.read()[i] == '1':
                    res[i] = '0'
                    borrow = False
                else:
                    res[i] = '1'
            else:
                res[i] = self.m1.read()[i]
        self.m3.assign(''.join(res))
        self.flags.sign = self.m3.high[0]
        self.flags.carry = borrow
        self.flags.zero = self.m3.read() == '0' * 16

    def exec_dec2w(self):
        x = word_to_uint(self.m1.read()) - 2
        self.m3.assign(uint_to_word(x))

    def exec_inc2w(self):
        x = word_to_uint(self.m1.read()) + 2
        self.m3.assign(uint_to_word(x))

    def exec_cwd(self):
        if self.regs['AH'].value[0] == '1':
            self.regs['DH'].value = '1' * 8
            self.regs['DL'].value = '1' * 8
        else:
            self.regs['DH'].value = '0' * 8
            self.regs['DL'].value = '0' * 8

    # TODO: Division

    def exec_divb(self):
        x = word_to_uint(self._read_reg('A'))
        y = byte_to_uint(self.m1.low)
        z = x // y
        w = x % y
        self.regs['AL'].value = uint_to_byte(z)
        self.regs['AH'].value = uint_to_byte(w)

    def exec_divw(self):
        xdw = self._read_reg('D') + self._read_reg('A')
        x = dword_to_uint(xdw)
        y = word_to_uint(self.m1.read())
        z = x // y
        w = x % y
        self._assign_reg('A', uint_to_word(z))
        self._assign_reg('D', uint_to_word(w))

    def exec_idivb(self):
        x = word_to_int(self._read_reg('A'))
        y = byte_to_int(self.m1.low)
        if x < 0:
            x = -x
            y = -y
        if y >= 0:
            z = x // y
            w = x % y
        else:
            z = (x + y + 1) // y
            w = x - z * y
        self.regs['AL'].value = int_to_byte(z)
        self.regs['AH'].value = int_to_byte(w)

    def exec_idivw(self):
        xdw = self._read_reg('D') + self._read_reg('A')
        x = dword_to_int(xdw)
        y = word_to_int(self.m1.read())
        if x < 0:
            x = -x
            y = -y
        if y >= 0:
            z = x // y
            w = x % y
        else:
            z = (x + y + 1) // y
            w = x - z * y
        self._assign_reg('A', int_to_word(z))
        self._assign_reg('D', int_to_word(w))

    def exec_imulb(self):
        x = byte_to_int(self.regs['AL'].value)
        y = byte_to_int(self.m1.low)
        z = x * y
        res = int_to_word(z)
        self._assign_reg('A', res)
        if byte_to_int(self.regs['AL'].value) == z:
            self.flags.carry = False
            self.flags.overflow = False
        else:
            self.flags.carry = True
            self.flags.overflow = True

    def exec_imulw(self):
        x = word_to_int(self._read_reg('A'))
        y = word_to_int(self.m1.read())
        z = x * y
        zh, zl = int_to_dword(z)
        self._assign_reg('D', zh)
        self._assign_reg('A', zl)
        if word_to_int(self._read_reg('A')) == z:
            self.flags.carry = False
            self.flags.overflow = False
        else:
            self.flags.carry = True
            self.flags.overflow = True

    def exec_mulb(self):
        x = byte_to_uint(self.regs['AL'].value)
        y = byte_to_uint(self.m1.low)
        z = x * y
        res = uint_to_word(z)
        self._assign_reg('A', res)
        if self.regs['AH'].value == '0' * 8:
            self.flags.carry = False
            self.flags.overflow = False
        else:
            self.flags.carry = True
            self.flags.overflow = True

    def exec_mulw(self):
        x = word_to_uint(self._read_reg('A'))
        y = word_to_uint(self.m1.read())
        z = x * y
        zh, zl = uint_to_dword(z)
        self._assign_reg('D', zh)
        self._assign_reg('A', zl)
        if self._read_reg('D') == '0' * 16:
            self.flags.carry = False
            self.flags.overflow = False
        else:
            self.flags.carry = True
            self.flags.overflow = True

    def exec_incb(self):
        res = ['0'] * 8
        carry = True
        for i in range(7, -1, -1):
            if i == 7:
                self.flags.overflow = carry
            if carry:
                if self.m1.low[i] == '0':
                    res[i] = '1'
                    carry = False
                else:
                    res[i] = '0'
                    carry = True
            else:
                res[i] = self.m1.low[i]
        self.m3.low = ''.join(res)
        self.flags.sign = self.m3.low[0]
        self.flags.carry = carry
        self.flags.zero = self.m3.low == '0' * 8

    def exec_incw(self):
        res = ['0'] * 16
        carry = True
        for i in range(15, -1, -1):
            if i == 15:
                self.flags.overflow = carry
            if carry:
                if self.m1.read()[i] == '0':
                    res[i] = '1'
                    carry = False
                else:
                    res[i] = '0'
            else:
                res[i] = self.m1.read()[i]
                
        self.m3.assign(''.join(res))
        self.flags.sign = self.m3.high[0]
        self.flags.carry = carry
        self.flags.zero = self.m3.read() == '0' * 16

    # TODO: IRET

    def exec_va(self):
        self.flags.verdict = not self.flags.carry and not self.flags.zero

    def exec_vc(self):
        self.flags.verdict = self.flags.carry

    def exec_vz(self):
        self.flags.verdict = self.flags.zero

    def exec_vo(self):
        self.flags.verdict = self.flags.overflow

    def exec_vs(self):
        self.flags.verdict = self.flags.sign

    def exec_vg(self):
        self.flags.verdict = not self.flags.zero and (self.flags.sign == self.flags.overflow)

    def exec_vl(self):
        self.flags.verdict = self.flags.sign != self.flags.overflow
    
    def exec_nv(self):
        self.flags.verdict = not self.flags.verdict

    def exec_jmp(self): # Used
        assert(self.regs['SPH'].value[0] == '1')
        self.ip = self.m1.read()

    def exec_jv(self): # Used
        if self.flags.verdict:
            self.ip = self.m1.read()

    def exec_rmem(self): # Used
        if self.mp[0] == '1':
            self.m3.low = self.data[self.mp]
        else:
            self.m3.low = self.const[self.mp]

    def exec_wmem(self):
        assert self.mp[0] == '1'
        # assert self.mp in self.data
        self.data[self.mp] = self.m2.low

    def exec_smp(self):
        self.mp = self.m1.read()

    def exec_imp(self):
        self.mp = inc_bits(self.mp)

    def exec_dmp(self):
        self.mp = dec_bits(self.mp)

    def exec_negb(self):
        res = ['0'] * 8
        for i in range(8):
            res[i] = '0' if self.m1.low[i] == '1' else '1'
        m1 = self.m1.low
        self.m1.low = ''.join(res)
        self.exec_incb()
        self.m3.low = self.m1.low
        self.m1.low = m1

    def exec_negw(self):
        res = ['0'] * 16
        for i in range(16):
            res[i] = '0' if self.m1.read()[i] == '1' else '1'
        m1 = self.m1.read()
        self.m1.assign(''.join(res))
        self.exec_incw()
        self.m3.assign(self.m1.read())
        self.m1.assign(m1)

    def exec_notb(self):
        res = ['0'] * 8
        for i in range(8):
            res[i] = '0' if self.m1.low[i] == '1' else '1'
        self.m3.low = ''.join(res)

    def exec_notw(self):
        res = ['0'] * 16
        for i in range(16):
            res[i] = '0' if self.m1.read()[i] == '1' else '1'
        self.m3.assign(''.join(res))

    def exec_orb(self):
        self._bitwiseb(or_bits)

    def exec_orw(self):
        self._bitwisew(or_bits)

    def exec_sarb(self):
        carry = self.m1.low[0] == '1'
        res = ['0'] * 8
        for i in range(8):
            if carry:
                res[i] = '1'
            carry = self.m1.low[i] == '1'
        self.flags.carry = carry
        self.flags.overflow = res[0] != self.m1.low[0]
        self.m3.low = ''.join(res)

    def exec_sarw(self):
        carry = self.m1.low[0] == '1'
        res = ['0'] * 16
        for i in range(16):
            if carry:
                res[i] = '1'
            carry = self.m1.read()[i] == '1'
        self.flags.carry = carry
        self.flags.overflow = res[0] != self.m1.high[0]
        self.m3.assign(''.join(res))

    def exec_shlb(self): # Used
        carry = False
        res = ['0'] * 8
        for i in range(7, -1, -1):
            if carry:
                res[i] = '1'
            carry = self.m1.low[i] == '1'
        self.flags.carry = carry
        self.flags.overflow = res[0] != self.m1.low[0]
        self.m3.low = ''.join(res)
        
    def exec_shlw(self): # Used
        carry = False
        res = ['0'] * 16
        for i in range(15, -1, -1):
            if carry:
                res[i] = '1'
            carry = self.m1.read()[i] == '1'
        self.flags.carry = carry
        self.flags.overflow = res[0] != self.m1.high[0]
        self.m3.assign(''.join(res))

    def exec_shrb(self):
        carry = False
        res = ['0'] * 8
        for i in range(8):
            if carry:
                res[i] = '1'
            carry = self.m1.low[i] == '1'
        self.flags.carry = carry
        self.flags.overflow = res[0] != self.m1.low[0]
        self.m3.low = ''.join(res)

    def exec_shrw(self):
        carry = False
        res = ['0'] * 16
        for i in range(16):
            if carry:
                res[i] = '1'
            carry = self.m1.read()[i] == '1'
        self.flags.carry = carry
        self.flags.overflow = res[0] != self.m1.high[0]
        self.m3.assign(''.join(res))

    def exec_stc(self):
        self.flags.carry = True

    def _subb(self, with_borrow=False):
        res = ['0'] * 8
        borrow = False
        if with_borrow:
            borrow = self.flags.carry
        for i in range(7, -1, -1):
            if i == 7:
                self.flags.overflow = borrow
            total = 1 if self.m1.low[i] == '1' else 0
            total -= 1 if self.m2.low[i] == '1' else 0
            if borrow:
                total -= 1
            if total == 0:
                borrow = False
            elif total == 1:
                borrow = False
                res[i] = '1'
            elif total == -1:
                borrow = True
                res[i] = '1'
            elif total == -2:
                borrow = True
            else:
                assert False
        self.flags.carry = borrow
        self.flags.sign = res[0] == '1'
        self.m3.low = ''.join(res)
        self.flags.zero = self.m3.low == '0' * 8

    def _subw(self, with_borrow=False):
        res = ['0'] * 16
        borrow = False
        if with_borrow:
            borrow = self.flags.carry
        for i in range(15, -1, -1):
            if i == 15:
                self.flags.overflow = borrow
            total = 1 if self.m1.read()[i] == '1' else 0
            total -= 1 if self.m2.read()[i] == '1' else 0
            if borrow:
                total -= 1
            if total == 0:
                borrow = False
            elif total == 1:
                borrow = False
                res[i] = '1'
            elif total == -1:
                borrow = True
                res[i] = '1'
            elif total == -2:
                borrow = True
            else:
                assert False
        self.flags.carry = borrow
        self.flags.sign = res[0] == '1'
        self.m3.assign(''.join(res))
        self.flags.zero = self.m3.read() == '0' * 16

    def exec_sbbb(self):
        self._subb(with_borrow=True)

    def exec_sbbw(self):
        self._subw(with_borrow=True)

    def exec_subb(self):
        self._subb(with_borrow=False)

    def exec_subw(self):
        self._subw(with_borrow=False)

    def exec_testb(self):
        m3 = self.m3.low
        self.exec_andb()
        self.m3.low = m3

    def exec_testw(self):
        m3 = self.m3.read()
        self.exec_andw()
        self.m3.assign(m3)

    def exec_xorb(self):
        self._bitwiseb(xor_bits)

    def exec_xorw(self):
        self._bitwisew(xor_bits)

    def exec_puts(self):
        m3 = self.m3.low
        self.m1.assign(self._read_reg('A'))
        self.exec_smp()
        self.exec_rmem()
        while self.m3.low != '0' * 8:
            print(chr(byte_to_uint(self.m3.low)), end='')
            self.exec_imp()
            self.exec_rmem()
        self.m3.low = m3

    def exec_putint(self):
        print(str(word_to_int(self._read_reg('A'))), end='')

    def exec_putc(self):
        print(chr(byte_to_uint(self.regs['AL'].value)), end='')

    def exec_gets(self):
        m2 = self.m2.low
        s = input()
        self.m1.assign(self._read_reg('A'))
        self.exec_smp()
        for c in s:
            self.m2.low = uint_to_byte(ord(c))
            self.exec_wmem()
            self.exec_imp()
        self.m2.low = '0' * 8
        self.exec_wmem()
        self.m2.low = m2

    def exec_getint(self):
        self._assign_reg('A', int_to_word(int(input())))

    def exec_rand(self):
        r = random.randint(0, 2 ** 15 - 1)
        self._assign_reg('A', int_to_word(r))

    def exec_hlt(self):
        exit(0)


def run(pptasm_dict):
    vm = MachineState(pptasm_dict)
    while True:
        vm.step()

def test_verdict(cmd1, cmd2):
    print('Testing ' + cmd1 + ' and ' + cmd2)
    class Dummy:
        def __init__(self, flags):
            self.flags = flags
    d = Dummy(Flags())
    import random
    from copy import deepcopy
    for i in range(100):
        d.flags.carry = random.choice([True, False])
        d.flags.overflow = random.choice([True, False])
        d.flags.sign = random.choice([True, False])
        d.flags.zero = random.choice([True, False])
        d.flags.verdict = False
        d2 = deepcopy(d)
        MachineState.__dict__[cmd1](d)
        MachineState.__dict__[cmd2](d2)
        if d.flags.verdict == d2.flags.verdict:
            print('*** No match ***')
            return
    print('(match)')

def test():
    print('Hello')
    names = [k for k in MachineState.__dict__.keys() if k.startswith('exec_v')]
    for k in names:
        cmd = k[6:]
        if cmd[0] != 'n':
            test_verdict(k, 'exec_vn' + cmd)
    
    print(names)

def parse_file(file_path):
    with open(file_path, mode='rt') as file:
        lines = file.readlines()
        lines = [line.strip() for line in lines]
        lines = [line for line in lines if line]
    text = {}
    data = {}
    const = {}
    i = 0
    assert lines[i] == 'text:'
    i += 1
    while lines[i] != 'data:':
        parts = split_on_spaces(lines[i])
        text[parts[0]] = Instruction(parts[1], parts[2:])
        i += 1
    i += 1
    while lines[i] != 'const:':
        parts = split_on_spaces(lines[i])
        data[parts[0]] = parts[1]
        i += 1
    i += 1
    while i < len(lines):
        parts = split_on_spaces(lines[i])
        const[parts[0]] = parts[1]
        i += 1
    return MachineState(text, data, const)    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run .pptasm files')
    parser.add_argument('file', help='.pptasm file to run', type=str)
    args = parser.parse_args()
    vm = parse_file(args.file)
    while True:
        try:
            vm.step()
        except SystemExit:
            exit(0)
        except:
            raise Exception('Error while running line %s' % vm.ip)