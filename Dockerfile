# 使用官方Go镜像作为构建环境
FROM golang:1.21-alpine AS builder

# 设置工作目录
WORKDIR /app

# 安装依赖
RUN apk add --no-cache git

# 复制go mod文件
COPY go.mod go.sum ./
RUN go mod download

# 复制源代码
COPY . .

# 构建应用
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main cmd/server/main.go

# 使用Alpine作为运行环境
FROM alpine:latest

# 安装必要的包
RUN apk --no-cache add ca-certificates

# 设置工作目录
WORKDIR /root/

# 复制二进制文件
COPY --from=builder /app/main .

# 复制前端文件
COPY --from=builder /app/web ./web

# 暴露端口
EXPOSE 8080

# 运行应用
CMD ["./main"]