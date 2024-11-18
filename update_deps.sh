#!/bin/bash
# Generate lock files for different Python versions
for version in 3.10 3.11 3.12; do
    echo "Generating requirements for Python ${version}"
    uv pip compile pyproject.toml -o "requirements-py${version//.}.txt" --python-version=${version}
done

# Update the main uv.lock file
uv lock