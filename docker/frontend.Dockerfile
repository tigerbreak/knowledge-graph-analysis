# 构建阶段
FROM node:latest as build-stage

# 设置工作目录
WORKDIR /app

# 复制 package.json 和 package-lock.json
COPY package*.json ./

# 安装依赖
RUN npm install

# 复制源代码
COPY . .

# 构建应用
RUN npm run build

# 生产阶段
FROM nginx:alpine as production-stage

# 复制构建产物到 Nginx 目录
COPY --from=build-stage /app/dist /usr/share/nginx/html

# 暴露 80 端口
EXPOSE 80

# 启动 Nginx
CMD ["nginx", "-g", "daemon off;"] 