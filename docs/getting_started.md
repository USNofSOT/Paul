# Getting Started with Paul

This guide covers the local development setup for Paul, including Python tooling, environment variables, the MariaDB
dependency via Docker, and the normal day-to-day commands used while working on the bot.

## Prerequisites

- **Python 3.13**: The bot is built for the latest Python.
- **[Astral UV](https://docs.astral.sh/uv/getting-started/installation/)**: For fast, reliable dependency management.
- **[Docker](https://www.docker.com/get-started)**: To run the local database.
- **Discord Bot Token**: You'll need a token from
  the [Discord Developer Portal](https://discord.com/developers/applications).

---

## 1. Environment Setup

### Install Dependencies

Install the required Python version and sync dependencies:

```bash
uv python install 3.13
uv sync --group dev --group lint
```

### Configure Environment Variables

Copy the example environment file and fill in your `DISCORD_TOKEN`:

```bash
cp .env.example .env
```

The database values in `.env.example` are pre-configured to work out-of-the-box with the included Docker configuration.

| Variable      | Local Value | Description                                      |
|:--------------|:------------|:-------------------------------------------------|
| `DB_HOST`     | `localhost` | Points to your local machine.                    |
| `DB_PORT`     | `3307`      | Matches the port mapped in `docker-compose.yml`. |
| `DB_NAME`     | `paul_dev`  | The default database created by Docker.          |
| `ENVIRONMENT` | `DEV`       | Enables development-specific features.           |

---

## 2. Database Setup

### Start MariaDB

Paul uses MariaDB for persistence. Use Docker to start a local instance:

```bash
docker compose up -d
```

This starts a MariaDB 10.11 container named `paul-db-dev` listening on port **3307**.

### Initialize the Schema

Paul's startup flow automatically creates missing tables via SQLAlchemy models. However, you must tell Alembic (the
migration tool) that the database is current:

```bash
# Set the current DB state to the latest revision
alembic stamp head
```

*Note: Use `alembic upgrade head` for future updates when new migration scripts are added to the repository.*

---

## 3. Running the Bot

Run the application from the repository root:

```bash
uv run src/main.py
```

### Startup Sequence

1. **Logging**: Initializes console and file logs.
2. **Database**: Reflects models and runs auto-migrations.
3. **Bot**: Connects to Discord and auto-discovers cogs in `src/cogs/`.

---

## Daily Workflow

| Task          | Command                                   |
|:--------------|:------------------------------------------|
| **Run Bot**   | `uv run src/main.py`                      |
| **Run Tests** | `uv run pytest tests`                     |
| **Lint**      | `uvx ruff check . --fix`                  |
| **Format**    | `uvx ruff format .`                       |
| **DB Health** | Use `/dbhealth` inside Discord (NSC only) |

---

### "Alembic revision conflict"

If the bot fails to start due to migrations, you might need to manually align the version:
```bash
alembic stamp head
```
