# SaaS多租户系统API文档

本文档详细说明了SaaS多租户系统提供的所有API接口，包括租户管理、用户认证、API密钥管理和权限控制等功能。

## 基础信息

- 基础URL: `https://api.yourdomain.com` 或 `https://{tenant-name}.yourdomain.com`
- 所有请求和响应均使用JSON格式
- 认证方式：JWT令牌或API密钥

## 认证方式

### JWT认证

大多数API请求需要在请求头中包含JWT访问令牌：

```
Authorization: Bearer {access_token}
```

### API密钥认证

某些API请求可以使用API密钥进行认证：

```
X-API-Key: {api_key}
```

### 租户标识

所有请求都需要指定租户标识，可以通过以下方式之一提供：

1. 请求头：`X-Tenant: {tenant_name}`
2. 子域名：`{tenant_name}.yourdomain.com`

## 租户管理API

### 创建租户

```
POST /api/v1/tenants
```

请求体：

```json
{
  "name": "tenant-name"
}
```

响应：

```json
{
  "id": "uuid",
  "name": "tenant-name",
  "schema": "tenant_12345678",
  "active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### 获取租户信息

```
GET /api/v1/tenants/{id}
```

响应：

```json
{
  "id": "uuid",
  "name": "tenant-name",
  "schema": "tenant_12345678",
  "active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### 列出所有租户

```
GET /api/v1/tenants
```

响应：

```json
[
  {
    "id": "uuid",
    "name": "tenant-name-1",
    "schema": "tenant_12345678",
    "active": true,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  },
  {
    "id": "uuid",
    "name": "tenant-name-2",
    "schema": "tenant_87654321",
    "active": true,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
]
```

### 停用租户

```
POST /api/v1/tenants/{id}/deactivate
```

响应：

```json
{
  "message": "租户已停用"
}
```

### 激活租户

```
POST /api/v1/tenants/{id}/activate
```

响应：

```json
{
  "message": "租户已激活"
}
```

## 用户认证API

### 注册用户

```
POST /api/v1/auth/register
```

请求体：

```json
{
  "username": "user123",
  "email": "user@example.com",
  "password": "password123"
}
```

响应：

```json
{
  "id": "uuid",
  "username": "user123",
  "email": "user@example.com",
  "role": "user",
  "active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### 用户登录

```
POST /api/v1/auth/login
```

请求体：

```json
{
  "username_or_email": "user123",
  "password": "password123"
}
```

响应：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2023-01-01T01:00:00Z",
  "user": {
    "id": "uuid",
    "username": "user123",
    "email": "user@example.com",
    "role": "user",
    "active": true,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
}
```

### 刷新令牌

```
POST /api/v1/auth/refresh
```

请求体：

```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

响应：

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": "2023-01-01T02:00:00Z"
}
```

### 修改密码

```
POST /api/v1/auth/change-password
```

请求体：

```json
{
  "current_password": "password123",
  "new_password": "newpassword123"
}
```

响应：

```json
{
  "message": "密码修改成功"
}
```

## API密钥管理API

### 生成API密钥

```
POST /api/v1/apikeys
```

请求体：

```json
{
  "description": "用于测试的API密钥",
  "expiry_days": 30
}
```

响应：

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "key": "ak_1234567890abcdef1234567890abcdef",
  "description": "用于测试的API密钥",
  "expires_at": "2023-02-01T00:00:00Z",
  "active": true,
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### 列出API密钥

```
GET /api/v1/apikeys
```

响应：

```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "key": "ak_1234567890abcdef1234567890abcdef",
    "description": "用于测试的API密钥",
    "expires_at": "2023-02-01T00:00:00Z",
    "active": true,
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-01-01T00:00:00Z"
  }
]
```

### 停用API密钥

```
POST /api/v1/apikeys/{id}/deactivate
```

响应：

```json
{
  "message": "API密钥已停用"
}
```

### 激活API密钥

```
POST /api/v1/apikeys/{id}/activate
```

响应：

```json
{
  "message": "API密钥已激活"
}
```

### 删除API密钥

```
DELETE /api/v1/apikeys/{id}
```

响应：

```json
{
  "message": "API密钥已删除"
}
```

## 权限管理API

### 创建权限

```
POST /api/v1/permissions
```

请求体：

```json
{
  "name": "read:users",
  "description": "允许读取用户信息"
}
```

响应：

```json
{
  "id": "uuid",
  "name": "read:users",
  "description": "允许读取用户信息",
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### 创建角色

```
POST /api/v1/roles
```

请求体：

```json
{
  "name": "editor",
  "description": "编辑者角色"
}
```

响应：

```json
{
  "id": "uuid",
  "name": "editor",
  "description": "编辑者角色",
  "permissions": [],
  "created_at": "2023-01-01T00:00:00Z",
  "updated_at": "2023-01-01T00:00:00Z"
}
```

### 向角色添加权限

```
POST /api/v1/roles/{role_id}/permissions
```

请求体：

```json
{
  "permission_id": "uuid"
}
```

响应：

```json
{
  "message": "权限已添加到角色"
}
```

### 将角色分配给用户

```
POST /api/v1/users/{user_id}/roles
```

请求体：

```json
{
  "role_id": "uuid"
}
```

响应：

```json
{
  "message": "角色已分配给用户"
}
```

### 检查用户权限

```
GET /api/v1/users/{user_id}/permissions/check?permission=read:users
```

响应：

```json
{
  "has_permission": true
}
```

## 错误响应

所有API错误响应都遵循以下格式：

```json
{
  "error": "错误消息描述"
}
```

常见HTTP状态码：

- 200 OK - 请求成功
- 201 Created - 资源创建成功
- 400 Bad Request - 请求参数无效
- 401 Unauthorized - 未提供认证或认证无效
- 403 Forbidden - 权限不足
- 404 Not Found - 资源不存在
- 500 Internal Server Error - 服务器内部错误

## 示例使用流程

### 1. 创建租户

```
POST /api/v1/tenants
```

请求体：
```json
{
  "name": "acme-corp"
}
```

### 2. 注册用户

```
POST /api/v1/auth/register
X-Tenant: acme-corp
```

请求体：
```json
{
  "username": "admin",
  "email": "admin@acme-corp.com",
  "password": "securepassword"
}
```

### 3. 用户登录

```
POST /api/v1/auth/login
X-Tenant: acme-corp
```

请求体：
```json
{
  "username_or_email": "admin",
  "password": "securepassword"
}
```

### 4. 使用JWT令牌访问API

```
GET /api/v1/users
X-Tenant: acme-corp
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 5. 生成API密钥

```
POST /api/v1/apikeys
X-Tenant: acme-corp
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

请求体：
```json
{
  "description": "服务器集成",
  "expiry_days": 90
}
```

### 6. 使用API密钥访问API

```
GET /api/v1/users
X-Tenant: acme-corp
X-API-Key: ak_1234567890abcdef1234567890abcdef
```