# Spec
## Comment

```
# comment
```

## Instruction
```
[LABEL] MNEMONIC [OPERAND]
[LABEL] DIRECTIVE [OPTION]
```

## Directive
### START
```
<NAME>  START <START_ADDR>
```

### END
```
        END   [<EXEC_ADDR>]
```

### BYTE
```bnf
[LABEL] BYTE <BYTE_VALUE>

<BYTE_VALUE> ::= C'<string>' | 0x<2-hexadecimal>
<string> ::= ([a-zA-Z0-9_])+
<2-hexadecimal> ::= [0-9a-fA-F]{2}
```

the length of BYTE_VALUE should be less or equal than 30 bytes and at least 1 byte 

### WORD
```bnf
[LABEL] WORD <WORD_VALUE>
<WORD_VALUE> ::= 0x<6-hexadecimal> | <signed-int> | <unsigned-int> 
<signed-int> ::= [+-]?[0-9]+
<unsigned-int> ::= [0-9]+U
<6-hexadecimal> ::= [0-9a-fA-F]{6}
```

### RESB
```bnf
[LABEL] RESB <NUM>
<NUM> ::= <unsigned-int>
```
### RESW
```bnf
[LABEL] RESW <NUM>