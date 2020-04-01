import unittest
import pptvm
import copy

class TestBitConversions(unittest.TestCase):
    def test_byte_v_uint(self):
        cases = [
            ('00000000', 0), 
            ('10000001', 2**7+1), 
            ('11111111', 2**8-1),
            ('00000101', 5)
        ]
        for b, i in cases:
            self.assertEqual(pptvm.byte_to_uint(b), i)
            self.assertEqual(pptvm.uint_to_byte(i), b)

    def test_byte_v_int(self):
        cases = [
            ('00000000', 0), 
            ('10000000', -2**7), 
            ('11111111', -1),
            ('00000101', 5),
            ('11111011', -5)
        ]
        for b, i in cases:
            self.assertEqual(pptvm.byte_to_int(b), i)
            self.assertEqual(pptvm.int_to_byte(i), b)

    def test_dword_v_int(self):
        cases = [
            ('00000000', '00000000', '00000000', '00000000', 0),
            ('00000000', '00000000', '00000000', '00000101', 5),
            ('11111111', '11111111', '11111111', '11111111', -1),
            ('00000000', '00000001', '00000000', '00000000', 2**16),
        ]
        for b1, b2, b3, b4, i in cases:
            self.assertEqual(pptvm.dword_to_int(b1+b2+b3+b4), i)
            h, l = pptvm.int_to_dword(i)
            self.assertEqual(h + l, b1+b2+b3+b4)

class TestMachineInstructions(unittest.TestCase):
    def setUp(self):
        const_dict = {pptvm.uint_to_word(i+2**15): pptvm.uint_to_word(i*10) for i in range(20)}
        data_dict = {pptvm.uint_to_word(i): pptvm.uint_to_word(i*20) for i in range(20)}
        pptasm_dict = {
            'code': {},
            'const': const_dict,
            'data': data_dict,
        }
        self.machine_state = pptvm.MachineState(pptasm_dict)


if __name__ == '__main__':
    unittest.main()