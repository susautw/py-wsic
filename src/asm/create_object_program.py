from asm.directives import AsmDirectives
from asm.model import Instruction, ObjectProgramRecord, SYMTAB
from common.object_program import (
    EndRecord,
    HeaderRecord,
    ModificationRecord,
    SICFormatObjectCode,
    TextRecord,
)
from collections.abc import Iterable

from common.optable import OpcodeTable


def create_object_program(
    symtab: SYMTAB, instructions: list[Instruction], program_length
) -> list[ObjectProgramRecord]:
    """
    Create the object program from the symbol table and instructions.

    :param symtab: The symbol table.
    :param instructions: The list of instructions.
    :param program_length: The length of the program.
    :return: The object program.
    """
    if len(instructions) < 3:
        raise ValueError(
            "The instruction list must contain at least 3 instructions. START, END, and one RSUB instruction."
        )

    start = instructions[0]
    end = instructions[-1]
    if start.op != AsmDirectives.START or end.op != AsmDirectives.END:
        raise ValueError(
            "The first instruction must be START and the last instruction must be END."
        )

    starting_address: int = start.parsed_ctx["starting_addr"]
    program_name: str = start.parsed_ctx["program_name"]
    executing_address: int = end.parsed_ctx["exec_addr"]

    object_program: list[ObjectProgramRecord] = []
    modification_records: list[ModificationRecord] = []

    # Create the header record
    object_program.append(
        HeaderRecord.create(
            program_name=program_name.encode("ascii"),
            starting_address=starting_address,
            program_length=program_length,
        )
    )

    # Create the text records
    for grouped_instructions, text_record_length in group_instructions_for_text_record(
        instructions[1:-1]
    ):
        text_record_starting_address = grouped_instructions[0].location

        # Create the payload for the text record
        object_program.append(
            TextRecord.create(
                starting_address=text_record_starting_address,
                length=text_record_length,
            )
        )

        for instruction in grouped_instructions:
            if instruction.op in (AsmDirectives.BYTE, AsmDirectives.WORD):
                # BYTE directive
                value = instruction.parsed_ctx["value"]
                object_program.append(value)
                continue

            assert isinstance(instruction.op, OpcodeTable), (
                f"Instruction {instruction.instruction_name} is not an opcode."
            )
            indexed = instruction.parsed_ctx.get("indexed", False)
            symbol = instruction.parsed_ctx.get("symbol", None)

            # If the instruction has no symbol, use the address 0
            address = 0

            # If the instruction has a symbol, use its address from the symbol table
            # And add a modification record for it
            if symbol is not None:
                # Check if the symbol is in the symbol table
                if symbol not in symtab:
                    raise ValueError(
                        f"Symbol {symbol} not found in the symbol table. at line {instruction.line_number}"
                    )

                address = symtab[symbol]

                # Create a modification record for the symbol
                modification_records.append(
                    ModificationRecord.create(
                        # +1 to skip the opcode, modify the address only
                        address=instruction.location + 1,
                        length=2,  # 2 bytes for the address
                    )
                )

            object_program.append(
                SICFormatObjectCode.create(
                    op=instruction.op, address=address, indexed=indexed
                )
            )

    # Create the modification records
    object_program.extend(modification_records)

    # Create the end record
    object_program.append(EndRecord.create(exec_address=executing_address))

    return object_program


def group_instructions_for_text_record(
    instructions: Iterable[Instruction],
) -> Iterable[tuple[list[Instruction], int]]:
    """
    Groups instructions with object code into chunks for text records.

    Skips instructions without object code (like RESB, RESW)
    and starts a new chunk after encountering them.
    Each chunk contains at most 30 bytes of object code.

    :param instructions: An iterable of instructions (typically excluding START and END).
    :yields: A list of instructions for a single text record and the length of the chunk.
    """
    chunk: list[Instruction] = []
    length = 0
    for instruction in instructions:
        # If the instruction is a directive (RESB, RESW), skip it and start a new chunk
        if instruction.op in (AsmDirectives.RESB, AsmDirectives.RESW):
            if chunk:
                yield chunk, length
                chunk = []
                length = 0
            continue

        ins_length = 0

        # If the instruction is an BYTE or WORD directive, add it to the chunk
        if instruction.op == AsmDirectives.BYTE:
            ins_length = len(instruction.parsed_ctx["value"])
        elif instruction.op == AsmDirectives.WORD:
            ins_length = 3
        # If the instruction is an OpcodeTable, add it to the chunk
        elif isinstance(instruction.op, OpcodeTable):
            ins_length = 3  # Each instruction is 3 bytes
        else:
            # If the instruction is not RESB, RESW, or an OpcodeTable,
            # it is likely a directive or an invalid instruction.
            raise ValueError(
                f"Invalid instruction {instruction.instruction_name} at line {instruction.line_number}"
            )

        # Check if the chunk has reached the maximum size
        overflow_after_ins = length + ins_length > TextRecord.MAX_TEXT_RECORD_SIZE

        if overflow_after_ins:
            yield chunk, length
            chunk = []
            length = 0

        # Add the instruction to the new chunk
        chunk.append(instruction)
        length += ins_length

    if chunk:
        yield chunk, length
