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
    - [Sample Test](#sample-test)
    - [Pitfalls](#pitfalls)


[Contributors](#Contributors)
[License](#License)
[Citation](#Citation)

### New-Features
### RISC-V-Support
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
pip3 install -r requirements.txt
```


### Running-PATARA
The default architecture target is RISC-V.
The assembly files will be aggregated in a newly created folder `reversiAssembly`


To access the help message, run 

```bash
python3 main.py -h 
```

Creating tests for all configurations of all instructions:
```bash
python3 main.py -c
```
Creating interleaving testcases with variable repetitions can be generated with
```bash
python3 main.py -i -l REPETITIONS
```

The test for explicit pipeline tests can be set with the following command. The command should be repeated with varying forwarding distances, to test all forwardig mechanisms. For our 6 stage pipeline FORWARDING_DISTANCE should vary from 0 to 4, to test all forwarding mechanisms.
```bash
python3 main.py -s -f FORWARDING_DISTANCE 
```


In a test-instruction the random value is set to a specific operand. This however can be changed, to test that data forwarding works for all ports. The probability to switch the operands can be set with
```bash
python3 main.py --switch PROBABILITY
```

Cache test can be configured with the following parameter: 
The probabilities to modify the icache and dcache probability can be set. 
Additionally, with the newMemoryBlock-parameter the data addresses can be random (0), consequitive (1.0) or a mixture of both. 
```bash
python3 main.py --icacheMiss PROBABILITY --dcacheMiss PROBABILITY --newMemoryBlock PROBABILITY
```

A single instruction test can be started with
```bash
python3 main.py -b add
```






## Targets

### RISC-V
The RV32I and RV32M instruction sets are currently supported.
To verify the effectiveness of PATARA the coverage metrics were measured on an in-order, 6 pipeline-stage processor. 
100% coverage was reached for Statement, Branch, Expression, Condition ,and FSM states and Transitions. 


More information can be found here:
> S. Gesper, F. Stuckmann, L. Wöbbekind and G. Payá-Vayá. "PATARA: Extension of a Verification Framework for RISC-V Instruction Set Implementations". 2023 23rd International Conference on Embedded Computer Systems: Architectures, Modeling and Simulation (SAMOS), 2023, accepted for publication.

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



 #### Sample Test

 A Test consists of the following componentens
 
 Header:
 1. initialization of the processor
 2. randomization of the register file
 
 test:

 3. Actual test-instruction
 4. Comparison of initial and target data 

 Footer: 

 5. a. Success branch target. Address 0 set to zero to indicate a successful test
 5. b. Failure branch target. Address 0 set to 1 to indicate a failed test
 6. Exit Assembly test

After the execution of a test, the Address 0 has to be evaluated to determine if the test was successful. 
An simple example can be generated with 
```bash
python3 main.py -b add
```

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