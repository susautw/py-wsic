HELLO  START  0000
LOOP   LDX    LOC     # 0x0000 Set index with LOC

       LDA    ZERO    # 0x0003 Clear REG_A and load char
       LDCH   STR,X   # 0x0006
       COMP   ZERO    # 0x0009 goto EXIT if loaded char is EOC
       JEQ    EXIT    # 0x000C

       WD             # 0x000F write the char

       LDA    LOC     # 0x0012 increase LOC by ONE
       ADD    ONE     # 0x0015
       STA    LOC     # 0x0018
       J      LOOP    # 0x001B goto LOOP
EXIT   RSUB           # 0x001E

STR    BYTE   c'Hello World'  # 0x0021
       BYTE   0x0A            # 0x002C
EOC    BYTE   0x00            # 0x002D
LOC    WORD   0               # 0x002E
ONE    WORD   1               # 0x0031
ZERO   WORD   0               # 0x0034
END                           # 0x0037