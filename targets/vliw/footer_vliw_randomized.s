



// FFF indicates successfull execution of test case
MVI_8 V0R4, #0xFF
STORE 0x001, V0R4
// if an error occurs, program will directly jump to L_END_SIMULATION_LABEL, so addres 1 will be 0x00 (error)
:L_END_SIMULATION_LABEL
MVI_8 V0R4, #0xFF
STORE 0x000, V0R4

