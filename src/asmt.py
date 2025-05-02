"""
A script to show the object program in a human-readable format.
"""

import argparse

from common.object_program import TextRecord
from common.program_iter import program_iter


def main():
    args = get_arg_parser().parse_args()
    program = args.program
    with open(program, "rb") as f:
        data = f.read()

    for record, buffer in program_iter(memoryview(data)):
        if isinstance(record, TextRecord):
            print(record, end=", ")
            for code in buffer[: record.length]:
                print(bytes((code,)).hex(), end=" ")
            print()
        else:
            print(record)


def get_arg_parser() -> argparse.ArgumentParser:
    """
    Get the argument parser for the program.

    :return: The argument parser.
    """
    parser = argparse.ArgumentParser(
        description="Show the object program in a human-readable format."
    )
    parser.add_argument(
        "program",
        type=str,
        help="The path to the object program file.",
    )
    return parser


if __name__ == "__main__":
    main()
