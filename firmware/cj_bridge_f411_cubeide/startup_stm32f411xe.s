.syntax unified
.cpu cortex-m4
.fpu softvfp
.thumb

.global g_pfnVectors
.global Reset_Handler
.global Default_Handler

.word _sidata
.word _sdata
.word _edata
.word _sbss
.word _ebss

.section .isr_vector,"a",%progbits
.type g_pfnVectors, %object
.size g_pfnVectors, .-g_pfnVectors

g_pfnVectors:
  .word _estack
  .word Reset_Handler
  .word Default_Handler
  .word Default_Handler
  .word Default_Handler
  .word Default_Handler
  .word Default_Handler
  .word 0
  .word 0
  .word 0
  .word 0
  .word Default_Handler
  .word Default_Handler
  .word 0
  .word Default_Handler
  .word Default_Handler
  .rept 82
  .word Default_Handler
  .endr

.section .text.Reset_Handler
.thumb_func
.type Reset_Handler, %function
Reset_Handler:
  ldr r0, =_sidata
  ldr r1, =_sdata
  ldr r2, =_edata
1:
  cmp r1, r2
  bcc 2f
  b 3f
2:
  ldr r3, [r0], #4
  str r3, [r1], #4
  b 1b
3:
  ldr r0, =_sbss
  ldr r1, =_ebss
  movs r2, #0
4:
  cmp r0, r1
  bcc 5f
  b 6f
5:
  str r2, [r0], #4
  b 4b
6:
  bl main
7:
  b 7b
.size Reset_Handler, .-Reset_Handler

.section .text.Default_Handler,"ax",%progbits
.thumb_func
.type Default_Handler, %function
Default_Handler:
  b .
.size Default_Handler, .-Default_Handler
