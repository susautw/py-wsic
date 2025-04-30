import enum


class AsmDirectives(enum.IntEnum):
    """
    Enum for different assembler directives.
    The values are the corresponding opcode values.
    """

    START = 0x00
    """Start directive"""

    END = 0x01
    """End directive"""

    BYTE = 0x02
    """Byte directive"""

    WORD = 0x03
    """Word directive"""

    RESB = 0x04
    """Reserve byte directive"""

    RESW = 0x05
    """Reserve word directive"""
