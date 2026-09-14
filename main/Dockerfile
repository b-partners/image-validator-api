FROM python:3.12-slim

# Install Lambda runtime
RUN pip install awslambdaric

WORKDIR /var/task

COPY requirements.txt app.py ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "-m", "awslambdaric", "app.lambda_handler"]