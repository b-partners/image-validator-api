FROM python:3.12-slim

# Install Lambda runtime
RUN pip install awslambdaric

# Tesseract binary requis par pytesseract pour la detection de texte "failed"/"wmts"
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /var/task

COPY requirements.txt app.py ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "awslambdaric", "app.lambda_handler"]