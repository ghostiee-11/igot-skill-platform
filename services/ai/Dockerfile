FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.12.4 /uv /uvx /bin/
WORKDIR /app
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/src
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev --no-editable
EXPOSE 8105
CMD ["uvicorn","igot_ai.main:app","--host","0.0.0.0","--port","8105"]
