FROM python:3.12-alpine@sha256:78e98729f8fc4099e53cffb3fe59fd15b18dfa4ace8c914dee0cefa5320068eb
RUN apk add --no-cache libuuid=2.42.3-r1
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /workspace
COPY . /workspace
USER 1000:1000
CMD ["python", "benchmark.py"]
