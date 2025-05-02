from dataclasses import dataclass, field
from typing import Any

from asm.directives import AsmDirectives
from common.object_program import Records, SICFormatObjectCode, UInt24
from common.optable import OpcodeTable


@dataclass
class Instruction:
    instruction_name: str
    op: OpcodeTable | AsmDirectives
    location: int
    line_number: int
    label: str | None = None
    operand: str | None = None
    parsed_ctx: dict[str, Any] = field(default_factory=dict)


type SYMTAB = dict[str, int]

type ObjectProgramRecord = Records | SICFormatObjectCode | bytearray | UInt24
