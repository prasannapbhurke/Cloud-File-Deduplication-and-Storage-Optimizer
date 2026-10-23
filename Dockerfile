FROM python:3.10-slim

# Set up non-root user (Hugging Face Spaces UID 1000 requirement)
RUN useradd -m -u 1000 user
USER user
ENV HOME=/home/user \
    PATH=/home/user/.local/bin:$PATH \
    PORT=7860 \
    PYTHONUNBUFFERED=1

WORKDIR $HOME/app

# Install dependencies
COPY --chown=user:user requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY --chown=user:user . .

# Ensure storage directories exist with proper write permissions
RUN mkdir -p cloud_storage_bucket/chunks

EXPOSE 7860

# Run with Gunicorn on port 7860
CMD ["gunicorn", "-b", "0.0.0.0:7860", "--workers", "2", "--timeout", "120", "app:app"]
