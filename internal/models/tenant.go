package models

import (
	"time"

	"github.com/google/uuid"
)

// Tenant 表示系统中的租户
type Tenant struct {
	ID        uuid.UUID `json:"id"`
	Name      string    `json:"name"`
	Schema    string    `json:"schema"` // 数据库模式名称，用于租户隔离
	Active    bool      `json:"active"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

// TenantService 定义租户相关操作的接口
type TenantService interface {
	CreateTenant(name string) (*Tenant, error)
	GetTenantByID(id uuid.UUID) (*Tenant, error)
	GetTenantByName(name string) (*Tenant, error)
	ListTenants() ([]*Tenant, error)
	UpdateTenant(tenant *Tenant) error
	DeactivateTenant(id uuid.UUID) error
	ActivateTenant(id uuid.UUID) error
}

// TenantRepository 定义租户数据访问的接口
type TenantRepository interface {
	Create(tenant *Tenant) error
	GetByID(id uuid.UUID) (*Tenant, error)
	GetByName(name string) (*Tenant, error)
	List() ([]*Tenant, error)
	Update(tenant *Tenant) error
}