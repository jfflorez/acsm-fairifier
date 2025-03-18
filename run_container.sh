#!/bin/bash

# Define container name and image
CONTAINER_NAME="datachain_processor"
IMAGE_NAME="datachain_processor"

# Define ports
PORTS=(
    "-p" "8889:8888"
    "-p" "8050:8050"
)

# Define environment variables
ENV_VARS=(
    "-e" "DOCKER_CONTAINER=1"
)

# Define volumes (add more as needed)
VOLUMES=(
    "-v" "$(pwd)/data:/acsmdc/data"
    "-v" "$(pwd)/figures:/acsmdc/figures"
    "-v" "$(pwd)/pipelines/params:/acsmdc/pipelines/params"
)

# Combine all options
DOCKER_OPTS=(
    "--rm"
    "-it"
    "${PORTS[@]}"
    "${ENV_VARS[@]}"
    "${VOLUMES[@]}"
)

# Run the container
docker run "${DOCKER_OPTS[@]}" "$IMAGE_NAME" bash -c "jupyter lab --NotebookApp.token='my-token' --ip=0.0.0.0 --allow-root & python app/data_flagging_app.py"