import ctypes
from common.object_program import (
    HeaderRecord,
    TextRecord,
    EndRecord,
    ModificationRecord,
    Records,
)


def program_iter(buffer: memoryview):
    """
    Iterate over the program's instructions.

    Args:
        program: The program to iterate over.

    Yields:
        The next instruction in the program.
    """
    while True:
        try:
            # Parse the record
            record, buffer = parse_record(buffer)

            # Yield the record and the remaining buffer
            yield record, buffer

            # If the record is a text record, skip the data
            if isinstance(record, TextRecord):
                buffer = buffer[record.length :]
        except ValueError:
            break


def parse_record(buffer: memoryview) -> tuple[Records, memoryview]:
    first_byte = buffer[0:1]
    for record in [HeaderRecord, TextRecord, EndRecord, ModificationRecord]:
        if record.ID == first_byte:
            record_size = ctypes.sizeof(record)
            record_data = buffer[0:record_size]
            record_obj = record.from_buffer_copy(record_data)
            return record_obj, buffer[record_size:]
    raise ValueError(f"Unknown record type: {first_byte}")
