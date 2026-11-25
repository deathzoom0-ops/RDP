FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --system bridge && mkdir -p /data && chown bridge /data
COPY bridge.py .
ENV BRIDGE_DB=/data/jobs.sqlite3
VOLUME /data
USER bridge
EXPOSE 8080
CMD ["gunicorn", "-w", "1", "--threads", "4", "-b", "0.0.0.0:8080", "bridge:app"]
