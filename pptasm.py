from pptutils import *
import json
import argparse

def find_line(lines, target):
    if target not in lines:
        raise Exception('Could not find line "%s" in file' % target)
    return lines.index(target)

def parse_line(line):
    line = line.strip()
    if ' ' not in line:
        return line, []
    i = line.find(' ')
    inst = line[:i]
    arg_str = line[i:].strip()
    args = [a.strip() for a in arg_str.split(',')]
    args2 = []
    for a in args:
        if len(args2) > 0 and '(' in args2[-1] and ')' not in args2[-1]:
            args2[-1] = args2[-1] + ',' + a
        else:
            args2.append(a)
    return inst, args2

class X86LabeledRegion:
    def __init__(self, label, lines):
        self.label = label
        self.lines = lines

    def __repr__(self):
        return 'X86LabeledRegion(%s, <%d lines>)' % (repr(self.label), len(self.lines))

def parse_section_labels(section_name, lines):
    labeled_regions = [X86LabeledRegion(section_name, [])]
    for l in lines:
        if l.startswith(' '):
            labeled_regions[-1].lines.append(l)
        else:
            assert l.endswith(':')
            labeled_regions.append(X86LabeledRegion(l[:-1], []))
    return labeled_regions

def assemble_gas(file_path, output_path):
    with open(file_path, mode='rt') as file:
        lines = file.readlines()
        lines = [line.replace('\t', ' ').rstrip() for line in lines]
        lines = [line for line in lines if line]
    section_map = {}
    section = []
    section_map['INITIAL'] = section
    for l in lines:
        if l.startswith('.new_section'):
            section = []
            inst, args = parse_line(l)
            section_map[args[0]] = section
        else:
            section.append(l)
    if '_TEXT' not in section_map:
        raise Exception('No _TEXT section in assembly code')
    text_section = section_map['_TEXT']
    const_section = section_map.get('CONST', [])
    data_section = section_map.get('_DATA', [])
    labeled_text = parse_section_labels('_TEXT', text_section)
    labeled_const = parse_section_labels('CONST', const_section)
    labeled_data = parse_section_labels('_DATA', data_section)
    labels_to_offsets = get_label_offsets(labeled_data, 2**15)
    labels_to_offsets.update(get_label_offsets(labeled_const, 0))
    
    code = [
        PptInstruction('CONSTH', '11111111'),
        PptInstruction('CONSTL', '11111100'),
        PptInstruction('STOREH', 'SPH'),
        PptInstruction('STOREL', 'SPL'),
        PptInstruction('LOAD1H', 'M3H'),
        PptInstruction('LOAD1L', 'M3L'),
        PptInstruction('EXEC', 'SMP'),
        PptInstruction('CONSTL', Immediate(0, 'w', 'X$0')),
        PptInstruction('LOAD2L', 'M3L'),
        PptInstruction('EXEC', 'WMEM'),
        PptInstruction('EXEC', 'IMP'),
        PptInstruction('CONSTH', Immediate(0, 'w', 'X$0')),
        PptInstruction('LOAD2L', 'M3H'),
        PptInstruction('EXEC', 'WMEM'),
        PptInstruction('CONSTH', Immediate(0, 'w', 'main_')),
        PptInstruction('CONSTL', Immediate(0, 'w', 'main_')),
        PptInstruction('LOAD1H', 'M3H'),
        PptInstruction('LOAD1L', 'M3L'),
        PptInstruction('EXEC', 'JMP'),
    ]
    labels_to_offsets['X$0'] = len(code)
    code += [PptInstruction('EXEC', 'HLT')]
    for region in labeled_text:
        labels_to_offsets[region.label] = len(code)
        for line in region.lines:
            try:
                new_code = code_for_line(line, len(code))
            except SegmentRegisterException as e:
                print('Warning: skipping line containing segment register "%s"' % e.message)
                continue
            new_code[0].comment = condense_spaces(line)
            code += new_code

    for inst in code:
        if inst.cmd == 'CONSTL':
            assert inst.arg is not None
        if isinstance(inst.arg, Immediate):
            h = inst.arg.to_binary(labels_to_offsets)
            if inst.cmd == 'CONSTH':
                h = h[:8]
            elif inst.cmd == 'CONSTL':
                h = h[-8:]
            assert len(h) == 8
            inst.arg = h
    data = read_data_section(labeled_data, labels_to_offsets)
    const = read_data_section(labeled_const, labels_to_offsets)

    lines = []
    lines.append('text:')
    for i in range(len(code)):
        lines.append('    ' + int_to_word(i) + '    ' + str(code[i]))
    lines.append('')
    lines.append('data:')
    for i in range(len(data)):
        lines.append('    ' + int_to_word(i+2**15) + '    ' + data[i])
    lines.append('')
    lines.append('const:')
    for i in range(len(const)):
        lines.append('    ' + int_to_word(i) + '    ' + const[i])

    with open(output_path, mode='wt') as file:
        file.write('\n'.join(lines))
    

