from collections.abc import Iterable
from contextlib import suppress
import re
from asm.create_object_program import create_object_program
from asm.directives import AsmDirectives
from asm.model import SYMTAB, Instruction, ObjectProgramRecord
from common.object_program import Int24, UInt24
from common.optable import OpcodeTable


def assemble_program(program: str) -> list[ObjectProgramRecord]:
    """
    Assemble the program into a list of Records.

    :param program: The program to assemble.
    :return: A list of Records representing the assembled program.
    """
    # Split the program into lines
    lines = program.splitlines()

    # Tokenize the lines
    line_tokens = tokenize(lines)

    # Parse the tokens and create the symbol table
    symtab, instructions, program_length = parse_and_create_symtab(line_tokens)

    return create_object_program(symtab, instructions, program_length)


def tokenize(lines: Iterable[str]) -> Iterable[tuple[int, list[str]]]:
    """
    Tokenize the input lines into a list of tokens.

    :param lines: The input lines to tokenize.
    :return: An iterable of lists of tokens.
    """
    for line_number, line in enumerate(lines, start=1):
        # Skip empty lines and comments
        if not line or line.rstrip().startswith("#"):
            continue

        # Remove line comments
        line = line.partition("#")[0]

        # Split the line into tokens
        tokens = line.split(maxsplit=2)

        tokens = [token.strip() for token in tokens if token.strip()]

        yield line_number, tokens


def parse_and_create_symtab(
    tokens: Iterable[tuple[int, list[str]]],
) -> tuple[SYMTAB, list[Instruction], int]:
    """
    Parse the tokens and create a symbol table and a list of instructions.

    :param tokens: The tokens to parse.
    :return: A tuple containing the symbol table and the list of instructions and the program length.
    """
    symtab = {}
    instructions = []
    starting_addr = 0
    locctr = 0

    for line_number, token in tokens:
        # Parse the instruction
        instruction = parse_instruction(token, locctr, line_number)

        # Determine the size of the instruction
        size = parse_and_determine_size(instruction)

        if instruction.op == AsmDirectives.START:
            # If the instruction is a START directive, set the location counter to the starting address
            starting_addr = locctr = instruction.parsed_ctx["starting_addr"]
        else:
            # Update the location counter
            locctr += size

        # add the instruction to the list of instructions
        instructions.append(instruction)

        # Add the label to the symbol table if it exists
        if instruction.label:
            symtab[instruction.label] = instruction.location

    return symtab, instructions, locctr - starting_addr


def parse_instruction(token: list[str], locctr: int, line_number: int) -> Instruction:
    """
    Parse a single instruction token.

    :param token: The token to parse.
    :param locctr: The location counter for the instruction.
    :param line_number: The line number of the instruction.
    :return: An Instruction object representing the parsed instruction.
    """

    match token:
        # Case 1: instruction only
        case [str(ins_name)]:
            instruction = Instruction(
                instruction_name=ins_name,
                op=determine_instruction(ins_name, line_number),
                location=locctr,
                line_number=line_number,
            )
        # Case 2: label instruction or instruction with operand
        case [str(first), str(second)]:
            # Check if the first token is a label or an instruction
            ins = None

            # suppress invalid instruction error and leave ins as None when not found
            with suppress(ValueError):
                ins = determine_instruction(first, line_number)

            # If instruction is found, the first token is an instruction
            if ins is not None:
                instruction = Instruction(
                    instruction_name=first,
                    op=ins,
                    location=locctr,
                    line_number=line_number,
                    label=None,
                    operand=second,
                )
            else:
                # Otherwise, the first token is a label
                ins = determine_instruction(second, line_number)
                instruction = Instruction(
                    instruction_name=second,
                    op=ins,
                    location=locctr,
                    line_number=line_number,
                    label=first,
                    operand=None,
                )
        # Case 3: label instruction with operand
        case [str(label), str(ins_name), str(operand)]:
            # Check if the first token is a label or an instruction
            ins = determine_instruction(ins_name, line_number)

            # If instruction is found, the first token is an instruction
            instruction = Instruction(
                instruction_name=ins_name,
                op=ins,
                location=locctr,
                line_number=line_number,
                label=label,
                operand=operand,
            )
        # Case 4: raise an error if the token is not valid
        case _:
            raise ValueError(f"Invalid instruction format: {token} at {line_number}")

    return instruction


