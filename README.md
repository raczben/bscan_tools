
This project contains some JTAG boundary scan related tools that help me with reverse engineering PCB.

**Important: these are hacked up scripts for personal usage. They may very well only work for my specific case.**

# BSCAN_PROC

Requires the following input:

* BSDL file

    This is file provided by a chip company that describes the JTAG contents of the chip.

    If it contains IO port boundary scan registers, this information can be used to dump the
    state of the IO ports that have such a register.

* File with hex values of the JTAG boundary scan register, as dumped by OpenOCD.

    One line per hex value.

Output:

* A report that shows the values of all boundary scan register in chronological order


## Usage:

I have a PCB with an Intel Arria GX EP1AGX90EF115C6N chip.

### Preparation

* Download [its BDSL file](https://www.intel.com/content/dam/altera-www/global/en_US/others/support/devices/bsdl/EP1AGX90EF1152.BSD) 
from the [Intel website](https://www.intel.com/content/www/us/en/programmable/support/support-resources/download/board-layout-test/bsdl/arriagx.html).

    This will give you a file called `EP1AGX90EF1152.BSD`.

* Install requirements by 

    `python3 -m pip install -r requirements.txt`

* Create an OpenOCD file that describes the JTAG chain of the PCB.

    The [Comtech AHA363PCIE0301G board](https://tomverbeure.github.io/2020/06/14/AHA363-Reverse-Engineering.html)
	that I'm using has a relatively complex chain with 4 devices.

`./example/aha363.tcl`:

```tcl
jtag newtap AHA6310B_0          tap -irlen 5 -expected-id 0x10e1b291
jtag newtap AHA6310B_1          tap -irlen 5 -expected-id 0x10e1b291
jtag newtap EP1AGX90EF1152C6N   tap -irlen 10 -expected-id 0x021230dd
jtag newtap EPM570              tap -irlen 10 -expected-id 0x020a20dd
```

The `-expected-id` parameter specifies the JTAG IDCODE of the chips in the JTAG scan chain.
OpenOCD can figure out those values for you with an autoscan. For well documented chips (such
as Intel FPGAs and CPLDs), you can also find these values in their development documentation
or in their BDSL files.

* Create an OpenOCD file that prints the boundary scan register contents:

`./example/bscan_dump.tcl`:

```tcl
source EP1AGX90EF1152C6N_dev.tcl

irscan EP1AGX90EF1152C6N.tap $EP1AGX90EF1152_SAMPLE
drscan EP1AGX90EF1152C6N.tap $EP1AGX90EF1152_BOUNDARY_LENGTH 0
```

### Gather data

* Using OpenOCD, connect to the chip:

```console
tom@thinkcenter:~/projects/bscan_tools/example$ sudo /opt/openocd/bin/openocd -f /opt/openocd/share/openocd/scripts/interface/altera-usb-blaster.cfg -f ./aha363.tcl

Open On-Chip Debugger 0.10.0+dev-00930-g09eb941 (2019-09-16-21:01)
Licensed under GNU GPL v2
For bug reports, read
	http://openocd.org/doc/doxygen/bugs.html
Info : only one transport option; autoselect 'jtag'
Info : Listening on port 6666 for tcl connections
Info : Listening on port 4444 for telnet connections
Info : usb blaster interface using libftdi
Info : This adapter doesn't support configurable speed
Info : JTAG tap: AHA6310B.tap tap/device found: 0x10e1b291 (mfg: 0x148 (Agilent Technologies), part: 0x0e1b, ver: 0x1)
Info : JTAG tap: AHA6310B.tap tap/device found: 0x10e1b291 (mfg: 0x148 (Agilent Technologies), part: 0x0e1b, ver: 0x1)
Info : JTAG tap: EP1AGX90EF1152C6N.tap tap/device found: 0x021230dd (mfg: 0x06e (Altera), part: 0x2123, ver: 0x0)
Info : JTAG tap: EPM570.tap tap/device found: 0x020a20dd (mfg: 0x06e (Altera), part: 0x20a2, ver: 0x0)
Warn : gdb services need one or more targets defined
```

* Telnet to the OpenOCD session, and dump the boundary scan values:

```console
tom@thinkcenter:~/projects/bscan_tools/example$ telnet localhost 4444
Trying 127.0.0.1...
Connected to localhost.
Escape character is '^]'.
Open On-Chip Debugger
> source bscan_dump.tcl
5FAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEDBFDF7FFFDFEDB6DFFDF7DFFFF6DBFDF7FBFFFFFFFFFFFFFFFFFFFE9FED7FFFFFFDBFFBFDFEFFEDB6DFFFF6DFEDBFFBFDF7DB6DFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5FBE97FFFFBFFFFFFFDFFFFEFFFFFFFFFDF7FFFFFFFFFFFFFFFFF7DFFFF7FFFDFFDB6FFFFF7FFFFFFDBFFFFFFFFFFFFFFFFFFFFFFFFFDFFDFEFFFFFFFFFFF7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF6DC693FFFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF178FB7DB7FFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7DFFFBFDB6DFE082
> source bscan_dump.tcl
5FAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEDBFDF7FFFDFEDB6DFFDF7DFFFF6DBFDF7FBFFFFFFFFFFFFFFFFFFFE9FED7FFFFFFDBFFBFDFEFFEDB6DFFFF6DFEDBFFBFDF7DB6DFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5FBE97FFFFBFFFFFFFDFFFFEFFFFFFFFFDF7FFFFFFFFFFFFFFFFF7DFFFF7FFFDFFDB6FFFFF7FFFFFFFBFFFFFFFFFFFFFFFFFFFFFFFFFDFFDFEFFFFFFFFFFF7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF6DC693FFFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF178FB7DB7FFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7DFFFBFDB6DFE082
> source bscan_dump.tcl
5FAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEDBFDF7FFFDFEDB6DFFDF7DFFFF6DBFDF7FBFFFFFFFFFFFFFFFFFFFE9FED7FFFFFFDBFFBFDFEFFEDB6DFFFF6DFEDBFFBFDF7DB6DFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF5FBE97FFFFBFFFFFFFDFFFFEFFFFFFFFFDF7FFFFFFFFFFFFFFFFF7DFFFF7FFFDFFDB6FFFFF7FFFFFFFBFFFFFFFFFFFFFFFFFFFFFFFFFDFFDFEFFFFFFFFFFF7FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF6DC693FFFFFFFFFDFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF178FB7DB7FFFFFFFFFFFFFFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFF7DFFFBFDB6DFE082
```

* Store the values above in file `./example/bscan_values.txt`.

### Process Data

```sh
./bscan_proc.py EP1AGX90EF1152.bsdl bscan_values.txt > pin_report.txt
```

*If the parsed `EP1AGX90EF1152.bsdl` wasn't already in the local cache 
(located in `~/.cache/bscan_proc` by default), `bscan_proc.py` will also
create a `EP1AGX90EF1152_dev.tcl` with a number of useful constants
that can be used by OpenOCD.*

The `pin_report.txt` file will look like this:

```
...
AJ16  (IOAJ16)    : INPUT     :  1 1 1 1 1 1 1 1 1 1 
AJ16  (IOAJ16)    : OUTPUT3   :  1 1 1 1 1 1 1 1 1 1 
AJ16  (IOAJ16)    : CONTROL   :  1 1 1 1 1 1 1 1 1 1 

AJ19  (IOAJ19)    : INPUT     :  0 0 0 1 1 0 1 1 1 0 ! 
AJ19  (IOAJ19)    : OUTPUT3   :  1 1 1 1 1 1 1 1 1 1 
AJ19  (IOAJ19)    : CONTROL   :  1 1 1 1 1 1 1 1 1 1 

AJ20  (IOAJ20)    : INPUT     :  1 1 1 1 1 1 1 1 1 1 
AJ20  (IOAJ20)    : OUTPUT3   :  1 1 1 1 1 1 1 1 1 1 
AJ20  (IOAJ20)    : CONTROL   :  1 1 1 1 1 1 1 1 1 1 

AJ21  (IOAJ21)    : INPUT     :  0 0 0 0 0 0 0 0 0 0 
AJ21  (IOAJ21)    : OUTPUT3   :  1 1 1 1 1 1 1 1 1 1 
AJ21  (IOAJ21)    : CONTROL   :  1 1 1 1 1 1 1 1 1 1 
...
H14   (IOH14)     : INPUT     :  1 1 1 1 1 1 1 1 1 1 
H14   (IOH14)     : OUTPUT3   :  1 1 1 1 1 1 1 1 1 1 
H14   (IOH14)     : CONTROL   :  1 1 1 1 1 1 1 1 1 1 

H20   (IOH20)     : INPUT     :  0 0 0 0 0 0 0 0 0 0 
H20   (IOH20)     : OUTPUT3   :  0 0 0 0 0 0 0 0 0 0 
H20   (IOH20)     : CONTROL   :  0 0 0 0 0 0 0 0 0 0 

H22   (IOH22)     : INPUT     :  1 1 1 1 1 1 1 1 1 1 
H22   (IOH22)     : OUTPUT3   :  1 1 1 1 1 1 1 1 1 1 
H22   (IOH22)     : CONTROL   :  0 0 0 0 0 0 0 0 0 0 
...
K10   (MSEL0)     : INPUT     :  0 0 0 0 0 0 0 0 0 0 

J9    (MSEL1)     : INPUT     :  0 0 0 0 0 0 0 0 0 0 

J10   (MSEL2)     : INPUT     :  1 1 1 1 1 1 1 1 1 1 

H11   (MSEL3)     : INPUT     :  1 1 1 1 1 1 1 1 1 1 

AF8   (PLL_ENA)   : INPUT     :  1 1 1 1 1 1 1 1 1 1 

AE8   (PORSEL)    : INPUT     :  1 1 1 1 1 1 1 1 1 1 

AF24  (VCCSEL)    : INPUT     :  0 0 0 0 0 0 0 0 0 0 

AE7   (nIO_PULLUP): INPUT     :  1 1 1 1 1 1 1 1 1 1 
```

### Analysis

* `MSEL[3:0] == 4'b1100`

    This means "Remote system upgrade FPP with decompression feature enabled". That's extremely useful information to configure the chip.

* `H20` and `H22` are configured as output.

    These pins are used as PGM pins when the FPGA is configured in remote system upgrade mode.

* `AJ19` has a toggling pin (See the '!' at the end of the line)

    AJ19 is a clock input of this FPGA, so we've very likely found the main clock source.

### Port Renaming

As you discover new pin values, you can translate the original port name (e.g. `IOH22`) to the real name (`PGM[0]`) with
an pin renaming file.

`./example/pin_renamings.txt`:

```
AJ19:CLK100
K10:MSEL[0]
J9:MSEL[1]
J10:MSEL[2]
H11:MSEL[3]
G20:PGM[2]
H20:PGM[1]
H22:PGM[0]
```

Now rerun with the pin renamings file as a parameter:
```
./bscan_proc.py -r pin_renamings.txt EP1AGX90EF1152.bsdl bscan_values.txt > pin_report.ann.txt
```

And you get somethingn like this:

`./example/pin_report.ann.txt`:

```
...
AJ19  (CLK100)    : INPUT     :  0 0 0 1 1 0 1 1 1 0 !
AJ19  (CLK100)    : OUTPUT3   :  1 1 1 1 1 1 1 1 1 1
AJ19  (CLK100)    : CONTROL   :  1 1 1 1 1 1 1 1 1 1
...
```

## Future Improvements

* Link the script directly with OpenOCD through its TCL interface for interactive debugging
* Create OpenOCD scripts to change the value of the boundary scan register
* ...

