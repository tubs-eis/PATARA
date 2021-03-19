# PATARA: Post-Silicon Validation Tool based on REVERSI

PATARA is an open-source tool for post-silicon validation of **any** fabricated processor. 
It is based on the REVERSI methodolgy in which the processor varifies itself.

## Table of Contents

[Getting started](#Getting-started)

- [Installation](#Installation)
- [Configuring PATARA](#Configuring-PATARA)
- [Running PATARA](#Running-PATARA)


[Contributors](#Contributors)
[License](#License)

## Getting started

### Installation
Clone the repository
```bash
git clone https://github.com/c3e-tubs/PATARA
```

Install python modules:
```bash
pip3 install xmltodict docutils
```

### Configuring-PATARA
The following configuration steps are available to configure PATARA to a custom processor.
The configuration files are stored in `sources`.

1. Instructions can be added in `instructions.xml`.

2. The processor specifications can be modified in `processor.xml`.

3. In `header.txt` and `footer.txt` the startup and shutdown instruction can be modified. 




### Running-PATARA
To access the help message, run 

```bash
python3 main.py
```

A single instruction test can be started with
```bash
python3 main.py -v -1
```

Creating all configurations of all instructions can be generated with
```bash
python3 main.py -v -2
```

Interleaving testcases can be generated with
```bash
python3 main.py -v 1
```





## Contributors

- Guillermo Payá Vayá (Technische Universität Braunschweig)
- Fabian Stuckmann (Technische Universität Braunschweig)
- Pasha Fistanto (Leibniz Universität Hannover)

## License

This open-source project is distributed under the MIT license.
