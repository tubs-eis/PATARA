
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
#	bnez	a0, END_SIMULATION	#
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
li t5, 0x40000000
lw x1, 0(t5)
lw x2, 4(t5)
lw x3, 8(t5)
lw x4, 12(t5)
lw x5, 16(t5)
lw x6, 20(t5)
lw x7, 24(t5)
lw x8, 28(t5)
lw x9, 32(t5)
lw x10, 36(t5)
lw x11, 40(t5)
lw x12, 44(t5)
lw x13, 48(t5)
lw x14, 52(t5)
lw x15, 56(t5)
lw x16, 60(t5)
lw x17, 64(t5)
lw x18, 68(t5)
lw x19, 72(t5)
lw x20, 76(t5)
lw x21, 80(t5)
lw x22, 84(t5)
lw x23, 88(t5)
lw x24, 92(t5)
lw x25, 96(t5)
lw x26, 100(t5)
lw x27, 104(t5)
lw x28, 108(t5)
lw x29, 112(t5)
lw x30, 116(t5)
lw x31, 120(t5)