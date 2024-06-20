# PATARA: Post-Silicon Validation Tool based on REVERSI


PATARA is an open-source tool for post-silicon validation of **any** fabricated processor. 
It is based on the REVERSI methodology in which the processor validates itself. 
The validation process is performed on random data and random instructions.
Therefore this tool can functionally verify functional units, and interactions between functional units and modules.

PATARA can be used for a host of different hardware targets.
These can be configured using XML files to describe the characteristcs of a custom processor and ISAs. 
Examples for targets can be found under `targets`.


**RISC-V Support**

PATARA implements the instruction sets for RV32I and RV32M. 
The paper can be found here:
> S. Gesper, F. Stuckmann, L. Wöbbekind and G. Payá-Vayá. "PATARA: Extension of a Verification Framework for RISC-V Instruction Set Implementations". 2023 23rd International Conference on Embedded Computer Systems: Architectures, Modeling and Simulation (SAMOS), 2023, accepted for publication.


**Citation**

The PATARA tool is described in the following paper. If you are using PATARA, please cite it as follows:

> F. Stuckmann,P. A. Fistanto and G. Payá-Vayá. "PATARA: A REVERSI-Based Open-Source Tool
> for Post-Silicon Validation of Processor Cores". 2021 10th International Conference on
> Modern Circuits and Systems Technologies (MOCAST), 2021, https://doi.org/10.1109/mocast52088.2021.9493373



## Table of Contents

[New Features](#New-Features)
- [RISC-V Support](#RISC-V-Support)

[Getting started](#Getting-started)


- [Installation](#Installation)
- [Running PATARA](#Running-PATARA)

[Targets](#targets)
- [RISC-V](#risc-v)
- [VLIW](#vliw)
- [Custom Target](#custom-targets)
    - [Example Patara Test](#example-patara-test)
    - [Pitfalls](#pitfalls)


[Contributors](#Contributors)
[License](#License)
[Citation](#Citation)

### New-Features
### Release v1.1: 
- Interleaving test sequences can now be longer
- added possibility to randomize from file (memory load) or from assembly (load immediate)
- added parallelism to accelerate test generation
- reorganized arguments to better indicate which arguments are grouped together
- bug fixes

### Release v1.0: RISC-V-Support
- Added support for RV32I and RV32M instruction tests
- Added support for dedicated instruction/data cache tests
- Added support for dedicated pipeline hazard detection tests. This is especially useful for variable length  pipeline implementations.


## Getting started



### Installation
Clone the repository
```bash
git clone https://github.com/tubs-eis/PATARA.git
```

Install python modules:
```bash
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Initialization
```bash
source venv/bin/activate
```

### Running-PATARA
The default ISA target is RISC-V.
The resulting assembly files will be aggregated in a newly created folder `reversiAssembly`.


To access the help message, run 

```bash
python3 main.py -h 
```

By default the RISC-V ISA is seleted and corresponds to the following command. 
To select a different target, the folder-name found in `targets` has to be passed to the architecture parameter.
```bash
python3 main.py -a rv32imc
```


Creating tests for all configurations of all instructions:
```bash
python3 main.py --completeInstruction
```
Creating interleaving testcases with variable repetitions can be generated with
```bash
python3 main.py --interleaving --isa_repetition REPETITIONS
```

The test for explicit pipeline tests can be set with the following command. The command should be repeated with varying forwarding distances, to test all forwardig mechanisms. For our 6 stage pipeline FORWARDING_DISTANCE should vary from 0 to 4, to test all forwarding mechanisms.
```bash
python3 main.py --sequence  --forwarding FORWARDING_DISTANCE 
```


In a test-instruction the random value is set to a specific operand. This however can be changed, to test that data forwarding works for all ports. The probability to switch the operands can be set with
```bash
python3 main.py  --switch_prob PROBABILITY
```

Cache test can be configured with the following parameter: 
The probabilities to modify the icache and dcache probability can be set. 
Additionally, with the newMemoryBlock-parameter the data addresses can be random (0), consequitive (1.0) or a mixture of both. 
```bash
python3 main.py --icacheMiss PROBABILITY --dcacheMiss PROBABILITY --newMemoryBlock PROBABILITY
```

A single instruction test can be started with
```bash
python3 main.py --singleInstruction add
```






## Targets

### RISC-V
The RV32I and RV32M instruction sets are currently supported.
To verify the effectiveness of PATARA the coverage metrics were measured on an in-order, 6 pipeline-stage processor. 
100% coverage was reached for Statement, Branch, Expression, Condition ,and FSM states and Transitions. 


More information can be found here:
> S. Gesper, F. Stuckmann, L. Wöbbekind and G. Payá-Vayá. "PATARA: Extension of a Verification Framework for RISC-V Instruction Set Implementations". 2023 23rd International Conference on Embedded Computer Systems: Architectures, Modeling and Simulation (SAMOS), 2023, https://doi.org/10.1007/978-3-031-46077-7_15

### VLIW 
Due to licensing issues, the VLIW instruction set is massivly reduced and modified.
It can be used as a template of how expressive PATARA can be. 
The full breadth implemented features can be found here:
> F. Stuckmann, P. A. Fistanto and G. Payá-Vayá. "PATARA: A REVERSI-Based Open-Source Tool
> for Post-Silicon Validation of Processor Cores". 2021 10th International Conference on
> Modern Circuits and Systems Technologies (MOCAST), 2021, https://doi.org/10.1109/mocast52088.2021.9493373


### Custom Targets
The following configuration steps are available to configure PATARA to a custom processor.
The configuration files are stored in `targets`.

1. Create a custom target folder in `targets`.

2. Instructions can be added in `instructions.xml`. If instructions need custom code for specific options, these can be added in a specialization part (see ADD specialization in targets/rv32imc/instructions_rv32imc.xml). 

3. The processor specifications can be modified in `processor.xml`. These also include the features the processor enables.

4. In `header.txt` and `footer.txt` the startup and shutdown instruction can be modified. The `footer.txt` should containa a END_TEST branch target to signify that a test has executed correctly, accordingly a END_SIMULATION branch target should also be enabled to notify that an error occured. In the RISC-V target, an 1 at the address identifies an error in the execution.



#### Example Patara Test

To generate an example patara assembly file for the RISC-V ISA, the following command can be used: 
```
python3 main.py -b add -a rv32imc
```

The parts of the PATARA tests are explained by looking at the resulting assembly file of the previous command. 
The assembly file can be found under `reversiAssembly/singleInstr_add_switch_50_1685627323.S`.
Note: The integer at the end of the filename corresponds to the time in miliseconds, when the assembly was was generated and will differ.

```
########################## Header #################################
####### initialize processor
.section .text.trap, "ax"
.option norvc
.global vector_table

....
	

####### randomize register file
li x1, 0xaf7b6215
...
li x31, 0x8c88c802

########################## Tests #################################

####### Patara test of the ADD instruction
#add
add x8, x19, x4

#REVERSE:add
sub x8, x8, x19

####### Comparison of inital data (x4) and target data (x8)
#Comparison Code
bne x4, x8, END_SIMULATION
nop


########################## Footer #################################

####### Successful execution, set flag
END_TEST:                   # SUCCESS | successfull
	li	t5, -60
	li  t2, 0                   
	sw	t2, 0(t5)			# signature dump: 0
	j _exit

####### Failed execution, set flag
END_SIMULATION:             # FAIL | not successfull
	li	t5, -60
	li  t2, 1   
	sw	t2, 0(t5)			# signature dump: 1 (fail)

####### Successful execution, set flag
_exit:                      
	li	t5, -52
	sw	gp, 0(t5)			# exit code : gp | stops simulation
	fence
	li	gp, 1
	ecall
	
```


After the execution of a test, the Address 0 has to be evaluated to determine if the test was successful (0) or failed (1). 


#### Pitfalls
- **Branch targets** should always have the keyword `_BRANCH_INDEX` so that the test-instruction can be repeated in a test. It will be automatically replaced in the code generation with an integer number.
- if **temporary registers** are used in describing a test-instruction, these should be blocked in the processor configuration, because the random data in the register file has to be constant, so that the instructions can be reversed




## Contributors

- Fabian Stuckmann (Technische Universität Braunschweig)
- Sven Gesper (Technische Universität Braunschweig)
- Lucy Wöbbekind (Technische Universität Braunschweig)
- Guillermo Payá Vayá (Technische Universität Braunschweig)

## License

This open-source project is distributed under the MIT license.

## Citation
The PATARA tool is described in the following paper. If you are using PATARA, please cite it as follows:

> F. Stuckmann, P. A. Fistanto and G. Payá-Vayá. "PATARA: A REVERSI-Based Open-Source Tool
> for Post-Silicon Validation of Processor Cores". 2021 10th International Conference on
> Modern Circuits and Systems Technologies (MOCAST), 2021, https://doi.org/10.1109/mocast52088.2021.9493373


# Known Bugs
Reverse should ideally work without Focusregister in reverse instruction (please consider removing them!)
- Kavuaka requires that the Focusregister is valid for some reverse instructions to work (reverse of shift left)
- RISC-V requires that the Focusregister is valid for some reverse instructions to work (beq and bne)

## Interleaving
- For each test instructions 5 Memory addresses will be blocked from the data memory address range. If they are not used in a Testinstruction they are not freed again, therefore small memories can exhaust the avaialable data memory range.
This can be solved by giving back the memories, if they are unused in a test instruction, which is currently not implemented.
-> register pressure can be reduced by providing load and store instructions, so that the random data can be spilled to memory and thus the register do not have to be permanently blocked. See Kavuaka for sample.
```
    <interleaving_random_to_memory>
        <pre>
        <instr>STORE ADDRESS5, randValue</instr>
        </pre>
        <post>
        <instr>LOAD randValue, ADDRESS5</instr>
        </post>
    </interleaving_random_to_memory>
```

## Kavuaka
- [x] correct fixed issue slot in assembly
- [x] fix basic to also have randomize STATE in the middle
- [ ] random implementation

### Signed_unsigned
Kavauka encodes the sign in some instructions (i.e. AND and OR) wrong.
Instruction is Signed, however immediate is unsign extended.
This fix is encoded with <signed_unsigned>True</signed_unsigned> in the instructions_kavauaka.xml file.




### Switch operand (based on RISC-V)
- idea behind: test forwarding of source operand 1 

### Missing ISA
- ELOOP is not implemented
- kommentare todo f[r implementation
- kommentare for missing instructions
- 



## RISC-V
- does not have a randomize processor state between modification and reverse instruciton!

### Instruction Types
Instruction types can be defined
- R : Register instruction
- R-M: Register instruction multicyle
- U : U-Type (Upper Immediate)
- UJ:  (Unconditional Jump)
- I : (Immediate)
- S: (Store)
- SB:  (Conditional Branch)

### Enabled ISA Extensions
- ISA extensions can be enabled and disabled, depending on if the processor can execute them
- In an instruction the M extension of e.g. a multiplicaiton can be described by 
```
<isa_extension>m</isa_extension>
```
- I and M extens can be enabled with
```
--isa_extensions="im"
```
