# SaaS多租户系统 - Makefile

.PHONY: build run test clean docker-build docker-up docker-down init-db

# 构建应用
build:
	go build -o bin/saas-server cmd/server/main.go

# 运行应用
run:
	go run cmd/server/main.go

# 运行测试
test:
	go test ./...

# 清理构建文件
clean:
	rm -rf bin/

# Docker构建
docker-build:
	docker build -t saas-multitenant .

# Docker启动
docker-up:
	docker-compose up -d

# Docker停止
docker-down:
	docker-compose down

# 初始化数据库
init-db:
	psql -d saas -f scripts/init_db.sql

# 数据库迁移
migrate:
	go run cmd/migrate/main.go

# 安装依赖
deps:
	go mod download
	go mod tidy

# 格式化代码
fmt:
	go fmt ./...

# 运行代码检查
lint:
	golangci-lint run

# 启动开发服务器（带热重载）
dev:
	air

# 查看日志
logs:
	docker-compose logs -f

# 进入数据库
psql:
	psql -d saas

# 备份数据库
backup:
	pg_dump saas > backup_$(shell date +%Y%m%d_%H%M%S).sql

# 恢复数据库
restore:
	psql -d saas < $(file)

# 帮助信息
help:
	@echo "SaaS多租户系统 - 可用命令:"
	@echo "  make build      - 构建应用"
	@echo "  make run        - 运行应用"
	@echo "  make test       - 运行测试"
	@echo "  make clean      - 清理构建文件"
	@echo "  make docker-up  - Docker启动"
	@echo "  make docker-down - Docker停止"
	@echo "  make init-db    - 初始化数据库"
	@echo "  make deps       - 安装依赖"
	@echo "  make help       - 显示帮助信息"