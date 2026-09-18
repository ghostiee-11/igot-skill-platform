FROM python:3.12-alpine

RUN addgroup -S target && adduser -S -G target target
WORKDIR /srv
COPY --chown=target:target index.html /srv/index.html
USER target
EXPOSE 8080
CMD ["python", "-m", "http.server", "8080", "--bind", "0.0.0.0", "--directory", "/srv"]
