
.section .text.trap, "ax"
.option norvc
.global vector_table
_trap_start:
	j _trap_exception
	j END_SIMULATION
	j END_SIMULATION
	j END_SIMULATION
	j END_SIMULATION
	j END_SIMULATION
	j END_SIMULATION
	j END_SIMULATION
	j END_SIMULATION
	j END_SIMULATION
	j END_SIMULATION
	j END_SIMULATION
	j END_SIMULATION

_trap_exception:
	csrr	t3, mcause
	li 		t4, 11		# 0xb = CAUSE_MACHINE_ECALL
	fence
	beq 	t3, t4, CONTINUE_SIM	
	j		END_SIMULATION
	
CONTINUE_SIM:
	csrr t0, mepc
	addi t0, t0, 0x4
	csrw mepc, t0
	mret
	
	
	
	
	
.section .traphandler, "ax"
trap_vector:
	csrr	t3, mcause
	li 		t4, 11
	fence
	beq 	t3, t4, CONTINUE_SIM
	li	t5,-52
	li  t6, 0xaffedead
	nop
	nop
	nop
	nop
	nop
	nop
	sw	t6,0(t5)
	fence
	ecall
	
	
	
	
	
	
.section .text.init, "ax"
.global _start

# 0x80: entry point to app (label: _start)
_start:
	j		crt0

# will be 0x84
EXCEPTION_11:
	li	t5,-52
	li  t6, 0xcafedead
	nop
	nop
	nop
	nop
	nop
	nop
	sw	t6,0(t5)
	fence
	ecall
	
crt0:
	csrr	a0, mhartid			# read hardwareid, expect 0
	bnez	a0, END_SIMULATION	# 
	li		a0, -1
	CSRRC	x1, mtvec, a0		# read to x1, clear with mask: -1
	la 		t0, trap_vector
	csrw	mtvec,t0
	
_start2:
	ecall

# # Specific to venus simulator
# .text
# .globl _start               # defines where programm execution starts
# _start:
