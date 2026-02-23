FROM python:3.12-slim

# Install tesseract
RUN apt-get update && \
    apt-get install -y tesseract-ocr && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Lambda runtime
RUN pip install awslambdaric

WORKDIR /var/task

COPY requirements.txt app.py ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "awslambdaric", "app.lambda_handler"]