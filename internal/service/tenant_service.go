package service

import (
	"database/sql"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

// TenantServiceImpl 实现租户服务接口
type TenantServiceImpl struct {
	db         *sql.DB
	repository models.TenantRepository
}

// NewTenantService 创建新的租户服务实例
func NewTenantService(db *sql.DB, repo models.TenantRepository) models.TenantService {
	return &TenantServiceImpl{
		db:         db,
		repository: repo,
	}
}

// CreateTenant 创建新租户并初始化其数据库模式
func (s *TenantServiceImpl) CreateTenant(name string) (*models.Tenant, error) {
	// 检查租户名是否已存在
	existingTenant, err := s.repository.GetByName(name)
	if err != nil && err != sql.ErrNoRows {
		return nil, fmt.Errorf("检查租户名时出错: %w", err)
	}
	if existingTenant != nil {
		return nil, fmt.Errorf("租户名 '%s' 已存在", name)
	}

	// 创建新租户
	tenantID := uuid.New()
	schemaName := fmt.Sprintf("tenant_%s", tenantID.String()[:8])
	tenant := &models.Tenant{
		ID:        tenantID,
		Name:      name,
		Schema:    schemaName,
		Active:    true,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	// 开始事务
	tx, err := s.db.Begin()
	if err != nil {
		return nil, fmt.Errorf("开始事务时出错: %w", err)
	}
	defer func() {
		if err != nil {
			tx.Rollback()
		}
	}()

	// 创建租户记录
	if err = s.repository.Create(tenant); err != nil {
		return nil, fmt.Errorf("创建租户记录时出错: %w", err)
	}

	// 创建租户的数据库模式
	_, err = tx.Exec(fmt.Sprintf("CREATE SCHEMA IF NOT EXISTS %s", schemaName))
	if err != nil {
		return nil, fmt.Errorf("创建数据库模式时出错: %w", err)
	}

	// 初始化租户的表结构
	err = s.initTenantSchema(tx, schemaName)
	if err != nil {
		return nil, fmt.Errorf("初始化租户模式时出错: %w", err)
	}

	// 提交事务
	if err = tx.Commit(); err != nil {
		return nil, fmt.Errorf("提交事务时出错: %w", err)
	}

	return tenant, nil
}

// GetTenantByID 通过ID获取租户
func (s *TenantServiceImpl) GetTenantByID(id uuid.UUID) (*models.Tenant, error) {
	return s.repository.GetByID(id)
}

// GetTenantByName 通过名称获取租户
func (s *TenantServiceImpl) GetTenantByName(name string) (*models.Tenant, error) {
	return s.repository.GetByName(name)
}

// ListTenants 列出所有租户
func (s *TenantServiceImpl) ListTenants() ([]*models.Tenant, error) {
	return s.repository.List()
}

// UpdateTenant 更新租户信息
func (s *TenantServiceImpl) UpdateTenant(tenant *models.Tenant) error {
	tenant.UpdatedAt = time.Now()
	return s.repository.Update(tenant)
}

// DeactivateTenant 停用租户
func (s *TenantServiceImpl) DeactivateTenant(id uuid.UUID) error {
	tenant, err := s.repository.GetByID(id)
	if err != nil {
		return err
	}
	tenant.Active = false
	tenant.UpdatedAt = time.Now()
	return s.repository.Update(tenant)
}

// ActivateTenant 激活租户
func (s *TenantServiceImpl) ActivateTenant(id uuid.UUID) error {
	tenant, err := s.repository.GetByID(id)
	if err != nil {
		return err
	}
	tenant.Active = true
	tenant.UpdatedAt = time.Now()
	return s.repository.Update(tenant)
}

// initTenantSchema 初始化租户的数据库模式，创建必要的表
func (s *TenantServiceImpl) initTenantSchema(tx *sql.Tx, schema string) error {
	// 创建用户表
	_, err := tx.Exec(fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.users (
			id UUID PRIMARY KEY,
			username VARCHAR(50) UNIQUE NOT NULL,
			email VARCHAR(100) UNIQUE NOT NULL,
			password_hash VARCHAR(100) NOT NULL,
			role VARCHAR(20) NOT NULL,
			active BOOLEAN NOT NULL DEFAULT TRUE,
			created_at TIMESTAMP NOT NULL,
			updated_at TIMESTAMP NOT NULL
		)
	`, schema))
	if err != nil {
		return err
	}

	// 创建API密钥表
	_, err = tx.Exec(fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.api_keys (
			id UUID PRIMARY KEY,
			user_id UUID NOT NULL REFERENCES %s.users(id) ON DELETE CASCADE,
			api_key VARCHAR(64) UNIQUE NOT NULL,
			description VARCHAR(200),
			expires_at TIMESTAMP,
			active BOOLEAN NOT NULL DEFAULT TRUE,
			created_at TIMESTAMP NOT NULL,
			updated_at TIMESTAMP NOT NULL
		)
	`, schema, schema))
	if err != nil {
		return err
	}

	// 创建权限表
	_, err = tx.Exec(fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.permissions (
			id UUID PRIMARY KEY,
			name VARCHAR(50) UNIQUE NOT NULL,
			description VARCHAR(200),
			created_at TIMESTAMP NOT NULL,
			updated_at TIMESTAMP NOT NULL
		)
	`, schema))
	if err != nil {
		return err
	}

	// 创建角色表
	_, err = tx.Exec(fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.roles (
			id UUID PRIMARY KEY,
			name VARCHAR(50) UNIQUE NOT NULL,
			description VARCHAR(200),
			created_at TIMESTAMP NOT NULL,
			updated_at TIMESTAMP NOT NULL
		)
	`, schema))
	if err != nil {
		return err
	}

	// 创建角色权限关联表
	_, err = tx.Exec(fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.role_permissions (
			role_id UUID NOT NULL REFERENCES %s.roles(id) ON DELETE CASCADE,
			permission_id UUID NOT NULL REFERENCES %s.permissions(id) ON DELETE CASCADE,
			PRIMARY KEY (role_id, permission_id)
		)
	`, schema, schema, schema))
	if err != nil {
		return err
	}

	// 创建用户角色关联表
	_, err = tx.Exec(fmt.Sprintf(`
		CREATE TABLE IF NOT EXISTS %s.user_roles (
			user_id UUID NOT NULL REFERENCES %s.users(id) ON DELETE CASCADE,
			role_id UUID NOT NULL REFERENCES %s.roles(id) ON DELETE CASCADE,
			PRIMARY KEY (user_id, role_id)
		)
	`, schema, schema, schema))

	return err
}