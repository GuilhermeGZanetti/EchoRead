# Stage 1: Build the application with Poetry
FROM python:3.8-slim as builder

WORKDIR /app
RUN pip install poetry
COPY pyproject.toml poetry.lock* ./
RUN poetry config virtualenvs.create false && poetry install --no-dev --no-interaction --no-ansi --no-root

# Stage 2: Setup the runtime environment
FROM python:3.8-slim

WORKDIR /app

# Copy installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
# Copy the alembic executable installed by poetry in the builder stage
# This path might vary depending on Python version and poetry config,
# /usr/local/bin is a common place for executables.
COPY --from=builder /usr/local/bin/alembic /usr/local/bin/alembic


COPY . . # Copies the rest of the app, including alembic folder and alembic.ini

# Run database migrations
# poetry run ensures that alembic is run with the correct environment and dependencies
RUN poetry run alembic upgrade head

EXPOSE 8000
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-c", "/app/gunicorn_conf.py", "echoread.api_server.main:app"]