def get_label_offsets(labeled_const_or_data, initial_byte_offset):
    byte_offset = initial_byte_offset
    labels_to_offsets = {}
    for region in labeled_const_or_data:
        labels_to_offsets[region.label] = byte_offset
        for l in region.lines:
            inst, args = parse_line(l)
            if inst == '.byte':
                byte_offset += len(args)
            elif inst == '.word':
                byte_offset += 2 * len(args)
            elif inst == '.ascii':
                byte_offset += sum(data_string_len(a) for a in args)
            elif inst in ['.asciiz', '.string']:
                byte_offset += sum(1+data_string_len(a) for a in args)
            else:
                raise Exception('Unidentified line "%s"' % l)
    return labels_to_offsets

def read_byte_data(arg, offsets):
    if arg.startswith('0x'):
        return [int_to_byte(hex_to_int(arg))]
    else:
        return [Immediate.parse(arg, 'b').to_binary(offsets)]

def read_word_data(arg, offsets):
    if arg.startswith('0x'):
        w = int_to_word(hex_to_int(arg))
    else:
        w = Immediate.parse(arg, 'w').to_binary(offsets)
    return [w[8:], w[:8]]

def read_asciiz_data(arg):
    assert arg[0] == '"'
    assert arg[-1] == '"'
    s = json.loads(arg)
    return [int_to_byte(ord(a)) for a in s] + ['0' * 8]

def read_ascii_data(arg):
    assert arg[0] == '"'
    assert arg[-1] == '"'
    s = json.loads(arg)
    return [int_to_byte(ord(a)) for a in s]


def read_data_section(labeled_const_or_data, labels_to_offsets):
    data = []
    for region in labeled_const_or_data:
        for l in region.lines:
            inst, args = parse_line(l)
            if inst == '.byte':
                for a in args:
                    data += read_byte_data(a.strip(), labels_to_offsets)
            elif inst == '.word':
                for a in args:
                    data += read_word_data(a.strip(), labels_to_offsets)
            elif inst == '.ascii':
                for a in args:
                    data += read_ascii_data(a.strip())
            elif inst in ['.asciiz', '.string']:
                for a in args:
                    data += read_asciiz_data(a.strip())
            else:
                raise Exception('Unidentified line "%s"' % l)
    return data

def data_string_len(string):
    assert string[0] == '"'
    assert string[-1] == '"'
    return len(json.loads(string))

class SegmentRegisterException(Exception):
    def __init__(self, message):
        self.message = message

def code_for_line(line, offset):
    inst, args = parse_line(line)
    cmd = inst.upper()
    size = 'b' if inst[-1] == 'b' else 'w'
    def parse_args(is_branch_operand=False):
        parsed_args = []
        for a in args:
            try:
                parsed_args.append(X86InstructionOperand(a, size, is_branch_operand))
            except:
                if a in ['%ds', '%es', '%ss', '%cs']:
                    raise SegmentRegisterException(line)
                else:
                    raise Exception('Failure parsing operand "%s" for line "%s"' % (a, line))
        return parsed_args
    if cmd in unary_commands_w:
        return code_for_unary_cmd_w(parse_args(), cmd)
    if cmd in unary_commands_b:
        return code_for_unary_cmd_b(parse_args(), cmd)
    if cmd in binary_commands_w:
        return code_for_binary_cmd_w(parse_args(), cmd)
    if cmd in binary_commands_b:
        return code_for_binary_cmd_b(parse_args(), cmd)
    if cmd in nullary_commands:
        return [PptInstruction('EXEC', cmd)]
    if cmd.startswith('J') and cmd[1:] in cond_jmp_suffixes:
        return code_for_cond_jmp(parse_args(True), cmd)
    if cmd.startswith('J') and cmd[1:] in cond_jump_suffix_map:
        suffix = cond_jump_suffix_map[cmd[1:]]
        return code_for_cond_jmp(parse_args(True), 'J' + suffix)
    if cmd.startswith('JN') and cmd[2:] in cond_jmp_suffixes:
        return code_for_cond_jmp(parse_args(True), cmd)
    if cmd.startswith('JN') and cmd[2:] in cond_jump_suffix_map:
        suffix = cond_jump_suffix_map[cmd[2:]]
        if suffix.startswith('N'):
            return code_for_cond_jmp(parse_args(True), 'J' + suffix[1:])
        else:
            return code_for_cond_jmp(parse_args(True), 'JN' + suffix)
    if cmd == 'CALL':
        return code_for_cmd_call(parse_args(True), offset)
    key = 'code_for_cmd_' + inst
    if key not in globals():
        raise Exception('Unrecognized command "%s"' % inst)
    return globals()[key](parse_args(cmd in cmds_with_branch_ops))

