STARS  START  0000
## TEXT SEC
# Loop A
LOOPA  LDA    WIDTH   # A <- WIDTH
       COMP   NSTAR   # Goto WSTAR if WIDTH == NSTAR
       JEQ    WSTAR

       SUB    NSTAR   # NSTAR <- A - NSTAR
       STA    NSPACE


# Write spaces
       LDX    ZERO    # X <- ZERO
       LDCH   SPACE
LOOPB  WD             # Write char * NSPACE times
       TIX    NSPACE  # X <- X + 1 and compare X with NSPACE
       JLT    LOOPB   # Goto LOOPB if X < NSPACE

# Write stars
WSTAR  LDX    ZERO    # X <- ZERO
       LDCH   STAR
LOOPC  WD             # Write char * NSTAR times
       TIX    NSTAR  # X <- X + 1 and compare X with NSTAR
       JLT    LOOPC   # Goto LOOPC if X < NSTAR

       LDCH   LN      # Write a line break char
       WD

       LDA    NSTAR   # A <- NSTAR + 1
       ADD    ONE

       COMP   WIDTH   # Goto EXIT if NSTAR > WIDTH
       JGT    EXIT    

       STA    NSTAR   # NSTAR <- A
       J      LOOPA   # Goto LOOPA

EXIT   RSUB

## DATA SEC
NSPACE RESW   1

NSTAR  WORD   1
STAR   BYTE   c'*'
SPACE  BYTE   c' '
LN     BYTE   0x0A
WIDTH  WORD   5
ZERO   WORD   0
ONE    WORD   1
       END 