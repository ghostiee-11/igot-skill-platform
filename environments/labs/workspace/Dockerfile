FROM python:3.12-slim

RUN groupadd --system learner && useradd --system --gid learner --create-home learner \
    && pip install --no-cache-dir marimo==0.24.1 pandas==2.3.3 numpy==2.3.4

WORKDIR /opt/lab
COPY --chown=learner:learner app.py /opt/lab/app.py
USER learner
ENV HOME=/tmp
EXPOSE 2718

CMD ["python", "-m", "marimo", "run", "/opt/lab/app.py", "--host", "0.0.0.0", "--port", "2718", "--no-token", "--headless"]
