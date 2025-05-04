FROM python:3.12-slim
WORKDIR /workspace
COPY . .
ENV PYTHONPATH=/workspace
EXPOSE 8002
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["sh", "-c", "python payment_service/app.py & celery -A background_tasks.app worker --loglevel=info & celery -A background_tasks.app beat --loglevel=info"]