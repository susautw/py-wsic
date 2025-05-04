# WISC Assmebler & Simulator

# Setup
1. Clone the repository
```bash
git clone https://github.com/susautw/py-wsic.git
cd py-wsic
```

2. Install [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#installation)

3. sync with uv
```bash
uv sync
```
4. Run the tests
```bash
uv run python -m asm test_programs/helloworld.asm  # run the assembler

# ls -l output.obj  # list the object file produced (optional)

uv run python -m asmt output.obj  # show the object file produced

uv run python -m sim output.obj 2>exec.log # run the simulator, redirecting stderr to exec.log

# you can examine the log file to see the process of the simulator

# run the simulator with a speed of 25 instructions per second
uv run python -m sim output.obj --speed 25 2>exec.log 
```