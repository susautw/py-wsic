# WISC Assmebler & Simulator

# Setup
1. Install [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)

2. sync with uv
```bash
uv sync
```
3. Run the tests
```bash
uv run python -m asm test_programs/helloworld.asm  # run the assembler

# ls -l output.obj  # list the object file produced (optional)

uv run python -m asmt output.obj  # show the object file produced

uv run python -m sim output.obj 2>exec.log # run the simulator, redirecting stderr to exec.log

# you can examine the log file to see the process of the simulator
```