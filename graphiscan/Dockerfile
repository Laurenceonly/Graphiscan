FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    CUDA_VISIBLE_DEVICES=-1 \
    HOME=/tmp

WORKDIR /app
COPY requirements-hosted.txt ./
RUN pip install --no-cache-dir -r requirements-hosted.txt

# The context allowlist excludes configuration, datasets and student images.
COPY hosted_api.py gunicorn.conf.py api_v1.py predict.py v1_*.py ./
COPY db/postgres/access_snapshot.sql ./db/postgres/access_snapshot.sql
# Provision these private artifacts outside Git before building the container.
# Keep the manifest's source and artifact hash checks intact.
COPY model/class_names.json ./model/class_names.json
COPY model/deployment.local.json ./model/deployment.local.json
COPY model/versions/ ./model/versions/

ENV GRAPHISCAN_V1_MODEL_MANIFEST=/app/model/deployment.local.json
USER 10001:10001
EXPOSE 8080
CMD ["gunicorn", "--config", "gunicorn.conf.py", "hosted_api:create_app()"]
