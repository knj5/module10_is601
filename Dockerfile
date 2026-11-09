FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* \
    && groupadd --system appgroup && useradd --system --gid appgroup appuser
COPY requirements.txt .
RUN python -m pip install --upgrade pip && python -m pip install -r requirements.txt
COPY --chown=appuser:appgroup app ./app
COPY --chown=appuser:appgroup templates ./templates
COPY --chown=appuser:appgroup main.py .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM runtime AS test
USER root
COPY requirements-dev.txt .
RUN python -m pip install -r requirements-dev.txt
COPY --chown=appuser:appgroup tests ./tests
COPY --chown=appuser:appgroup pytest.ini .
RUN chown appuser:appgroup /app
USER appuser
CMD ["python", "-m", "pytest", "tests/unit", "tests/integration"]
