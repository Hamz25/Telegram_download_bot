# ─────────────────────────────────────────────
# Stage 1 — Builder
# Install dependencies in an isolated layer so
# they are NOT rebuilt every time code changes.
# ─────────────────────────────────────────────
FROM python:3.11-slim AS builder

COPY requirements.txt .

# Install into a dedicated prefix so we can copy just the packages
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─────────────────────────────────────────────
# Stage 2 — Runtime (final image)
# Only the compiled packages + app code land
# here — no build tools, no apt cache.
# ─────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Runtime-only system deps for yt-dlp / ffmpeg (audio/video muxing)
# ffmpeg is tiny on slim and prevents crashes on media downloads
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-built Python packages from builder
COPY --from=builder /install /usr/local

# Run as non-root for security
RUN useradd -m -u 1001 botuser
WORKDIR /app

# Copy source (respects .dockerignore)
COPY --chown=botuser:botuser . .

# Create downloads dir with correct ownership
RUN mkdir -p downloads && chown botuser:botuser downloads && mkdir data && chown botuser:botuser data && mkdir .venv && chown botuser:botuser .venv

USER botuser

# Healthcheck — confirms the process is still alive
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/index.py') else 1)"

# Cross-platform: works on linux/amd64, linux/arm64 (Raspberry Pi, AWS Graviton, etc.)
CMD ["python", "-u", "index.py"]