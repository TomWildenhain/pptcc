import argparse
import subprocess

parser = argparse.ArgumentParser(description='Compile C to PPT CPU microcode.')
parser.add_argument('file', help='.c files to compile', type=str)
parser.add_argument('-o', help='output obj from wasm', action='store_true')
parser.add_argument('-l', help='output listing file from wdis', action='store_true')
parser.add_argument('-a', help='output pptasm file runnable on pptvm', action='store_true')

args = parser.parse_args()
print(args.file)

# -0 -s

WATCOM_PATH = 'C:\\WATCOM\\binnt\\%s.exe'

def watcom_compile(source_file, output_path):
    subprocess.check_call([WATCOM_PATH % 'wcc', '-0', '-s', '-fo=' + output_path, source_file])

def watcom_dis(obj_file, output_masm_path, output_gas_path):
    subprocess.check_call([WATCOM_PATH % 'wdis', '-a', '-l=' + output_masm_path, obj_file])
    subprocess.check_call([WATCOM_PATH % 'wdis', '-au', '-l=' + output_gas_path, obj_file])

def ppt_compile(ppt_asm_file, output_path):
    pass

def main():
    print('*** Compiling c code ***')
    watcom_compile(args.file, 'test.myout')
    print('*** Disassembling obj file ***')
    watcom_dis('test.myout', 'mytest.masm', 'mytest.gas')
    print('*** Compiling pptasm ***')
    ppt_asm('mytest.lst', 'sometest.pptasm')

def ppt_asm(listing_file, output_path):
    pass



if __name__ == '__main__':
    main()
