# Getting Started with Paul

This guide covers the local development setup for Paul, including Python tooling, environment variables, the MySQL
dependency, and the normal day-to-day commands used while working on the bot.

## Prerequisites

- Python 3.12
- [Astral UV](https://docs.astral.sh/uv/getting-started/installation/)
- Access to a MySQL database for local development
- A Discord bot token and any environment-specific values you need for testing

## 1. Install Python and Dependencies

Install Python 3.12 through `uv` if you do not already have it:

```bash
uv python install 3.12
```

Create the environment and install project dependencies:

```bash
uv venv .venv
uv sync --group dev --group lint
```

The `dev` group installs test dependencies and the `lint` group installs Ruff.

## 2. Configure Environment Variables

Copy `.env.example` to `.env` and fill in the values you need for your local setup.

Core values used by the current startup flow include:

- `DISCORD_TOKEN`
- `DB_HOST`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `ENVIRONMENT`
- `LOGS_PERSISTENCE`
- `LOGS_MAX_AGE_IN_DAYS`

The code currently reads `DB_PORT` in `src/data/engine.py`, but the active connection string is still built from host,
database, user, and password only. For now, prefer a MySQL setup that is reachable through `DB_HOST` without relying on
a custom port in the DSN.

## 3. Prepare MySQL

Paul uses SQLAlchemy plus Alembic migrations against a MySQL database. Before starting the bot:

- Create or choose a database for local development.
- Make sure the credentials in `.env` can connect to it.
- Confirm the database is reachable from your machine before running the app.

On startup, Paul will create tables from the SQLAlchemy models and then run migrations, so the database should be
available before you start the process.

## 4. Start the Bot

Run the application from the repository root:

```bash
uv run src/main.py
```

The startup sequence in [`src/main.py`](src/main.py) is:

1. `initialise_logger()`
2. `create_tables()`
3. `run_migrations(engine_string)`
4. `asyncio.run(main())`
5. `Bot.setup_hook()` loads all extensions discovered from `src.cogs`

If startup succeeds, the bot will connect to Discord and send a startup summary to the configured bot log channel.

## Daily Workflow

Run the bot:

```bash
uv run src/main.py
```

Run tests:

```bash
uv run pytest tests
```

Run the linter:

```bash
uvx ruff check .
```

Format code:

```bash
uvx ruff format .
```

## Troubleshooting

- If the bot fails before connecting, check the database settings in `.env` first.
- If Discord startup fails, verify `DISCORD_TOKEN` and the environment-specific bot log configuration in
  `src/config/main_server.py`.
- If MySQL is running on a non-default port, note that the current engine string does not yet append `DB_PORT`.
- If a new cog is not loading, confirm it lives under `src/cogs` and is a valid Python module; extension discovery is
  automatic.
