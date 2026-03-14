# --------------------------------------------------------------
# Dockerfile – builds a container that runs your Streamlit app
# --------------------------------------------------------------
FROM python:3.12-slim

# ---- System deps (needed for pandas, binance, etc.) ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc git libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- Create a non‑root user (good practice) ----------
RUN useradd -m appuser
WORKDIR /home/appuser
USER appuser

# ---- Copy the Python requirements file -------------------------
COPY requirements.txt .

# ---- Install Python dependencies (this creates the `streamlit` command) ----
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy the rest of the source code -------------------------
COPY streamlit_app.py .
COPY bot/ ./bot/
# If you still want to ship a proxy list, place the file in the repo root
# COPY webshare_proxies.txt webshare_proxies.txt    # <-- optional, no quotes

# ---- Expose the Streamlit port (default 8501) ---------------
EXPOSE 8501

# ---- Run the app (Render, Railway, Fly all inject $PORT) ----
ENV PORT=8501
CMD streamlit run streamlit_app.py \
    --server.port $PORT \
    --server.headless true
