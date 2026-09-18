FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.4 /uv /uvx /bin/
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/src
COPY pyproject.toml uv.lock alembic.ini ./
COPY src ./src
COPY migrations ./migrations
RUN uv sync --frozen --no-dev --no-editable
ENV PORT=8104
EXPOSE 8104
CMD ["sh","-c","uvicorn igot_competency.main:app --host 0.0.0.0 --port ${PORT}"]