cmds_with_branch_ops = ['JMP', 'CALL']

class Immediate:
    def __init__(self, offset, size, label=None):
        self.offset = offset
        self.label = label
        self.size = size

    def __repr__(self):
        if self.label is None:
            return str(self.offset)
        elif self.offset < 0:
            return self.label + str(self.offset)
        else:
            return self.label + '+' + str(self.offset)

    def __str__(self):
        return self.__repr__()

    def is_zero(self):
        return self.offset == 0 and self.label is None

    def to_binary(self, label_dict):
        i = self.offset
        if self.label is not None:
            if self.label not in label_dict:
                raise Exception('Unidentified label "%s"' % self.label)
            i += label_dict[self.label]
        if self.size == 'w':
            return int_to_word(i)
        else:
            return int_to_byte(i)

    @staticmethod
    def parse(asm_str, size):
        asm_str = asm_str.strip()
        def parse_num(string):
            if string.startswith('0x'):
                return hex_to_int(string)
            else:
                return int(string)
        if '-' in asm_str:
            label, offset = asm_str.split('-')
            if len(label) > 0:
                return Immediate(-parse_num(offset), size, label)
            else:
                return Immediate(-parse_num(offset), size)
        elif '+' in asm_str:
            label, offset = asm_str.split('+')
            assert len(label) > 0
            return Immediate(parse_num(offset), size, label)
        elif asm_str[0] in '0123456789':
            return Immediate(parse_num(asm_str), size)
        else:
            return Immediate(0, size, asm_str)

class X86InstructionOperand:
    def __init__(self, arg, size, is_branch_operand=False):
        self.immediate = Immediate(0, size)
        self.reg1 = None
        self.reg2 = None
        self.scale = 1
        if arg.startswith('*'):
            assert is_branch_operand
            arg = arg[1:]
            is_branch_operand = False
        if arg.startswith('$'):
            self.type = 'IMM'
            self.immediate = Immediate.parse(arg[1:], size)
        elif arg.startswith('%'):
            self.type = 'REG'
            self.reg1 = get_reg_prefix(arg[1:])
        elif '(' in arg:
            self.type = 'MEM'
            assert '(' in arg
            i = arg.find('(')
            j = arg.find(')')
            contents = arg[i+1:j]
            arg = arg[:i]
            parts = contents.split(',')
            if parts[0] != '':
                self.reg1 = get_reg_prefix(parts[0][1:])
            if len(parts) >= 2:
                assert parts[1].startswith('%')
                self.reg2 = get_reg_prefix(parts[1][1:])
            if len(parts) >= 3:
                assert parts[2] in ['1', '2', '4', '8']
                self.scale = int(parts[2])
            if arg != '':
                self.immediate = Immediate.parse(arg, size='w')
        else:
            if is_branch_operand:
                self.type = 'IMM'
                self.immediate = Immediate.parse(arg, size)
            else:
                self.type = 'MEM'
                self.immediate = Immediate.parse(arg, size='w')
            


    def __repr__(self):
        if self.type == 'IMM':
            return repr(self.immediate)
        elif self.type == 'REG':
            return self.reg1
        else:
            return repr(self.immediate) + '(' + repr(self.reg1) + ',' + repr(self.reg2) + ',' + repr(self.scale) + ')'

    def requires_calculation(self, for_write=False):
        if self.type != 'MEM':
            return False
        if self.reg2 is not None:
            return True
        if not self.immediate.is_zero() and self.reg1 is not None:
            return True
        if not self.immediate.is_zero() and for_write:
            return True
        return False

class PptInstruction:
    def __init__(self, cmd, arg=None):
        self.cmd = cmd
        self.arg = arg
        self.comment = None
    def __str__(self):
        res = pad_to_length(self.cmd, 8)
        if self.arg is not None:
            res += pad_to_length(str(self.arg), 10)
        if self.comment is not None:
            res += '# ' + self.comment
        return res

def get_reg_prefix(x86reg):
    x86reg = x86reg.lower()
    if len(x86reg) == 2 and x86reg[0] in ['a', 'b', 'c', 'd'] and x86reg[1] in ['l', 'h']:
        return x86reg.upper()
    return {
        'ax': 'A',
        'bx': 'B',
        'cx': 'C',
        'dx': 'D',
        'di': 'DI',
        'si': 'SI',
        'bp': 'BP',
        'sp': 'SP',
    }[x86reg]

