# ---- Base image -------------------------------------------------
FROM python:3.12-slim

# ---- System dependencies -----------------------------------------
# (required for pandas, streamlit, and the binance client)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc git libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- Create a non‑root user (optional but recommended) ----------
RUN useradd -m appuser
WORKDIR /home/appuser
USER appuser

# ---- Copy source code --------------------------------------------
COPY requirements.txt .
COPY streamlit_app.py .
COPY bot/ ./bot/
COPY "webshare_proxies.txt" "webshare_proxies.txt"

# ---- Install Python dependencies ----------------------------------
RUN pip install --no-cache-dir -r requirements.txt

# ---- Expose the port Streamlit will use ---------------------------
EXPOSE 8501

# ---- Run the app -------------------------------------------------
# $PORT is injected by Render/Railway/Fly; otherwise default to 8501
ENV PORT=8501
CMD streamlit run streamlit_app.py --server.port $PORT --server.headless true
