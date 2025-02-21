# Stage 1: Build stage
# Specify the debian distribution to prevent update with out knowing
FROM python:3.12-slim-bookworm AS build-stage

# Install required dependencies
RUN apt update -y && apt install -y gcc libgmp-dev curl git && rm -rf /var/lib/apt/lists/*

# Add the uv installer script
ADD https://astral.sh/uv/0.5.24/install.sh /uv-installer.sh

# Run the uv installer and clean up
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure uv is in PATH
ENV PATH="/root/.local/bin:$PATH"

# Set work directory
WORKDIR /app

# Install dependencies using uv with cache support for faster builds
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    --mount=type=bind,source=libs,target=libs \
    uv sync --frozen --refresh --no-editable

# Stage 2: Runtime stage
FROM python:3.12-slim-bookworm AS runtime

# Install runtime dependencies
RUN apt update -y && apt install -y libgmp-dev && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy virtual environment and project files from the build stage
COPY --from=build-stage /app/.venv /app/.venv
COPY ./zexporta/ /app/zexporta

# Add virtual environment to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create a group and user
RUN addgroup appgroup && adduser --ingroup appgroup appuser

# Tell docker that all future commands should run as the appuser user
USER appuser