def get_low_byte(x86reg):
    pass

def code_for_calc_address(operand, dst_reg='M4'):
    assert operand.type == 'MEM'
    code = []
    if operand.reg2 is not None:
        code += [
            PptInstruction('LOAD1H', operand.reg2 + 'H'),
            PptInstruction('LOAD1L', operand.reg2 + 'L'),
        ]
        if operand.scale > 1:
            if operand.scale == 2:
                cmd = 'SHIFTADDR1'
            elif operand.scale == 4:
                cmd = 'SHIFTADDR2'
            elif operand.scale == 8:
                cmd = 'SHIFTADDR3'
            else:
                assert False
            code += [
                PptInstruction('EXEC', cmd),
            ]
            if operand.reg1 is None and operand.immediate.is_zero():
                code += [
                    PptInstruction('STOREH', dst_reg + 'H'),
                    PptInstruction('STOREL', dst_reg + 'L'),
                ]
            else:
                code += [
                    PptInstruction('LOAD1H', 'M3H'),
                    PptInstruction('LOAD1L', 'M3L'),
                ]
    if operand.reg1 is not None:
        if operand.reg2 is None:
            code += [
                PptInstruction('LOAD1H', operand.reg1 + 'H'),
                PptInstruction('LOAD1L', operand.reg1 + 'L'),
            ]
            if operand.immediate.is_zero():
                code += [
                    PptInstruction('COPYH'),
                    PptInstruction('COPYL'),
                    PptInstruction('STOREH', dst_reg + 'H'),
                    PptInstruction('STOREL', dst_reg + 'L'),
                ]
        else:
            code += [
                PptInstruction('LOAD2H', operand.reg1 + 'H'),
                PptInstruction('LOAD2L', operand.reg1 + 'L'),
                PptInstruction('EXEC', 'ADDADDR'),
            ]
            if not operand.immediate.is_zero():
                code += [
                    PptInstruction('LOAD1H', 'M3H'),
                    PptInstruction('LOAD1L', 'M3L'),
                ]
            else:
                code += [
                    PptInstruction('STOREH', dst_reg + 'H'),
                    PptInstruction('STOREL', dst_reg + 'L'),
                ]
    if not operand.immediate.is_zero():
        if operand.reg1 is not None or operand.reg2 is not None:
            code += [
                PptInstruction('CONSTH', operand.immediate),
                PptInstruction('CONSTL', operand.immediate),
                PptInstruction('LOAD2H', 'M3H'),
                PptInstruction('LOAD2L', 'M3L'),
                PptInstruction('EXEC', 'ADDADDR'),
                PptInstruction('STOREH', dst_reg + 'H'),
                PptInstruction('STOREL', dst_reg + 'L'),
            ]
        else:
            code += [
                PptInstruction('CONSTH', operand.immediate),
                PptInstruction('CONSTL', operand.immediate),
                PptInstruction('STOREH', dst_reg + 'H'),
                PptInstruction('STOREL', dst_reg + 'L'),
            ]
    return code
        
def code_for_read_w(op, reg='1'):
    code = []
    if op.type == 'MEM':
        if op.requires_calculation():
            code += [
                PptInstruction('LOAD1H', 'M4H'),
                PptInstruction('LOAD1L', 'M4L'),
            ]
        elif op.reg1 is not None:
            code += [
                PptInstruction('LOAD1H', op.reg1 + 'H'),
                PptInstruction('LOAD1L', op.reg1 + 'L'),
            ]
        else:
            assert not op.immediate.is_zero()
            code += [
                PptInstruction('CONSTH', op.immediate),
                PptInstruction('CONSTL', op.immediate),
                PptInstruction('LOAD1H', 'M3H'),
                PptInstruction('LOAD1L', 'M3L'),
            ]
        code += [
            PptInstruction('EXEC', 'SMP'),
            PptInstruction('EXEC', 'RMEM'),
            PptInstruction('STOREL', 'M5L'),
            PptInstruction('EXEC', 'IMP'),
            PptInstruction('EXEC', 'RMEM'),
        ]
        if reg == '3':
            code += [
                PptInstruction('STOREL', 'M5H'),
                PptInstruction('LOAD1H', 'M5H'),
                PptInstruction('LOAD1L', 'M5L'),
                PptInstruction('COPYH'),
                PptInstruction('COPYL'),
            ]
        else:
            code += [
                PptInstruction('LOAD' + reg + 'H', 'M3L'),
                PptInstruction('LOAD' + reg + 'L', 'M5L'),
            ]
        return code
    elif op.type == 'REG':
        if reg == '3':
            return [
                PptInstruction('LOAD1H', op.reg1 + 'H'),
                PptInstruction('LOAD1L', op.reg1 + 'L'),
                PptInstruction('COPYH'),
                PptInstruction('COPYL'),
            ]
        else:
            return [
                PptInstruction('LOAD' + reg + 'H', op.reg1 + 'H'),
                PptInstruction('LOAD' + reg + 'L', op.reg1 + 'L'),
            ]
    elif op.type == 'IMM':
        if reg == '3':
            return [
                PptInstruction('CONSTH', op.immediate),
                PptInstruction('CONSTL', op.immediate),
            ]
        else:
            return [
                PptInstruction('CONSTH', op.immediate),
                PptInstruction('CONSTL', op.immediate),
                PptInstruction('LOAD' + reg + 'H', 'M3H'),
                PptInstruction('LOAD' + reg + 'L', 'M3L'),
            ]
    assert False


