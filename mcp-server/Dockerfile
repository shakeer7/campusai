# Production Dockerfile for CampusAI Model Context Protocol (MCP) Server
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY mcp-server/requirements.txt ./
COPY backend/requirements.txt ./backend_requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r backend_requirements.txt

# Copy MCP server code and backend code
COPY mcp-server/ /app/
COPY backend/ /app/backend/

ENV PYTHONPATH=/app/backend:$PYTHONPATH
ENV PYTHONUNBUFFERED=1

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

CMD ["python", "server.py"]
