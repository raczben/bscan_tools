#!/usr/bin/env python3

import json
import fileinput
import sys
import argparse
import os
import subprocess
import logging
 
import pprint

# The directory of this script file.
__here__ = os.path.dirname(os.path.realpath(__file__))
__bscan_proc__ = os.path.join(__here__, '..')
if __name__ == "__main__":
    sys.path.insert(0, __bscan_proc__)

import bscan_tools.core

logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)


pp = pprint.PrettyPrinter(indent=4)


parser = argparse.ArgumentParser(description="Parse and visualize openocd's BSCAN data.")
parser.add_argument('bsdl_file', nargs=1, help='Path to BSDL file.')
parser.add_argument('oocd_hex_dump', nargs='+', help='File with boundary scan dump HEX values.')
parser.add_argument('-r', '--rename', default=None, help='File with port name renamings')
parser.add_argument('--bsdl-cache', default=None, help='Path to store parsed bsdl-files.')
args = parser.parse_args()

rename_filename = args.rename
bsdl_file = args.bsdl_file[0]
oocd_hex_dump_files = args.oocd_hex_dump


#============================================================

pin_renamings = {}
if rename_filename:
    with open(rename_filename) as rename_file:
        for line in rename_file:
            if len(line.strip()) == 0 or line.strip()[0] == "#":
                continue
            pin_name, value = line.split(":")
            pin_renamings[pin_name.strip()] = value.strip()

#============================================================

all_ports = {}
all_bregs_list = []

# Merge all BSDL port and pin data into 1 struct

data = bscan_tools.core.load_bsdl(bsdl_file, args.bsdl_cache)


for log_port_segment in data["logical_port_description"]:
    for port_name in log_port_segment["identifier_list"]:
        all_ports[port_name] = {
                    "pin_type"          : log_port_segment["pin_type"],
                    "port_dimension"    : log_port_segment["port_dimension"],
                    "pin_info"          : {},
                    "bscan_regs"        : []
                }

for port2pin in data["device_package_pin_mappings"][0]["pin_map"]:
    all_ports[port2pin["port_name"]]["pin_info"] = port2pin

fixed_boundary_stmts = data["boundary_scan_register_description"]["fixed_boundary_stmts"]
bscan_length = int(fixed_boundary_stmts["boundary_length"])

for bscan_reg in fixed_boundary_stmts["boundary_register"]:
    all_bregs_list.append(bscan_reg)

for bscan_reg in all_bregs_list:
    port_name = bscan_reg["cell_info"]["cell_spec"]["port_id"]
    bscan_reg["values"] = []
    if port_name != "*":
        all_ports[port_name]["bscan_regs"].append(bscan_reg)

        input_or_disable_spec = bscan_reg["cell_info"]["input_or_disable_spec"]
        if input_or_disable_spec:
            all_ports[port_name]["bscan_regs"].append(all_bregs_list[int(input_or_disable_spec["control_cell"])])


    #pp.pprint(all_ports)
    #print(json.dumps(data, indent=4))


for filename in oocd_hex_dump_files:

    for line in open(filename).readlines():
        line = line.strip()
        if len(line) == 0:
            continue

        if line.strip()[0] == "#":
            continue

        hex_str = line
        breg_val = int(hex_str, 16)

        for port_name in sorted(all_ports.keys()):
            port_info = all_ports[port_name]
            if len(port_info["bscan_regs"]) == 0:
                continue

            for bscan_reg in port_info["bscan_regs"]:
                cell_nr = int(bscan_reg["cell_number"])
                val     = (breg_val >> cell_nr)&1
                bscan_reg["values"].append(val)


# Sort by renamed ports to keep ports with same name together
all_renamed_ports = {}
for port_name in all_ports.keys():
    port_info       = all_ports[port_name]
    pin_name        = port_info["pin_info"]["pin_list"][0]
    renamed_port    = pin_renamings.get(pin_name, port_name)

    all_renamed_ports[renamed_port] = port_name

for renamed_port in sorted(all_renamed_ports.keys()):
    port_name = all_renamed_ports[renamed_port]
    port_info = all_ports[port_name]

    bscan_regs = port_info["bscan_regs"]
    if len(bscan_regs) == 0:
        continue

    pin_name   = port_info["pin_info"]["pin_list"][0]
    renaming   = pin_renamings.get(pin_name, port_name)

    for bscan_reg in bscan_regs:

        dir     = bscan_reg["cell_info"]["cell_spec"]["function"]
        values  = bscan_reg["values"]

        print("{:<5} {:<20}: {:<10}: ".format(pin_name, "("+renaming+")", dir), end=" ")

        all_values = {}
        for val in values:
            all_values[val] = 1
            print(val, end=" ")

        if len(all_values.keys()) > 1:
            print("!", end=" ")

        print()

    print()
