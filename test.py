"""
A simple test object program to print '*\n' to the console.

TEST01 START 1000
FIRST  LDCH  C1
       WD
       LDCH  C2
       WD
       RSUB
C1     BYTE  c'*'
C2     BYTE  c'\n'
       END   FIRST
"""

import ctypes
from common.object_program import (
    EndRecord,
    HeaderRecord,
    ModificationRecord,
    SICFormatObjectCode,
    TextRecord,
)
from common.optable import OpcodeTable


program = [
    HeaderRecord.create(b"TEST01", 0x001000, 0x000011),
    TextRecord.create(0x001000, 0x11),
    SICFormatObjectCode.create(OpcodeTable.LDCH, 0x00100F),  # 0x001000
    SICFormatObjectCode.create(OpcodeTable.WD, 0x000000),  # 0x001003
    SICFormatObjectCode.create(OpcodeTable.LDCH, 0x001010),  # 0x001006
    SICFormatObjectCode.create(OpcodeTable.WD, 0x000000),  # 0x001009
    SICFormatObjectCode.create(OpcodeTable.RSUB, 0x000000),  # 0x00100C
    ctypes.c_char(b"*"),  # 0x00100F
    ctypes.c_char(b"\n"),  # 0x001010
    ModificationRecord.create(0x001001, 0x02),
    ModificationRecord.create(0x001007, 0x02),
    EndRecord.create(0x001000),  # 0x001011
]


def main():
    with open("test.obj", "wb") as f:
        for record in program:
            f.write(record)


if __name__ == "__main__":
    main()
