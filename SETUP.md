# SaaS多租户系统 - 完整设置指南

## 🚀 系统概述

这是一个功能完整的SaaS多租户系统，包含以下核心功能：

- ✅ **多租户隔离** - 基于数据库模式隔离的租户系统
- ✅ **用户认证** - JWT基于令牌的身份验证
- ✅ **用户分级** - 普通用户、VIP用户、企业客户、管理员
- ✅ **RBAC权限系统** - 基于角色的访问控制
- ✅ **前端界面** - 现代化的响应式Web界面
- ✅ **API管理** - RESTful API和API密钥管理

## 📋 技术栈

- **后端**: Go 1.21+ with Gin框架
- **数据库**: PostgreSQL 12+
- **认证**: JWT (JSON Web Tokens)
- **前端**: HTML5, CSS3, JavaScript (Bootstrap 5)
- **容器化**: Docker & Docker Compose

## 🔧 环境要求

- Go 1.21 或更高版本
- PostgreSQL 12 或更高版本
- Docker 和 Docker Compose (可选)
- Git

## 🏃‍♂️ 快速开始

### 方法1: 使用Docker (推荐)

1. **克隆项目**
```bash
git clone https://github.com/yourusername/saas-multitenant.git
cd saas-multitenant
```

2. **启动服务**
```bash
docker-compose up -d
```

3. **访问系统**
- Web界面: http://localhost:8080
- API文档: http://localhost:8080/swagger/index.html

### 方法2: 本地开发

1. **安装依赖**
```bash
go mod download
```

2. **设置数据库**
```bash
# 创建数据库
createdb saas

# 运行初始化脚本
psql -d saas -f scripts/init_db.sql
```

3. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，设置数据库连接信息
```

4. **运行应用**
```bash
go run cmd/server/main.go
```

## 📁 项目结构

```
saas-multitenant/
├── cmd/server/           # 应用入口
├── internal/             # 内部包
│   ├── api/             # API处理器
│   ├── config/          # 配置管理
│   ├── middleware/      # 中间件
│   ├── models/          # 数据模型
│   ├── repository/      # 数据访问层
│   └── service/         # 业务逻辑层
├── pkg/                  # 可重用包
│   ├── database/        # 数据库工具
│   └── jwt/             # JWT工具
├── web/                  # 前端文件
│   ├── templates/       # HTML模板
│   └── static/          # 静态文件
├── scripts/              # 脚本文件
├── docker-compose.yml    # Docker配置
├── Dockerfile           # 容器镜像
└── .env                 # 环境变量
```

## 🔐 用户角色和权限

### 用户类型
- **普通用户 (user)**: 基本功能访问
- **VIP用户 (vip)**: 高级功能和优先支持
- **企业客户 (enterprise)**: 完整功能和专属服务
- **管理员 (admin)**: 系统管理权限

### 默认权限
- **users.read**: 读取用户信息
- **users.write**: 写入用户信息
- **users.delete**: 删除用户
- **roles.read**: 读取角色信息
- **roles.write**: 写入角色信息
- **permissions.read**: 读取权限信息
- **permissions.write**: 写入权限信息
- **api_keys.read**: 读取API密钥
- **api_keys.write**: 写入API密钥

## 🔌 API接口

### 认证接口
- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `POST /api/v1/auth/refresh` - 刷新令牌
- `POST /api/v1/auth/change-password` - 修改密码

### 用户管理
- `GET /api/v1/users` - 获取用户列表
- `GET /api/v1/users/:id` - 获取用户信息
- `PUT /api/v1/users/:id` - 更新用户信息
- `DELETE /api/v1/users/:id` - 删除用户

### 角色管理
- `GET /api/v1/roles` - 获取角色列表
- `POST /api/v1/roles` - 创建角色
- `PUT /api/v1/roles/:id` - 更新角色
- `DELETE /api/v1/roles/:id` - 删除角色
- `POST /api/v1/roles/:id/permissions` - 分配权限

### 权限管理
- `GET /api/v1/permissions` - 获取权限列表
- `POST /api/v1/permissions` - 创建权限
- `PUT /api/v1/permissions/:id` - 更新权限
- `DELETE /api/v1/permissions/:id` - 删除权限

## 🌐 前端页面

- **首页** `/` - 系统介绍和功能展示
- **登录页** `/login` - 用户登录
- **注册页** `/register` - 用户注册
- **控制台** `/dashboard` - 用户控制台

## ⚙️ 环境变量配置

```bash
# 数据库配置
DATABASE_URL=postgres://localhost/saas?sslmode=disable

# JWT配置
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production
JWT_EXPIRATION=24h

# 服务器配置
PORT=8080
ENVIRONMENT=development
```

## 🔒 安全建议

1. **生产环境**请使用强密码和HTTPS
2. **JWT密钥**请使用足够长的随机字符串
3. **数据库**请设置适当的访问权限
4. **定期更新**依赖包以修复安全漏洞

## 🧪 测试用户

系统初始化后会创建以下测试用户：

| 用户名 | 邮箱 | 密码 | 角色 |
|--------|------|------|------|
| admin | admin@example.com | admin123 | admin |
| user | user@example.com | user123 | user |
| vip | vip@example.com | vip123 | vip |
| enterprise | enterprise@example.com | enterprise123 | enterprise |

## 🐛 常见问题

### 数据库连接失败
确保PostgreSQL正在运行，并且数据库已创建：
```bash
createdb saas
```

### 端口被占用
修改`.env`文件中的`PORT`变量，或使用其他端口：
```bash
PORT=3000 go run cmd/server/main.go
```

### 前端静态文件未找到
确保在正确的目录下运行应用：
```bash
cd /path/to/saas-multitenant
go run cmd/server/main.go
```

## 📞 支持

如有问题或建议，请提交Issue或Pull Request。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件