def determine_instruction(ins_name: str, line_number: int) -> OpcodeTable | AsmDirectives:
    """
    Determine the instruction type based on the instruction name.

    :param ins_name: The name of the instruction.
    :param line_number: The line number of the instruction.
    :return: The corresponding OpcodeTable or AsmDirectives.
    :raises ValueError: If the instruction is not found in the opcode table or directive table.
    """
    # Try to find the instruction in the opcode table
    ins = OpcodeTable.__members__.get(ins_name)

    # If not found, try to find it in the directive table
    if ins is None:
        ins = AsmDirectives.__members__.get(ins_name)

    # If still not found, raise an error
    if ins is None:
        raise ValueError(f"Invalid instruction: {ins_name} at {line_number}")

    return ins


def parse_and_determine_size(instruction: Instruction) -> int:
    """
    Determine the size of the instruction.

    :param instruction: The instruction to determine the size of.
    :return: The size of the instruction in bytes.
    """

    line_number = instruction.line_number

    if instruction.label:
        # Check if the label is valid
        if not re.match(r"^[A-Z]{1,6}$", instruction.label):
            raise ValueError(f"Invalid label: {instruction.label} at {line_number}")

    ins = instruction.op

    if isinstance(ins, OpcodeTable):
        # For non-directive instructions, return the size based on the opcode
        # In this architecture, all instructions are 3 bytes

        # Check if the instruction has an operand
        if ins.value.has_operand and instruction.operand is None:
            raise ValueError(
                f"Instruction {instruction.instruction_name} requires an operand at {line_number}"
            )

        # Check operand is valid if it exists
        if instruction.operand is not None:
            # Check if the operand is 6-char alphabetical
            match_result = re.match(r"^([A-Z]{1,6})(,X)?$", instruction.operand)
            if match_result is None:
                raise ValueError(
                    f"Invalid operand {instruction.operand} for instruction: {instruction.instruction_name} at {line_number}"
                )

            # Check if the operand is an indexed operand
            if match_result.group(2) == ",X":
                instruction.parsed_ctx["indexed"] = True

            instruction.parsed_ctx["symbol"] = match_result.group(1)
            assert isinstance(instruction.parsed_ctx["symbol"], str), (
                f"Invalid symbol: {instruction.parsed_ctx['symbol']} at {line_number}"
            )

        return 3

    # For directives, return the size based on the directive type

    # Directives START and END are 0 bytes (no size)
    if ins == AsmDirectives.START:
        if instruction.label is None:
            raise ValueError(
                f"START directive requires a program name: {instruction.instruction_name} at {line_number}"
            )
        instruction.parsed_ctx["program_name"] = instruction.label

        if instruction.operand is None:
            raise ValueError(
                f"START directive requires an starting_addr: {instruction.instruction_name} at {line_number}"
            )
        # Check if the operand is a hexadecimal number
        if not re.match(r"^[0-9A-Fa-f]{4}$", instruction.operand):
            raise ValueError(
                f"Invalid operand for START directive: {instruction.operand} at {line_number}"
            )
        instruction.parsed_ctx["starting_addr"] = int(instruction.operand, 16)
        return 0

    if ins == AsmDirectives.END:
        exec_addr = 0
        if instruction.operand is not None:
            # Check if the operand is a hexadecimal number
            if not re.match(r"^[0-9A-Fa-f]{4}$", instruction.operand):
                raise ValueError(
                    f"Invalid operand for END directive: {instruction.operand} at {line_number}"
                )
            exec_addr = int(instruction.operand, 16)
        instruction.parsed_ctx["exec_addr"] = exec_addr
        return 0

    # Directives RESB and RESW's size is determined by the operand
    if ins in [
        AsmDirectives.RESB,
        AsmDirectives.RESW,
    ]:
        if instruction.operand is None:
            raise ValueError(
                f"RESB/RESW directive requires an operand: {instruction.instruction_name} at {line_number}"
            )

        # Convert the operand to an integer
        try:
            num = int(instruction.operand)
        except ValueError:
            raise ValueError(
                f"Invalid operand for RESB/RESW: {instruction.operand} at {line_number}"
            )

        # For RESB, the size is the operand value
        # For RESW, the size is 3 times the operand value
        multiplier = 1 if instruction.op == AsmDirectives.RESB else 3

        return num * multiplier

    # For WORD directives, the size is always 3 bytes
    if ins == AsmDirectives.WORD:
        # Parse the operand
        if instruction.operand is None:
            raise ValueError(
                f"WORD directive requires an operand: {instruction.instruction_name} at {line_number}"
            )
        instruction.parsed_ctx["value"] = parse_word_operand(
            instruction.operand, line_number
        )

        return 3

    # For BYTE directives, the size is determined by the operand
    if ins == AsmDirectives.BYTE:
        # Parse the operand
        if instruction.operand is None:
            raise ValueError(
                f"BYTE directive requires an operand: {instruction.instruction_name} at {line_number}"
            )
        value = parse_byte_operand(instruction.operand, line_number)

        instruction.parsed_ctx["value"] = value
        if not (1 <= len(value) <= 30):
            raise ValueError(
                f"BYTE directive operand must be between 1 and 30 bytes: {instruction.operand} at {line_number}"
            )

        # The size is the length of the byte array
        return len(value)

    # For all other directives, raise an error
    raise ValueError(
        f"Invalid directive: {instruction.instruction_name} at {line_number}"
    )


