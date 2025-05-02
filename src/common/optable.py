"""
This module contains the opcode table for the WSIC architecture.

An opcode item consists of the following fields:
- mnemonic: The mnemonic of the opcode.
- opcode: The opcode value.
- format: The possible formats of the opcode.
"""

from collections.abc import Callable
import enum
import sys
from typing import NamedTuple

import numpy as np

from .object_program import Int24, UInt24


from .reg import Registers

from .formats import Formats


type Effect = Callable[[EffectOption], None]


class EffectOption(NamedTuple):
    registers: dict[Registers, UInt24]
    memory: np.memmap
    decoded_address: int
    """
    address + index offset
    """


class OpcodeItem(NamedTuple):
    menemonic: str
    opcode: int
    format: list[Formats]
    effect: Effect
    has_operand: bool = True


code_start = 0x00


def new_code() -> int:
    """
    Returns the next available code for the opcode.
    The code is incremented by 1 each time this function is called.
    """
    global code_start
    code = code_start
    code_start += 1
    return code


def get_word(memory: np.memmap, address: int) -> UInt24:
    """
    Returns the word at the given address.
    The word is a 3-byte value.
    """
    return UInt24.from_buffer_copy(memory[address : address + 3])


def make_load_effect(target_register: Registers, lowest_only: bool = False) -> Effect:
    def load_effect(option: EffectOption):
        if lowest_only:
            option.registers[target_register] = UInt24.from_buffer_copy(
                b"\x00\x00"
                + bytes(
                    option.memory[option.decoded_address : option.decoded_address + 1]
                )
            )
        else:
            # Load the full 3 bytes
            option.registers[target_register] = UInt24.from_buffer_copy(
                option.memory[option.decoded_address : option.decoded_address + 3]
            )

    return load_effect


def make_store_effect(target_register: Registers, lowest_only: bool = False) -> Effect:
    def store_effect(option: EffectOption):
        if lowest_only:
            option.memory[option.decoded_address : option.decoded_address + 1] = list(
                bytes(option.registers[target_register])
            )
        else:
            # Store the full 3 bytes
            option.memory[option.decoded_address : option.decoded_address + 3] = list(
                bytes(option.registers[target_register])
            )

    return store_effect


def compare_effect(option: EffectOption, reg=Registers.A):
    # Compare the value in the register with the value in memory
    r = option.registers[reg]
    v = get_word(option.memory, option.decoded_address)
    if r.to_int() == v.to_int():
        option.registers[Registers.SW] = UInt24.from_int(0)
    elif r.to_int() < v.to_int():
        option.registers[Registers.SW] = UInt24.from_int(1)
    else:
        option.registers[Registers.SW] = UInt24.from_int(2)


def tix_effect(option: EffectOption):
    # Increment the value in the X register and compare it with the value in memory
    option.registers[Registers.X] = UInt24.from_int(
        option.registers[Registers.X].to_int() + 1
    )
    compare_effect(option, Registers.X)


def make_arithmetic_effect(fn: Callable[[int, int], int]) -> Effect:
    def arithmetic_effect(option: EffectOption):
        # Perform the arithmetic operation
        a = option.registers[Registers.A].to_int()
        v = Int24.from_buffer(get_word(option.memory, option.decoded_address)).to_int()
        result = fn(a, v)
        option.registers[Registers.A] = UInt24.from_buffer(Int24.from_int(result))

    return arithmetic_effect


def make_jump_effect(cond: Callable[[EffectOption], bool]) -> Effect:
    def jump_effect(option: EffectOption):
        if not cond(option):
            # If the condition is not met, do not perform the jump
            return None
        # Perform the jump operation
        option.registers[Registers.PC] = UInt24.from_int(option.decoded_address)

    return jump_effect


def jsub_effect(option: EffectOption) -> None:
    # Save the current PC in the L register
    option.registers[Registers.L] = option.registers[Registers.PC]
    # Jump to the address
    option.registers[Registers.PC] = UInt24.from_int(option.decoded_address)


def rsub_effect(option: EffectOption) -> None:
    # Jump to the address in the L register
    option.registers[Registers.PC] = option.registers[Registers.L]


def rd_effect(option: EffectOption) -> None:
    v = sys.stdin.read(1)
    if not v:
        raise ValueError("No input")
    option.registers[Registers.A] = UInt24.from_buffer_copy(b"\x00\x00" + v.encode())


def wd_effect(option: EffectOption) -> None:
    v = bytes(option.registers[Registers.A])
    print(v.decode(), end="")


def halt_effect(option: EffectOption) -> None:
    raise KeyboardInterrupt("Halted")


class OpcodeTable(enum.Enum):
    LDA = OpcodeItem("LDA", new_code(), [Formats.SIC], make_load_effect(Registers.A))
    LDCH = OpcodeItem(
        "LDCH", new_code(), [Formats.SIC], make_load_effect(Registers.A, True)
    )
    LDX = OpcodeItem("LDX", new_code(), [Formats.SIC], make_load_effect(Registers.X))
    LDL = OpcodeItem("LDL", new_code(), [Formats.SIC], make_load_effect(Registers.L))
    LDS = OpcodeItem("LDS", new_code(), [Formats.SIC], make_load_effect(Registers.S))

    STA = OpcodeItem("STA", new_code(), [Formats.SIC], make_store_effect(Registers.A))
    STCH = OpcodeItem(
        "STCH", new_code(), [Formats.SIC], make_store_effect(Registers.A, True)
    )
    STX = OpcodeItem("STX", new_code(), [Formats.SIC], make_store_effect(Registers.X))
    STL = OpcodeItem("STL", new_code(), [Formats.SIC], make_store_effect(Registers.L))
    STS = OpcodeItem("STS", new_code(), [Formats.SIC], make_store_effect(Registers.S))

    COMP = OpcodeItem("COMP", new_code(), [Formats.SIC], compare_effect)
    TIX = OpcodeItem("TIX", new_code(), [Formats.SIC], tix_effect)
    ADD = OpcodeItem(
        "ADD", new_code(), [Formats.SIC], make_arithmetic_effect(lambda a, b: a + b)
    )
    SUB = OpcodeItem(
        "SUB", new_code(), [Formats.SIC], make_arithmetic_effect(lambda a, b: a - b)
    )
    J = OpcodeItem("J", new_code(), [Formats.SIC], make_jump_effect(lambda _: True))
    JEQ = OpcodeItem(
        "JEQ",
        new_code(),
        [Formats.SIC],
        make_jump_effect(lambda option: option.registers[Registers.SW].to_int() == 0),
    )
    JLT = OpcodeItem(
        "JLT",
        new_code(),
        [Formats.SIC],
        make_jump_effect(lambda option: option.registers[Registers.SW].to_int() == 1),
    )
    JGT = OpcodeItem(
        "JGT",
        new_code(),
        [Formats.SIC],
        make_jump_effect(lambda option: option.registers[Registers.SW].to_int() == 2),
    )
    JSUB = OpcodeItem("JSUB", new_code(), [Formats.SIC], jsub_effect)
    RSUB = OpcodeItem("RSUB", new_code(), [Formats.SIC], rsub_effect, False)

    RD = OpcodeItem("RD", new_code(), [Formats.SIC], rd_effect, False)
    WD = OpcodeItem("WD", new_code(), [Formats.SIC], wd_effect, False)
    HLT = OpcodeItem("HLT", new_code(), [Formats.SIC], halt_effect, False)
    NOP = OpcodeItem("NOP", new_code(), [Formats.SIC], lambda _: None, False)


code_lut = {item.value.opcode: item for item in OpcodeTable}