def code_for_read_b(op, reg='1'):
    code = []
    if op.type == 'MEM':
        if op.requires_calculation():
            code += [
                PptInstruction('LOAD1H', 'M4H'),
                PptInstruction('LOAD1L', 'M4L'),
            ]
        elif op.reg1 is not None:
            code += [
                PptInstruction('LOAD1H', op.reg1 + 'H'),
                PptInstruction('LOAD1L', op.reg1 + 'L'),
            ]
        else:
            assert not op.immediate.is_zero()
            code += [
                PptInstruction('CONSTH', op.immediate),
                PptInstruction('CONSTL', op.immediate),
                PptInstruction('LOAD1H', 'M3H'),
                PptInstruction('LOAD1L', 'M3L'),
            ]
        code += [
            PptInstruction('EXEC', 'SMP'),
            PptInstruction('EXEC', 'RMEM'),
        ]
        if reg != '3':
            code += [
                PptInstruction('LOAD' + reg + 'L', 'M3L'),
            ]
        return code
    elif op.type == 'REG':
        if reg == '3':
            return [
                PptInstruction('LOAD1L', op.reg1),
                PptInstruction('COPYL'),
            ]
        else:
            return [
                PptInstruction('LOAD' + reg + 'L', op.reg1),
            ]
    elif op.type == 'IMM':
        if reg == '3':
            return [PptInstruction('CONSTL', op.immediate)]
        else:
            return [
                PptInstruction('CONSTL', op.immediate),
                PptInstruction('LOAD' + reg + 'L', 'M3L'),
            ]
    assert False
        
def code_for_write_w(op):
    if op.type == 'MEM':
        code = []
        if op.requires_calculation(for_write=True):
            code += [
                PptInstruction('LOAD1H', 'M4H'),
                PptInstruction('LOAD1L', 'M4L'),
            ]
        else:
            code += [
                PptInstruction('LOAD1H', op.reg1 + 'H'),
                PptInstruction('LOAD1L', op.reg1 + 'L'),
            ]
        code += [
            PptInstruction('LOAD2L', 'M3L'),
            PptInstruction('EXEC', 'SMP'),
            PptInstruction('EXEC', 'WMEM'),
            PptInstruction('EXEC', 'IMP'),
            PptInstruction('LOAD2L', 'M3H'),
            PptInstruction('EXEC', 'WMEM'),
        ]
        return code
    elif op.type == 'REG':
        return [
            PptInstruction('STOREH', op.reg1 + 'H'),
            PptInstruction('STOREL', op.reg1 + 'L'),
        ]
    assert False

def code_for_write_b(op):
    if op.type == 'MEM':
        code = []
        if op.requires_calculation(for_write=True):
            code += [
                PptInstruction('LOAD1H', 'M4H'),
                PptInstruction('LOAD1L', 'M4L'),
            ]
        else:
            code += [
                PptInstruction('LOAD1H', op.reg1 + 'H'),
                PptInstruction('LOAD1L', op.reg1 + 'L'),
            ]
        code += [
            PptInstruction('LOAD2L', 'M3L'),
            PptInstruction('EXEC', 'SMP'),
            PptInstruction('EXEC', 'WMEM'),
        ]
        return code
    elif op.type == 'REG':
        return [
            PptInstruction('STOREL', op.reg1),
        ]
    assert False

def code_to_calc_address_if_needed(ops, write_to_dst=True):
    code = None
    for i in range(len(ops)):
        op = ops[i]
        last = i == len(ops) - 1
        if op.requires_calculation(for_write=(write_to_dst and last)):
            assert code is None
            code = code_for_calc_address(op)
    return code or []
    
