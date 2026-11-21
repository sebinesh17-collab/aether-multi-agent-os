FROM python:3.12-slim
WORKDIR /sandbox
RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm git curl build-essential && rm -rf /var/lib/apt/lists/* && pip install --no-cache-dir -r requirements.txt && useradd -m runner && mkdir -p /workspace && chmod 777 /workspace
COPY server.py /sandbox/server.py
USER runner
EXPOSE 8090
CMD ["uvicorn","server:app","--host","0.0.0.0","--port","8090"]
