
# !/usr/bin/env python3

import sys
import argparse
import os
import logging

# The directory of this script file.
__here__ = os.path.dirname(os.path.realpath(__file__))
__bscan_proc__ = os.path.join(__here__, '..')
if __name__ == "__main__":
    sys.path.insert(0, __bscan_proc__)

import bscan_tools.core

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


def generate_tcl(bsdl_file, bsdl_cache=None):
    #
    # Fetch IDCODE, instruction length, and instruction opcodes.
    #

    data = bscan_tools.core.load_bsdl(bsdl_file, bsdl_cache)

    # Based on https://stackoverflow.com/a/3495395/2506522
    data['optional_register_description'] = {
        k: v for d in data['optional_register_description'] for k, v in d.items()}
    id_code = ''.join(data['optional_register_description']['idcode_register'])
    logging.debug(f'IDCODE: {id_code}')
    ir_length = int(data['instruction_register_description']['instruction_length'])
    logging.debug(f'IRLENGTH: {ir_length}')
    boundary_length = int(
        data['boundary_scan_register_description']['fixed_boundary_stmts']['boundary_length'])
    logging.debug(f'BOUNDARY_LENGTH: {boundary_length}')
    data['instruction_register_description']['instruction_opcodes'] = {
        d['instruction_name']: ''.join(d['opcode_list']) for d in
        data['instruction_register_description']['instruction_opcodes']}
    instruction_opcodes = {
        k: int(v, 2) for k, v in
        data['instruction_register_description']['instruction_opcodes'].items()}

    logging.debug('OPCODES:')
    for instr, opcode in instruction_opcodes.items():
        logging.debug(f'  {instr}: {opcode}')

    #
    # Generate device/part TCL
    #

    bname = os.path.basename(bsdl_file)
    device_name = os.path.splitext(bname)[0]
    tcl_dev_file_content = []
    tcl_dev_file_content += [f'# Generated with bscan_proc from {bsdl_file}']

    tcl_dev_file_content += ['']
    tcl_dev_file_content += ['# ID code']
    tcl_dev_file_content += [f'set {device_name}_IDCODE {id_code}']

    tcl_dev_file_content += ['']
    tcl_dev_file_content += ['# Instruction length']
    tcl_dev_file_content += [f'set {device_name}_IRLEN {ir_length}']

    tcl_dev_file_content += ['']
    tcl_dev_file_content += ['# Boundary length']
    tcl_dev_file_content += [f'set {device_name}_BOUNDARY_LENGTH {boundary_length}']

    tcl_dev_file_content += ['']
    tcl_dev_file_content += ['# Instruction opcodes']
    for instr, opcode in instruction_opcodes.items():
        tcl_dev_file_content += [f'set {device_name}_{instr} {hex(opcode)}']

    tcl_dev_file_name = f'{device_name}_dev.tcl'
    with open(tcl_dev_file_name, 'w') as tcl_dev_file:
        tcl_dev_file.write(os.linesep.join(tcl_dev_file_content))


def main():
    parser = argparse.ArgumentParser(description="Generate device/part TCL from BSDL file.")
    parser.add_argument('bsdl_file', nargs=1, help='Path to BSDL file.')
    parser.add_argument('--bsdl-cache', default=None, help='Path to store parsed bsdl-files.')
    args = parser.parse_args()
    generate_tcl(args.bsdl_file[0], args.bsdl_cache)


if __name__ == "__main__":
    main()