def code_for_cmd_movw(inst_operands):
    src, dst = inst_operands
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_w(src, reg='3')
    code += code_for_write_w(dst)
    return code

def code_for_cmd_movb(inst_operands):
    src, dst = inst_operands
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_b(src, reg='3')
    code += code_for_write_b(dst)
    return code

def code_for_cmd_ctwd(_):
    return [PptInstruction('EXEC', 'CWD')]

def code_for_binary_cmd_b(inst_operands, cmd, write_to_dst=True):
    src, dst = inst_operands
    code = code_to_calc_address_if_needed(inst_operands)
    if src.type == 'MEM':
        code += code_for_read_b(src, reg='2')
    if dst.type == 'MEM':
        code += code_for_read_b(dst, reg='1')
    if src.type != 'MEM':
        code += code_for_read_b(src, reg='2')
    if dst.type != 'MEM':
        code += code_for_read_b(dst, reg='1')
    code += [PptInstruction('EXEC', cmd)]
    if write_to_dst:
        code += code_for_write_b(dst)
    return code

def code_for_binary_cmd_w(inst_operands, cmd, write_to_dst=True):
    src, dst = inst_operands
    code = code_to_calc_address_if_needed(inst_operands, write_to_dst)
    if src.type == 'MEM':
        code += code_for_read_w(src, reg='2')
    if dst.type == 'MEM':
        code += code_for_read_w(dst, reg='1')
    if src.type != 'MEM':
        code += code_for_read_w(src, reg='2')
    if dst.type != 'MEM':
        code += code_for_read_w(dst, reg='1')
    code += [PptInstruction('EXEC', cmd)]
    if write_to_dst:
        code += code_for_write_w(dst)
    return code

def code_for_unary_cmd_b(inst_operands, cmd):
    dst = inst_operands[0]
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_b(dst, reg='1')
    code += [PptInstruction('EXEC', cmd)]
    code += code_for_write_b(dst)
    return code

def code_for_unary_cmd_w(inst_operands, cmd):
    dst = inst_operands[0]
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_w(dst, reg='1')
    code += [PptInstruction('EXEC', cmd)]
    code += code_for_write_w(dst)
    return code

binary_commands_w = [
    'ADDW', 'ADCW', 'ANDW', 'ORW', 'XORW', 'SUBW', 'SBBW',
    'SARW', 'SHLW', 'SHRW'
]
binary_commands_b = [
    'ADDB', 'ADCB', 'ANDB', 'ORB', 'XORB', 'SUBB', 'SBBB',
    'SARB', 'SHLB', 'SHRB'
]
unary_commands_w = [
    'INCW', 'DECW', 'NOTW', 'NEGW', 
]
unary_commands_b = [
    'INCB', 'DECB', 'NOTB', 'NEGB', 
]

def code_for_cmd_nop(inst_operands):
    return []

def code_for_cmd_cmpw(inst_operands):
    return code_for_binary_cmd_w(inst_operands, 'CMPW', write_to_dst=False)

def code_for_cmd_cmpb(inst_operands):
    return code_for_binary_cmd_b(inst_operands, 'CMPB', write_to_dst=False)

def code_for_cmd_testw(inst_operands):
    return code_for_binary_cmd_w(inst_operands, 'TESTW', write_to_dst=False)

def code_for_cmd_testb(inst_operands):
    return code_for_binary_cmd_b(inst_operands, 'TESTB', write_to_dst=False)

def code_for_cmd_idivw(inst_operands):
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_w(inst_operands[0], reg='1')
    code += [PptInstruction('EXEC', 'IDIVW')]
    return code

def code_for_cmd_idivb(inst_operands):
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_b(inst_operands[0], reg='1')
    code += [PptInstruction('EXEC', 'IDIVB')]
    return code

def code_for_cmd_divw(inst_operands):
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_w(inst_operands[0], reg='1')
    code += [PptInstruction('EXEC', 'DIVW')]
    return code

def code_for_cmd_divb(inst_operands):
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_b(inst_operands[0], reg='1')
    code += [PptInstruction('EXEC', 'DIVB')]
    return code

def code_for_cmd_imulw(inst_operands):
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_w(inst_operands[0], reg='1')
    code += [PptInstruction('EXEC', 'IMULW')]
    return code

def code_for_cmd_imulb(inst_operands):
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_b(inst_operands[0], reg='1')
    code += [PptInstruction('EXEC', 'IMULB')]
    return code

def code_for_cmd_mulw(inst_operands):
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_w(inst_operands[0], reg='1')
    code += [PptInstruction('EXEC', 'MULW')]
    return code

def code_for_cmd_mulb(inst_operands):
    code = code_to_calc_address_if_needed(inst_operands)
    code += code_for_read_b(inst_operands[0], reg='1')
    code += [PptInstruction('EXEC', 'MULB')]
    return code

