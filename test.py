"""
A simple test object program to print '*\n' to the console.

    LDCH C1
        WD
    LDCH C2
        WD
    HLT
        C1 DB 'A'
C1  BYTE c'*'
C2  BYTE c'\n'
"""

import ctypes
from common.object_program import EndRecord, HeaderRecord, SICFormatObjectCode, TextRecord
from common.optable import OpcodeTable


program = [
    HeaderRecord.create(b"TEST01", 0x000000, 0x000011),
    TextRecord.create(0x000000, 0x000011),
    SICFormatObjectCode.create(OpcodeTable.LDCH, 0x00000F),
    SICFormatObjectCode.create(OpcodeTable.WD, 0x000000),
    SICFormatObjectCode.create(OpcodeTable.LDCH, 0x000010),
    SICFormatObjectCode.create(OpcodeTable.WD, 0x000000),
    SICFormatObjectCode.create(OpcodeTable.HLT, 0x000000),
    ctypes.c_char(b"*"),
    ctypes.c_char(b"\n"),
    EndRecord.create(0x000000),
]


def main():
    with open("test.obj", "wb") as f:
        for record in program:
            f.write(record)


if __name__ == "__main__":
    main()
