FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

# Create non-root user for security
RUN groupadd --system --gid 999 nonroot \
 && useradd --system --gid 999 --uid 999 --create-home nonroot

WORKDIR /app

# Configure uv environment variables
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Install dependencies (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY . /app

# Install project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Change ownership to nonroot user
RUN chown -R nonroot:nonroot /app

# Add virtualenv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Expose port
EXPOSE 8000

# Switch to non-root user
USER nonroot

# Run uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