def code_for_cmd_leaw(inst_operands):
    addr, dst = inst_operands
    assert dst.type == 'REG'
    return code_for_calc_address(addr, dst.reg1)

def code_for_cmd_jmp(inst_operands):
    assert not inst_operands[0].requires_calculation()
    code = code_for_read_w(inst_operands[0], reg='1')
    code += [PptInstruction('EXEC', 'JMP')]
    return code

def code_for_cond_jmp(inst_operands, cmd='JNE'):
    suffix = cmd[1:]
    negate = suffix.startswith('N')
    if negate:
        suffix = suffix[1:]
    code = [PptInstruction('EXEC', 'V' + suffix)]
    if negate:
        code += [PptInstruction('EXEC', 'NV')]
    code += code_for_read_w(inst_operands[0], reg='1')
    code += [PptInstruction('EXEC', 'JV')]
    return code

cond_jmp_suffixes = ['A', 'C', 'Z', 'O', 'S', 'G', 'L']

cond_jump_suffix_map = {
    'AE': 'NC',
    'B': 'C',
    'BE': 'NA',
    'E': 'Z',
    'GE': 'NL',
    'LE': 'NG',
}

nullary_commands = [
    'CBW', 'CLC', 'CMC', 'STC', 'HLT'
]

def code_for_cmd_pushw(inst_operands):
    src = inst_operands[0]
    code = []
    if src.type == 'REG':
        return [
            PptInstruction('LOAD1H', 'SPH'),
            PptInstruction('LOAD1L', 'SPL'),
            PptInstruction('EXEC', 'DEC2W'),
            PptInstruction('STOREH', 'SPH'),
            PptInstruction('STOREL', 'SPL'),
            PptInstruction('LOAD1H', 'SPH'),
            PptInstruction('LOAD1L', 'SPL'),
            PptInstruction('EXEC', 'SMP'),
            PptInstruction('LOAD2L', src.reg1 + 'L'),
            PptInstruction('EXEC', 'WMEM'),
            PptInstruction('EXEC', 'IMP'),
            PptInstruction('LOAD2L', src.reg1 + 'H'),
            PptInstruction('EXEC', 'WMEM'),
        ]
    else:
        code += code_to_calc_address_if_needed(inst_operands, write_to_dst=False)
        code += code_for_read_w(src, reg='3')
        code += [
            PptInstruction('STOREH', 'M4H'),
            PptInstruction('STOREL', 'M4L'),
            PptInstruction('LOAD1H', 'SPH'),
            PptInstruction('LOAD1L', 'SPL'),
            PptInstruction('EXEC', 'DEC2W'),
            PptInstruction('STOREH', 'SPH'),
            PptInstruction('STOREL', 'SPL'),
            PptInstruction('LOAD1H', 'SPH'),
            PptInstruction('LOAD1L', 'SPL'),
            PptInstruction('EXEC', 'SMP'),
            PptInstruction('LOAD2L', 'M4L'),
            PptInstruction('EXEC', 'WMEM'),
            PptInstruction('EXEC', 'IMP'),
            PptInstruction('LOAD2L', 'M4H'),
            PptInstruction('EXEC', 'WMEM'),
        ]
        return code

def code_for_cmd_popw(inst_operands):
    dst = inst_operands[0]
    code = []
    if dst.type == 'REG':
        return [
            PptInstruction('LOAD1H', 'SPH'),
            PptInstruction('LOAD1L', 'SPL'),
            PptInstruction('EXEC', 'INC2W'),
            PptInstruction('STOREH', 'SPH'),
            PptInstruction('STOREL', 'SPL'),
            PptInstruction('EXEC', 'SMP'),
            PptInstruction('EXEC', 'RMEM'),
            PptInstruction('STOREL', dst.reg1 + 'L'),
            PptInstruction('EXEC', 'IMP'),
            PptInstruction('EXEC', 'RMEM'),
            PptInstruction('STOREL', dst.reg1 + 'H'),
        ]
    else:
        code += code_for_calc_address(dst)
        code += [
            PptInstruction('LOAD1H', 'SPH'),
            PptInstruction('LOAD1L', 'SPL'),
            PptInstruction('EXEC', 'INC2W'),
            PptInstruction('STOREH', 'SPH'),
            PptInstruction('STOREL', 'SPL'),
            PptInstruction('EXEC', 'SMP'),
            PptInstruction('EXEC', 'RMEM'),
            PptInstruction('STOREL', 'M5L'),
            PptInstruction('EXEC', 'IMP'),
            PptInstruction('EXEC', 'RMEM'),
            PptInstruction('STOREL', 'M5H'),

            PptInstruction('LOAD1H', 'M4H'),
            PptInstruction('LOAD1L', 'M4L'),
            PptInstruction('EXEC', 'SMP'),
            PptInstruction('LOAD2L', 'M5L'),
            PptInstruction('EXEC', 'WMEM'),
            PptInstruction('EXEC', 'IMP'),
            PptInstruction('LOAD2L', 'M5H'),
            PptInstruction('EXEC', 'WMEM'),
        ]
        return code

