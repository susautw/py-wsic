import enum


class Formats(enum.IntEnum):
    """
    Enum for different instruction formats.
    The values are number of bytes in the instruction.
    """

    SIC = 3
    """
    SIC format - 3 bytes
    8 bits for opcode, 1 for indexed addressing, 15 for address
    """
