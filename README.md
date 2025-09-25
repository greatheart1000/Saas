# SaaS多租户系统

这是一个基于Go的SaaS多租户系统，提供租户隔离、API密钥生成、JWT认证和基于角色的权限控制功能。

## 功能特性

- 多租户隔离：使用数据库模式隔离确保租户数据安全
- 用户认证：基于JWT的认证系统
- API密钥管理：生成和验证API密钥
- 权限控制：基于角色的访问控制系统

## 项目结构

```
├── cmd/                # 应用程序入口
│   └── server/         # 服务器启动代码
├── internal/           # 内部包
│   ├── api/            # API处理器
│   ├── auth/           # 认证相关代码
│   ├── config/         # 配置相关代码
│   ├── middleware/     # 中间件
│   ├── models/         # 数据模型
│   └── service/        # 业务逻辑
├── pkg/                # 可重用的包
│   ├── apikey/         # API密钥工具
│   ├── jwt/            # JWT工具
│   └── tenant/         # 租户工具
├── scripts/            # 脚本文件
└── configs/            # 配置文件
```

## 安装和使用

### 前提条件

- Go 1.16+
- PostgreSQL 12+

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/saas-multitenant.git
cd saas-multitenant

# 安装依赖
go mod download

# 构建应用
go build -o saas-server ./cmd/server
```

### 配置

编辑 `configs/config.yaml` 文件以配置数据库连接和其他设置。

### 运行

```bash
./saas-server
```

## API文档

启动服务器后，可以在 `http://localhost:8080/swagger/index.html` 访问API文档。

## 许可证

MIT# Saas