def code_for_cmd_call(inst_operands, offset=0):
    dst = inst_operands[0]
    if dst.type == 'IMM' and dst.immediate.label in builtin_commands_map:
        return [
            PptInstruction('EXEC', builtin_commands_map[dst.immediate.label])
        ]

    code = []
    i = Immediate(offset, size='w')
    if dst.type == 'MEM':
        code += code_to_calc_address_if_needed(inst_operands, write_to_dst=False)
        code += code_for_read_w(dst, reg='3')
        code += [
            PptInstruction('STOREH', 'M5H'),
            PptInstruction('STOREL', 'M5L'),
        ]
    code += [
        PptInstruction('LOAD1H', 'SPH'),
        PptInstruction('LOAD1L', 'SPL'),
        PptInstruction('EXEC', 'DEC2W'),
        PptInstruction('STOREH', 'SPH'),
        PptInstruction('STOREL', 'SPL'),
        PptInstruction('LOAD1H', 'SPH'),
        PptInstruction('LOAD1L', 'SPL'),
        PptInstruction('EXEC', 'SMP'),
        PptInstruction('CONSTH', i),
        PptInstruction('CONSTL', i),
        PptInstruction('LOAD2L', 'M3L'),
        PptInstruction('EXEC', 'WMEM'),
        PptInstruction('EXEC', 'IMP'),
        PptInstruction('LOAD2L', 'M3H'),
        PptInstruction('EXEC', 'WMEM'),
    ]
    if dst.type == 'MEM':
        code += [
            PptInstruction('LOAD1H', 'M5H'),
            PptInstruction('LOAD1L', 'M5L'),
        ]
    else:
        code += code_for_read_w(dst, reg='1')
    code += [
        PptInstruction('EXEC', 'JMP'),
    ]
    i.offset += len(code)
    return code

def code_for_cmd_ret(inst_operands):
    if len(inst_operands) > 0:
        op = inst_operands[0]
        assert op.type == 'IMM'
        op.immediate.offset += 2
    else:
        op = None
    code = []
    code += [
        PptInstruction('LOAD1H', 'SPH'),
        PptInstruction('LOAD1L', 'SPL'),
    ]
    if op is None:
        code += [
            PptInstruction('EXEC', 'INC2W'),
            PptInstruction('STOREH', 'SPH'),
            PptInstruction('STOREL', 'SPL'),
        ]
    else:
        code += [
            PptInstruction('CONSTH', op.immediate),
            PptInstruction('CONSTL', op.immediate),
            PptInstruction('EXEC', 'ADDADDR'),
            PptInstruction('STOREH', 'SPH'),
            PptInstruction('STOREL', 'SPL'),
        ]
    code += [
        PptInstruction('EXEC', 'SMP'),
        PptInstruction('EXEC', 'RMEM'),
        PptInstruction('LOAD1L', 'M3L'),
        PptInstruction('EXEC', 'IMP'),
        PptInstruction('EXEC', 'RMEM'),
        PptInstruction('LOAD1H', 'M3L'),
        PptInstruction('EXEC', 'JMP'),
    ]
    return code

builtin_commands_map = {
    'ppt_puts_': 'PUTS',
    'ppt_putint_': 'PUTINT',
    'ppt_putc_': 'PUTC',
    'ppt_gets_': 'GETS',
    'ppt_getint_': 'GETINT',
    'ppt_rand_': 'RAND',
}
    
# TODO: Optimize moving 0s
# TODO: Optimize moving between two addresses
# TODO: jumps, 
#       PUSH, POP, CALL, RET

#parse_masm('mytest.masm')
assemble_gas('mytest.gas', 'mytest2.pptasm')
#testline = 'cmpb $0x48,%al'
#code = code_for_line(testline, 0)
#print(code[0].arg.to_binary({}))
#print('\n'.join(str(c) for c in code))


if __name__ == '__main__':
    exit(0)
    parser = argparse.ArgumentParser(description='Convert .gas to .pptasm files')
    parser.add_argument('file', help='.gas file to assemble', type=str)
    args = parser.parse_args()
    args.file
    assemble_gas(args.file, 'mytest3.pptasm')
