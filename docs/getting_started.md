# Getting Started with Paul

## Using Astral UV (Recommended)
To get started with the bot, we recommend using [Astral UV](https://docs.astral.sh/uv/getting-started/installation/) to manage your Python environment. This will ensure that you have the correct version of Python and all necessary dependencies installed.

### Step 1: Install UV

Follow the instructions from the [official UV installation guide](https://docs.astral.sh/uv/getting-started/installation/).

#### Step 2: Install Python 3.12 with UV

```bash
uv python install 3.12
```

### Step 3: Create a Virtual Environment

```bash
uv venv .venv
```

### Step 4: Start up Paul
```bash
uv run src/main.py
```

### Some useful commands:

#### Run test suite
```bash
uv run pytest tests
```

### Run linter
```bash
uvx ruff check --fix
```

### Run formatter
```bash
uvx ruff format
```