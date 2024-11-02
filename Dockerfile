# Build stage
FROM node:14 as build-stage
WORKDIR /app

# 패키지 파일만 먼저 복사
COPY package*.json ./
RUN npm install

# 필요한 파일들만 복사
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY index.html ./
COPY src/ src/
COPY public/ public/

# 빌드
RUN npm run build

# Production stage
FROM nginx:stable-alpine as production-stage

# nginx 설정 파일 생성
RUN mkdir -p /etc/nginx/conf.d
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 빌드된 파일 복사
COPY --from=build-stage /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]