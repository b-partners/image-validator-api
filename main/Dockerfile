FROM public.ecr.aws/lambda/python:3.12
COPY requirements.txt app.py ./
RUN pip install --no-cache-dir -r requirements.txt
CMD ["app.lambda_handler"]