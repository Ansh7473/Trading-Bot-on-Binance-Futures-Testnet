# --------------------------------------------------------------
# Dockerfile – builds a container that runs your Streamlit app
# --------------------------------------------------------------
FROM python:3.12-slim

# ---- System dependencies -------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc git libssl-dev libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# ---- Create a non-root user ----------------------------------
RUN useradd -m appuser
WORKDIR /home/appuser

# ---- Add local bin to PATH for the user ----------------------
ENV PATH="/home/appuser/.local/bin:${PATH}"

# ---- Switch to non-root user ---------------------------------
USER appuser

# ---- Copy requirements and install dependencies --------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy source code ----------------------------------------
COPY streamlit_app.py .
COPY bot/ ./bot/
COPY "webshare_proxies.txt" "webshare_proxies.txt"
# ---- Expose port ---------------------------------------------
EXPOSE 8501

# ---- Run the app ---------------------------------------------
ENV PORT=8501
CMD streamlit run streamlit_app.py \
    --server.port $PORT \
    --server.headless true
