FROM python:3.11-slim

WORKDIR /app

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# requirements.txt 파일만 먼저 복사
COPY requirements.txt .

# 캐시를 활용하고 필요한 패키지만 설치
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 애플리케이션 파일 복사
COPY main.py .
COPY .env .
COPY .streamlit .streamlit/
COPY data /app/data/

EXPOSE 5000

CMD ["streamlit", "run", "main.py"]