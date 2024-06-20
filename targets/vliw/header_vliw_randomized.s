

// reset Finish (0x000) and Success Flags (0x001)
MVI_8 V0R4, #0x00
STORE 0x001, V0R4
STORE 0x000, V0R4



