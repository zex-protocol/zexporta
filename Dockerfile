FROM python:3.12-slim

RUN apt update -y && apt install gcc libgmp-dev curl git -y

ADD https://astral.sh/uv/0.5.24/install.sh /uv-installer.sh

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=libs,target=libs \
    uv sync --frozen --no-install-project --no-editable

# Copy the project into the intermediate image
ENV PATH="/app/.venv/bin:$PATH"

COPY ./zexporta/ /app/zexporta
