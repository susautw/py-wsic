import argparse
from contextlib import ExitStack
from pathlib import Path
import sys
from tempfile import NamedTemporaryFile
import time

import numpy as np

from common.object_program import SICFormatObjectCode, UInt24

from common.optable import EffectOption, OpcodeTable, code_lut
from common.reg import Registers
from sim.loader import load_program


def bootstrap_program():
    """
    BOOT  START 0000     #0x0000
    FIRST JSUB  XXXX     #0x0000
          HLT            #0x0003
          END   FIRST    #0x0006
    """
    bootstrap = [
        SICFormatObjectCode.create(OpcodeTable.JSUB, 0),
        SICFormatObjectCode.create(OpcodeTable.HLT, 0),
    ]

    # convert to bytes
    bootstrap_bytes = list(b"".join(bytes(record) for record in bootstrap))
    return bootstrap_bytes


def main():
    args = get_arg_parser().parse_args()
    if args.speed is not None and args.speed > 0:
        speed = 1 / args.speed
    else:
        speed = None

    with ExitStack() as stack:
        tmp_file = stack.enter_context(NamedTemporaryFile())
        v_memory = np.memmap(
            tmp_file,
            mode="w+",
            shape=(0x7FFF,),
            dtype=np.uint8,
        )

        # Create the bootstrap program
        bootstrap = bootstrap_program()
        # Write the bootstrap program to the memory
        v_memory[: len(bootstrap)] = bootstrap

        # Load the program into memory
        exec_address = load_program(
            v_memory,
            args.program,
            start_location=len(bootstrap),
        )

        # write execution address to memory
        v_memory[0x0001:0x0003] = list(bytes(exec_address.to_bytes(2, "little")))

        print(f"Exec address: 0x{exec_address:04X}")

        registers = {r: UInt24.from_int(0) for r in Registers}
        registers[Registers.PC] = UInt24.from_int(0)  # point to bootstrap program

        start_time = time.monotonic()

        try:
            while True:
                # Fetch the instruction
                raw_pc = registers[Registers.PC]
                pc = raw_pc.to_int()
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

                # Increment the program counter
                registers[Registers.PC] = UInt24.from_int(
                    registers[Registers.PC].to_int() + 3
                )

                # Print the instruction
                print(
                    f"0x{raw_pc.to_int():04X} | "
                    f"{code_lut[opcode].name:6}"
                    f"INDEXED: {indexed:1}  ",
                    f"TADDR: 0x{decoded_address:04X}  "
                    f"MEMORY: 0x{int.from_bytes(v_memory[decoded_address : decoded_address + 3], 'little'):06X}  ",
                    f"REGISTERS: {registers}",
                    file=sys.stderr,
                )

                # Execute the instruction
                op.value.effect(
                    EffectOption(
                        memory=v_memory,
                        registers=registers,
                        decoded_address=decoded_address,
                    )
                )

                if speed is not None:
                    # Sleep for the given speed
                    time.sleep(speed)

        except KeyboardInterrupt as e:
            print(e)

        finally:
            end_time = time.monotonic()
            print(f"Execution time: {end_time - start_time:.2f} seconds")


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Simulate a system in WSIC architecture.",
    )
    parser.add_argument(
        "program",
        type=Path,
        help="Path to the program file.",
    )

    parser.add_argument(
        "-s",
        "--speed",
        type=int,
        required=False,
    )
    return parser


if __name__ == "__main__":
    main()
