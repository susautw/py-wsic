STARS  START  0000
# TEXT SEC

# Loop A exit if width == 0
LOOPA  LDX    ZERO
       LDCH   STAR

# Loop B exit if X == WIDTH
LOOPB  WD             # Write char * WIDTH times
       TIX    WIDTH   # X <- X + 1 and compare X with WIDTH
       JLT    LOOPB   # Goto LOOPB if X < WIDTH


       LDCH   LN      # Write a line break char
       WD

       LDA    WIDTH   # WIDTH <- WIDTH - 1
       SUB    ONE

       COMP   ZERO    # Goto EXIT if WIDTH == ZERO
       JEQ    EXIT    

       STA    WIDTH   # STORE WIDTH value
       J      LOOPA   # Goto LOOPA

EXIT   RSUB

# DATA SEC
STAR   BYTE   c'*'
LN     BYTE   0x0A
WIDTH  WORD   5
ZERO   WORD   0
ONE    WORD   1
       END 