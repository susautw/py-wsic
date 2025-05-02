import argparse
from pathlib import Path

from asm.assemble import assemble_program


def main():
    args = get_arg_parser().parse_args()

    # Read the program file
    with open(args.program, "r") as f:
        program = f.read()

    # Assemble the program
    assembled_program = assemble_program(program)

    # Write the assembled program to the output file
    with open(args.output, "wb") as f:
        for record in assembled_program:
            f.write(record)


def get_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Assemble a program in WSIC architecture.",
    )
    parser.add_argument(
        "program",
        type=Path,
        help="Path to the program file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=Path("output.obj"),
        help="Path to the output file.",
    )

    return parser


if __name__ == "__main__":
    main()
