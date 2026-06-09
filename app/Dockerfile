# ============================================================
# Stage 1: Builder
# ============================================================
FROM python:3.11-alpine AS builder

WORKDIR /app

# Alpine needs these to compile some Python packages
RUN apk add --no-cache gcc musl-dev libffi-dev

COPY requirements.txt .

RUN pip install --no-cache-dir --user -r requirements.txt


# ============================================================
# Stage 2: Runtime — Alpine has no Perl, much smaller attack surface
# ============================================================
FROM python:3.11-alpine AS runtime

# Security: create a non-root user
RUN adduser -D -s /bin/sh appuser

WORKDIR /app

# Copy installed libraries from builder
COPY --from=builder /root/.local /home/appuser/.local

# Copy app code
COPY --chown=appuser:appuser app.py .

USER appuser

ENV PATH=/home/appuser/.local/bin:$PATH

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8080/health')" \
    || exit 1

CMD ["python3", "app.py"]
