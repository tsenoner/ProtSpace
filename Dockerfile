# syntax=docker/dockerfile:1.9

# Based off https://hynek.me/articles/docker-uv/
FROM python:3.12-slim AS build

SHELL ["sh", "-exc"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12 \
    UV_PROJECT_ENVIRONMENT=/app

COPY pyproject.toml /src/
COPY uv.lock /src/

RUN --mount=type=cache,target=/root/.cache <<EOT
cd /src
uv sync \
    --all-extras \
    --locked \
    --no-dev \
    --no-install-project
EOT


COPY . /src
RUN --mount=type=cache,target=/root/.cache \
uv pip install \
        --python=$UV_PROJECT_ENVIRONMENT \
        --no-deps \
        /src

#########################################################################
FROM python:3.12-slim

SHELL ["sh", "-exc"]
WORKDIR /app

ENV PATH=/app/bin:$PATH

# Don't run your app as root.
RUN <<EOT
groupadd -r app
useradd -r -d /app -g app -N app
EOT

# See <https://hynek.me/articles/docker-signals/>.
STOPSIGNAL SIGINT

COPY --from=build --chown=app:app /app /app

RUN <<EOT
python -V
python -Im site
python -Ic 'import protspace'
EOT
