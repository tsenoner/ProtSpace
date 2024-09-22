#!/usr/bin/env bash
# exit on error
set -o errexit

# create requirements.txt from pyproject.toml and install with pip
poetry export -f requirements.txt --output requirements.txt
poetry add gunicorn
pip install -r requirements.txt