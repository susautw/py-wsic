import argparse
from contextlib import ExitStack
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np

from common.object_program import SICFormatObjectCode, UInt24

from common.optable import EffectOption, code_lut
from common.reg import Registers
from sim.loader import load_program


def main():
    args = get_arg_parser().parse_args()

    with ExitStack() as stack:
        tmp_file = stack.enter_context(NamedTemporaryFile())
        v_memory = np.memmap(
            tmp_file,
            mode="w+",
            shape=(0xFFFFFF,),
            dtype=np.uint8,
        )

        # Load the program into memory
        exec_address, terminal_address = load_program(
            v_memory,
            args.program,
            start_location=0x000000,
        )

        print(
            f"Exec address: {exec_address:06X}, Terminal address: {terminal_address:06X}"
        )

        registers = {r: UInt24.from_int(0) for r in Registers}
        registers[Registers.PC] = UInt24.from_int(exec_address)

        try:
            while True:
                # Fetch the instruction
                pc = registers[Registers.PC].to_int()
                instruction = v_memory[pc : pc + 3]

                # Decode the instruction
                decoded_instruction = SICFormatObjectCode.from_buffer(instruction)
                opcode = decoded_instruction.opcode
                address = decoded_instruction.address
                indexed = decoded_instruction.indexed
                decoded_address = address + (
                    registers[Registers.X].to_int() if indexed else 0
                )
                op = code_lut.get(opcode)
                if op is None:
                    print(f"Unknown opcode: {opcode}")
                    break

                # Execute the instruction
                result = op.value.effect(
                    EffectOption(
                        memory=v_memory,
                        registers=registers,
                        decoded_address=decoded_address,
                    )
                )

                if result is None or not result.jumped:
                    # Increment the program counter
                    new_pc = pc + 3
                    if new_pc >= terminal_address:
                        print("End of program")
                        break
                    registers[Registers.PC] = UInt24.from_int(new_pc)

        except KeyboardInterrupt as e:
            print(e)


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulate a system in WSIC architecture.",
    )
    parser.add_argument(
        "program",
        type=Path,
        help="Path to the program file.",
    )
    return parser


if __name__ == "__main__":
    main()
