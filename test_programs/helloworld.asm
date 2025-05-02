HELLO  START  0000
LOOP   LDX    LOC     # Set index with LOC

       LDA    ZERO    # Clear REG_A and load char
       LDCH   STR,X
       COMP   ZERO    # goto EXIT if loaded char is EOC
       JEQ    EXIT    

       WD             # write the char

       LDA    LOC     # increase LOC by ONE
       ADD    ONE
       STA    LOC
       J      LOOP    # goto LOOP
EXIT   RSUB

STR    BYTE   c'Hello World'
       BYTE   0x0A
EOC    BYTE   0x00
LOC    WORD   0
ONE    WORD   1
ZERO   WORD   0
END    