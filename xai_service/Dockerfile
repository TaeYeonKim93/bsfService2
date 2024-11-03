FROM python:3.11-slim

WORKDIR /app

# 한글 폰트 및 fontconfig 패키지 설치
RUN apt-get update && apt-get install -y \
    fontconfig \
    fonts-nanum \
    fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

# 폰트 캐시 업데이트
RUN fc-cache -fv

# requirements.txt 파일 복사 및 패키지 설치
COPY requirements.txt .
RUN pip install -r requirements.txt

# 애플리케이션 파일 복사
COPY app.py .
COPY data/ data/

EXPOSE 5001

CMD ["python", "app.py"]