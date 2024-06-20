

END_TEST:                   # SUCCESS | successfull
	li	t5, 0x80000000
	li  t2, 0
	sw	t2, 0(t5)			# signature dump: 0
	j _exit

END_SIMULATION:             # FAIL | not successfull
	li	t5, 0x80000000
	li  t2, 1
	sw	t2, 0(t5)			# signature dump: 1 (fail)

_exit:
	li	t5, 0x80000004
	li      t2, 0
	sw	t2, 0(t5)			# exit code : gp | stops simulation
	fence
	li	gp, 1
	ecall



# # Specific to venus simulator
# END_TEST:                   # here the app was successfull
# li  a1, 0                   # return 0 as exit code
# j _exit

# END_SIMULATION:             # not successfull
# li  a1, 1                   # return 1 as exit code

# _exit:                      # exit code
# li	a0, 17                  # exit2, return code a1
# ecall
