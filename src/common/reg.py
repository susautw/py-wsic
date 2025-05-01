import enum


class Registers(enum.IntEnum):
    """Registers for the CPU and their corresponding register numbers."""

    A = enum.auto()
    """Accumulator register"""

    X = enum.auto()
    """Index register"""

    L = enum.auto()
    """Linkage register"""

    PC = enum.auto()
    """Program counter register"""

    SW = enum.auto()
    """Status word register"""

    S = enum.auto()
    """general purpose register"""

    def __repr__(self):
        return f"REG_{self.name}"
