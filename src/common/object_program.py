import ctypes
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .optable import OpcodeTable


class Int24(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("byte1", ctypes.c_uint8),
        ("byte2", ctypes.c_uint8),
        ("byte3", ctypes.c_uint8),
    ]

    @staticmethod
    def from_int(value):
        if not (-0x800000 <= value <= 0x7FFFFF):
            raise ValueError("Value must be in the range -8388608 to 8388607")
        return Int24(
            byte1=(value >> 16) & 0xFF,
            byte2=(value >> 8) & 0xFF,
            byte3=value & 0xFF,
        )

    def to_int(self):
        v = (self.byte1 << 16) | (self.byte2 << 8) | self.byte3
        if v >= 0x800000:
            v -= 0x1000000
        return v

    def __repr__(self):
        value = self.to_int()
        return f"Int24({value})"


class UInt24(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("byte1", ctypes.c_uint8),
        ("byte2", ctypes.c_uint8),
        ("byte3", ctypes.c_uint8),
    ]

    @staticmethod
    def from_int(value: int):
        if not (0 <= value <= 0xFFFFFF):
            raise ValueError("Value must be in the range 0 to 16777215 (0xFFFFFF)")
        return UInt24(
            byte1=(value >> 16) & 0xFF,
            byte2=(value >> 8) & 0xFF,
            byte3=value & 0xFF,
        )

    def to_int(self) -> int:
        return (self.byte1 << 16) | (self.byte2 << 8) | self.byte3

    def __repr__(self):
        value = self.to_int()
        return f"UInt24(0x{value:06X}={value})"


type Records = HeaderRecord | TextRecord | EndRecord | ModificationRecord


class HeaderRecord(ctypes.LittleEndianStructure):
    ID = b"\x00"
    _pack_ = 1
    _fields_ = [
        ("record_type", ctypes.c_char),
        ("program_name", ctypes.c_char * 6),
        ("starting_address", UInt24),
        ("program_length", UInt24),
    ]

    record_type: bytes
    program_name: bytes
    starting_address: UInt24
    program_length: UInt24

    @staticmethod
    def create(program_name: bytes, starting_address: int, program_length: int):
        return HeaderRecord(
            record_type=HeaderRecord.ID,
            program_name=program_name.ljust(6, b"\x00"),
            starting_address=UInt24.from_int(starting_address),
            program_length=UInt24.from_int(program_length),
        )

    def __repr__(self):
        return f"H, {self.program_name.decode().strip()}, {self.starting_address.to_int():06X}, {self.program_length.to_int():06X}"


class TextRecord(ctypes.LittleEndianStructure):
    ID = b"\x01"
    MAX_TEXT_RECORD_SIZE = 30
    _pack_ = 1
    _fields_ = [
        ("record_type", ctypes.c_char),
        ("starting_address", UInt24),
        ("length", ctypes.c_uint8),
        # data (maximum 30 bytes, SICFormatObjectCode)
    ]

    record_type: bytes
    starting_address: UInt24
    length: int

    @staticmethod
    def create(starting_address: int, length: int):
        return TextRecord(
            record_type=TextRecord.ID,
            starting_address=UInt24.from_int(starting_address),
            length=length,
        )

    def __repr__(self):
        return f"T,{self.starting_address.to_int():06X}, {self.length:02X}"


class EndRecord(ctypes.LittleEndianStructure):
    ID = b"\x02"
    _pack_ = 1
    _fields_ = [
        ("record_type", ctypes.c_char),
        ("exec_address", UInt24),
    ]

    record_type: str
    exec_address: UInt24

    @staticmethod
    def create(exec_address: int):
        return EndRecord(
            record_type=EndRecord.ID,
            exec_address=UInt24.from_int(exec_address),
        )

    def __repr__(self):
        return f"E,{self.exec_address.to_int():06X}"


class ModificationRecord(ctypes.LittleEndianStructure):
    ID = b"\x03"
    _pack_ = 1
    _fields_ = [
        ("record_type", ctypes.c_char),
        ("address", UInt24),
        ("length", ctypes.c_uint8),  # length of the modification in bytes
        # data (maximum 60 bytes, SICFormatObjectCode)
    ]

    record_type: str
    address: UInt24
    length: int

    @staticmethod
    def create(address: int, length: int):
        return ModificationRecord(
            record_type=ModificationRecord.ID,
            address=UInt24.from_int(address),
            length=length,
        )

    def __repr__(self):
        return f"M,{self.address.to_int():06X}, {self.length:02X}"


class SICFormatObjectCode(ctypes.LittleEndianStructure):
    _pack_ = 1
    _fields_ = [
        ("opcode", ctypes.c_uint8),
        ("_ia", ctypes.c_uint16),
    ]

    opcode: int
    _ia: int

    @property
    def indexed(self):
        return (self._ia & 0x8000) != 0

    @property
    def address(self):
        return self._ia & 0x7FFF

    def __str__(self):
        return hex(int.from_bytes(self, "big"))

    def __repr__(self):
        from .optable import code_lut

        return f"{code_lut[self.opcode].name}, {self.indexed}, {self.address:04X}"

    @staticmethod
    def create(op: "OpcodeTable", address: int, indexed: bool = False):
        ia = address | (0x8000 if indexed else 0)
        return SICFormatObjectCode(
            opcode=op.value.opcode,
            _ia=ia,
        )
