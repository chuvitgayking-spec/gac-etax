# Dockerfile with Thai font support
FROM python:3.11-slim

# Install Thai fonts and dependencies
RUN apt-get update && apt-get install -y \
    fonts-thai-tlwg \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Expose Streamlit
EXPOSE 8501

# Run
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"]
