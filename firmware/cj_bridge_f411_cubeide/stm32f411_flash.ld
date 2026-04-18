ENTRY(Reset_Handler)

MEMORY
{
  FLASH (rx)  : ORIGIN = 0x08000000, LENGTH = 512K
  RAM   (xrw) : ORIGIN = 0x20000000, LENGTH = 128K
}

_estack = ORIGIN(RAM) + LENGTH(RAM);

SECTIONS
{
  .isr_vector :
  {
    KEEP(*(.isr_vector))
  } > FLASH

  .text :
  {
    *(.text*)
    *(.rodata*)
    *(.init)
    *(.fini)
    *(.glue_7)
    *(.glue_7t)
    *(.eh_frame)
    . = ALIGN(4);
    __preinit_array_start = .;
    KEEP(*(.preinit_array*))
    __preinit_array_end = .;
    . = ALIGN(4);
    __init_array_start = .;
    KEEP(*(SORT(.init_array.*)))
    KEEP(*(.init_array*))
    __init_array_end = .;
    . = ALIGN(4);
    __fini_array_start = .;
    KEEP(*(SORT(.fini_array.*)))
    KEEP(*(.fini_array*))
    __fini_array_end = .;
    . = ALIGN(4);
    *(.ARM.exidx*)
    *(.ARM.extab*)
    _etext = .;
  } > FLASH

  _sidata = _etext;

  .data : AT(_sidata)
  {
    _sdata = .;
    *(.data*)
    _edata = .;
  } > RAM

  .bss :
  {
    _sbss = .;
    *(.bss*)
    *(COMMON)
    _ebss = .;
  } > RAM

  . = ALIGN(8);
  _end = .;
}
