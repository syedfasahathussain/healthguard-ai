# 1. Base Operating System with Python 3.11
FROM python:3.11-slim

# 2. Container ke andar 'app' naam ka working folder banaya
WORKDIR /app

# 3. Environment Variables (Python logs directly terminal par dikhane ke liye)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. Dependencies copy kiye aur install kiye
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Project ka Saara Code aur ML Model (.pkl) container mein copy kiya
COPY . .

# 6. Port 8000 Open Kiya
EXPOSE 8000

# 7. Production Start Command!
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]