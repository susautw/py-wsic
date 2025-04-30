"""
A script to load a program into memory (a numpy memmap)
"""

import ctypes
from pathlib import Path
import numpy as np

from common.object_program import (
    EndRecord,
    HeaderRecord,
    ModificationRecord,
    Records,
    TextRecord,
    UInt24,
)


def load_program(
    memory: np.memmap, program: Path, start_location: int
) -> tuple[int, int]:
    """
    Load a program into memory.

    :param memory: The memory to load the program into.
    :param program: The path to the program file.
    :param start_location: The starting location in memory to load the program.

    :return: The execution address and the terminal address of the program.
    """
    exec_address = 0
    terminal_address = 0
    with open(program, "rb") as f:
        # Read the program into memory
        data = f.read()

        header_record = None
        end_record = None

        while data:
            # Parse the record
            record, data = parse_record(data)
            match record:
                case HeaderRecord():
                    # Load the header record
                    program_name = record.program_name.decode().strip()
                    starting_address = record.starting_address.to_int()
                    program_length = record.program_length.to_int()
                    print(
                        f"Program: {program_name}, Start: {starting_address:06X}, Length: {program_length:06X}"
                    )
                    if starting_address + program_length > memory.shape[0]:
                        raise ValueError(
                            f"End of program address {starting_address + program_length} exceeds memory size {memory.shape[0]}"
                        )
                    header_record = record
                    terminal_address = start_location + starting_address + program_length
                case TextRecord():
                    if header_record is None:
                        raise ValueError("Header record not found before text record")
                    # Load the text record
                    starting_address = record.starting_address.to_int()
                    length = record.length

                    # load the code into memory
                    memory[
                        start_location + starting_address : start_location
                        + starting_address
                        + length
                    ] = list(data[:length])

                    # consume the data
                    data = data[length:]
                case EndRecord():
                    if header_record is None:
                        raise ValueError("Header record not found before text record")
                    # Load the end record
                    exec_address = record.exec_address.to_int()
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
                    cur_addr = UInt24.from_buffer_copy(
                        bytes(memory[location_slice])
                    ).to_int()
                    cur_addr += start_location
                    memory[location_slice] = list(UInt24(cur_addr).to_bytes())
            if end_record:
                break

        if end_record is None:
            raise ValueError("End record not found")

    return exec_address, terminal_address


def parse_record(buffer: bytes) -> tuple[Records, bytes]:
    first_byte = buffer[0:1]
    for record in [HeaderRecord, TextRecord, EndRecord, ModificationRecord]:
        if record.ID == first_byte:
            record_size = ctypes.sizeof(record)
            record_data = buffer[0:record_size]
            record_obj = record.from_buffer_copy(record_data)
            return record_obj, buffer[record_size:]
    raise ValueError(f"Unknown record type: {first_byte}")