def parse_word_operand(operand: str, line_number: int) -> UInt24:
    """
    Parse the operand of a WORD directive.

    :param operand: The operand to parse.
    :param line_number: The line number of the instruction.
    :return: The parsed operand as an integer.
    """
    # Check if the operand is a hexadecimal number
    if operand.startswith("0x") and len(operand) == 8:
        return UInt24.from_int(int(operand, 16))

    # Check if the operand is a unsigned decimal number ending with 'U'
    if operand.endswith("U"):
        # Remove the 'U'
        digit_part = operand[:-1]

        # Check if the remaining part are digits
        if digit_part.isdigit():
            return UInt24.from_int(int(digit_part))

        # If not, raise an error
        raise ValueError(
            f"Invalid operand for WORD directive: {operand} at {line_number}"
        )

    # Check if the operand is a decimal number
    try:
        return UInt24.from_buffer(Int24.from_int(int(operand)))
    except ValueError:
        raise ValueError(
            f"Invalid operand for WORD directive: {operand} at {line_number}"
        )


def parse_byte_operand(operand: str, line_number: int) -> bytearray:
    """
    Parse the operand of a BYTE directive.

    :param operand: The operand to parse.
    :param line_number: The line number of the instruction.
    :return: The parsed operand as a byte array.
    """
    try:
        # Check if the operand is a hexadecimal number
        if operand.startswith("0x") and len(operand) == 4:
            # Remove the '0x' prefix
            hex_part = operand[2:]

            # Convert the hexadecimal part to bytes
            return bytearray.fromhex(hex_part)

        # Check if the operand is a character string (c'string')
        if operand.startswith("c'") and operand.endswith("'"):
            # Remove the quotes
            char_part = operand[2:-1]

            # Convert the character part to bytes
            return bytearray(char_part, "ascii")
    except ValueError:
        # If the conversion fails, raise an error
        raise ValueError(
            f"Invalid operand for BYTE directive: {operand} at {line_number}"
        )

    # If not, raise an error
    raise ValueError(f"Invalid operand for BYTE directive: {operand} at {line_number}")
