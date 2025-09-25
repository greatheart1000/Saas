package database

import (
	"database/sql"
	"fmt"

	_ "github.com/lib/pq"
)

func Initialize(databaseURL string) (*sql.DB, error) {
	db, err := sql.Open("postgres", databaseURL)
	if err != nil {
		return nil, fmt.Errorf("无法连接到数据库: %v", err)
	}

	if err := db.Ping(); err != nil {
		return nil, fmt.Errorf("数据库连接测试失败: %v", err)
	}

	return db, nil
}

func Migrate(db *sql.DB) error {
	// 创建租户表
	if err := createTenantsTable(db); err != nil {
		return fmt.Errorf("创建租户表失败: %v", err)
	}

	// 创建用户表
	if err := createUsersTable(db); err != nil {
		return fmt.Errorf("创建用户表失败: %v", err)
	}

	// 创建权限表
	if err := createPermissionsTable(db); err != nil {
		return fmt.Errorf("创建权限表失败: %v", err)
	}

	// 创建角色表
	if err := createRolesTable(db); err != nil {
		return fmt.Errorf("创建角色表失败: %v", err)
	}

	// 创建角色权限关联表
	if err := createRolePermissionsTable(db); err != nil {
		return fmt.Errorf("创建角色权限关联表失败: %v", err)
	}

	// 创建用户角色关联表
	if err := createUserRolesTable(db); err != nil {
		return fmt.Errorf("创建用户角色关联表失败: %v", err)
	}

	// 创建API密钥表
	if err := createAPIKeysTable(db); err != nil {
		return fmt.Errorf("创建API密钥表失败: %v", err)
	}

	return nil
}

func createTenantsTable(db *sql.DB) error {
	query := `
	CREATE TABLE IF NOT EXISTS tenants (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		name VARCHAR(255) NOT NULL UNIQUE,
		schema_name VARCHAR(255) NOT NULL UNIQUE,
		active BOOLEAN DEFAULT true,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);
	`
	_, err := db.Exec(query)
	return err
}

func createUsersTable(db *sql.DB) error {
	query := `
	CREATE TABLE IF NOT EXISTS users (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
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
	`
	_, err := db.Exec(query)
	return err
}

func createPermissionsTable(db *sql.DB) error {
	query := `
	CREATE TABLE IF NOT EXISTS permissions (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
		name VARCHAR(255) NOT NULL,
		description TEXT,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		UNIQUE(tenant_id, name)
	);
	`
	_, err := db.Exec(query)
	return err
}

func createRolesTable(db *sql.DB) error {
	query := `
	CREATE TABLE IF NOT EXISTS roles (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
		name VARCHAR(255) NOT NULL,
		description TEXT,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		UNIQUE(tenant_id, name)
	);
	`
	_, err := db.Exec(query)
	return err
}

func createRolePermissionsTable(db *sql.DB) error {
	query := `
	CREATE TABLE IF NOT EXISTS role_permissions (
		role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
		permission_id UUID NOT NULL REFERENCES permissions(id) ON DELETE CASCADE,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		PRIMARY KEY (role_id, permission_id)
	);
	`
	_, err := db.Exec(query)
	return err
}

func createUserRolesTable(db *sql.DB) error {
	query := `
	CREATE TABLE IF NOT EXISTS user_roles (
		user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
		role_id UUID NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		PRIMARY KEY (user_id, role_id)
	);
	`
	_, err := db.Exec(query)
	return err
}

func createAPIKeysTable(db *sql.DB) error {
	query := `
	CREATE TABLE IF NOT EXISTS api_keys (
		id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
		tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
		user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
		key_hash VARCHAR(255) NOT NULL UNIQUE,
		name VARCHAR(255) NOT NULL,
		active BOOLEAN DEFAULT true,
		expires_at TIMESTAMP,
		created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
		updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
	);
	`
	_, err := db.Exec(query)
	return err
}