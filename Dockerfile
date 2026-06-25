FROM python:3.11

# Force python stdout/stderr to be unbuffered so logs print in real-time
ENV PYTHONUNBUFFERED=1

# Install tesseract-ocr and libgl1 (graphics library for streamlit/pillow)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set env flag to prevent hnswlib (ChromaDB dependency) from compiling with native CPU optimizations
# that fail on virtualized cloud build environments
ENV HNSWLIB_NO_NATIVE=1

# Copy requirements, upgrade pip/setuptools/wheel, and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 8501

# Run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
