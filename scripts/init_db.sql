-- 初始化数据库脚本
-- 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS saas;

-- 使用saas数据库
\c saas;

-- 启用UUID扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 创建租户表
CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL UNIQUE,
    schema_name VARCHAR(255) NOT NULL UNIQUE,
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'user',
    active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, username),
    UNIQUE(tenant_id, email)
);

-- 创建权限表
CREATE TABLE IF NOT EXISTS permissions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, name)
);

-- 创建角色表
CREATE TABLE IF NOT EXISTS roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(tenant_id, name)
);

-- 创建角色权限关联表
CREATE TABLE IF NOT EXISTS role_permissions (
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

-- 创建用户角色关联表
CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- 创建API密钥表
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL,
    active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_permissions_tenant_id ON permissions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_roles_tenant_id ON roles(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_tenant_id ON api_keys(tenant_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_user_id ON api_keys(user_id);

-- 插入默认租户
INSERT INTO tenants (id, name, schema_name, active, created_at, updated_at) 
VALUES (uuid_generate_v4(), 'default', 'default_schema', true, NOW(), NOW())
ON CONFLICT (name) DO NOTHING;

-- 插入默认权限
INSERT INTO permissions (id, tenant_id, name, description, created_at, updated_at) 
VALUES 
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'users.read', '读取用户信息', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'users.write', '写入用户信息', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'users.delete', '删除用户', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'roles.read', '读取角色信息', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'roles.write', '写入角色信息', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'permissions.read', '读取权限信息', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'permissions.write', '写入权限信息', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'api_keys.read', '读取API密钥', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'api_keys.write', '写入API密钥', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- 插入默认角色
INSERT INTO roles (id, tenant_id, name, description, created_at, updated_at) 
VALUES 
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'admin', '系统管理员', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'user', '普通用户', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'vip', 'VIP用户', NOW(), NOW()),
    (uuid_generate_v4(), (SELECT id FROM tenants WHERE name = 'default'), 'enterprise', '企业客户', NOW(), NOW())
ON CONFLICT DO NOTHING;

-- 为管理员角色分配所有权限
INSERT INTO role_permissions (role_id, permission_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r, permissions p
WHERE r.name = 'admin' AND r.tenant_id = (SELECT id FROM tenants WHERE name = 'default')
ON CONFLICT DO NOTHING;

-- 为普通用户角色分配基本权限
INSERT INTO role_permissions (role_id, permission_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r, permissions p
WHERE r.name = 'user' AND r.tenant_id = (SELECT id FROM tenants WHERE name = 'default')
AND p.name IN ('users.read', 'api_keys.read', 'api_keys.write')
ON CONFLICT DO NOTHING;

-- 为VIP用户角色分配更多权限
INSERT INTO role_permissions (role_id, permission_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r, permissions p
WHERE r.name = 'vip' AND r.tenant_id = (SELECT id FROM tenants WHERE name = 'default')
AND p.name IN ('users.read', 'users.write', 'api_keys.read', 'api_keys.write')
ON CONFLICT DO NOTHING;

-- 为企业客户角色分配管理权限
INSERT INTO role_permissions (role_id, permission_id, created_at)
SELECT r.id, p.id, NOW()
FROM roles r, permissions p
WHERE r.name = 'enterprise' AND r.tenant_id = (SELECT id FROM tenants WHERE name = 'default')
AND p.name IN ('users.read', 'users.write', 'roles.read', 'permissions.read', 'api_keys.read', 'api_keys.write')
ON CONFLICT DO NOTHING;