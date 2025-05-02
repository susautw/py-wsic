"""
A script to load a program into memory (a numpy memmap)
"""

from pathlib import Path
import numpy as np

from common.object_program import (
    EndRecord,
    HeaderRecord,
    ModificationRecord,
    TextRecord,
)
from common.program_iter import program_iter


def load_program(memory: np.memmap, program: Path, start_location: int) -> int:
    """
    Load a program into memory.

    :param memory: The memory to load the program into.
    :param program: The path to the program file.
    :param start_location: The starting location in memory to load the program.

    :return: The execution address of the program.
    """
    exec_address = 0
    with open(program, "rb") as f:
        # Read the program into memory
        data = f.read()

        header_record = None
        end_record = None

        for record, buffer in program_iter(memoryview(data)):
            match record:
                case HeaderRecord():
                    program_name = record.program_name.decode().strip()
                    starting_address = record.starting_address.to_int()
                    program_length = record.program_length.to_int()
                    print(
                        f"Program: {program_name}, Start: 0x{starting_address:04X}, Length: 0x{program_length:04X}"
                    )
                    print(
                        f"Loading program {program_name} at address 0x{start_location:04X}"
                    )
                    if starting_address + program_length > memory.shape[0]:
                        raise ValueError(
                            f"End of program address {starting_address + program_length} exceeds memory size {memory.shape[0]}"
                        )
                    header_record = record
                case TextRecord():
                    if header_record is None:
                        raise ValueError("Header record not found before text record")
                    starting_address = record.starting_address.to_int()
                    length = record.length

                    # load the code into memory
                    memory[
                        start_location + starting_address : start_location
                        + starting_address
                        + length
                    ] = list(buffer[:length])
                case EndRecord():
                    if header_record is None:
                        raise ValueError("Header record not found before text record")
                    exec_address = record.exec_address.to_int() + start_location
                    end_record = record
                case ModificationRecord():
                    if header_record is None:
                        raise ValueError("Header record not found before text record")
                    # Handle modification records if needed

                    address = record.address.to_int()
                    length = record.length

                    # Perform the modification in memory
                    location_slice = slice(
                        start_location + address,
                        start_location + address + length,
                    )
                    cur_addr = int.from_bytes(bytes(memory[location_slice]), "little")
                    memory[location_slice] = list(
                        bytes((cur_addr + start_location).to_bytes(length, "little"))
                    )

        if end_record is None:
            raise ValueError("End record not found")

    return exec_address
