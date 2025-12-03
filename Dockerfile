FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install --with-deps chromium

# Copy all project files
COPY . .

# Expose port 5000
EXPOSE 5000

# Environment variables for proper flask operation
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Start the app.
CMD ["python", "app.py"]