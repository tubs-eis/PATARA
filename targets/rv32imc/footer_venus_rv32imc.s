

# Specific to venus simulator
END_TEST:                   # here the app was successfull
li  a1, 0                   # return 0 as exit code
j _exit

END_SIMULATION:             # not successfull
li  a1, 1                   # return 1 as exit code

_exit:                      # exit code
li	a0, 17                  # exit2, return code a1
ecall