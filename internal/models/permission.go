package models

import (
	"time"

	"github.com/google/uuid"
)

// Permission 表示系统中的权限
type Permission struct {
	ID          uuid.UUID `json:"id"`
	Name        string    `json:"name"`
	Description string    `json:"description"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// Role 表示系统中的角色
type Role struct {
	ID          uuid.UUID     `json:"id"`
	Name        string        `json:"name"`
	Description string        `json:"description"`
	Permissions []*Permission `json:"permissions,omitempty"`
	CreatedAt   time.Time     `json:"created_at"`
	UpdatedAt   time.Time     `json:"updated_at"`
}

// PermissionService 定义权限相关操作的接口
type PermissionService interface {
	CreatePermission(tenantID uuid.UUID, name, description string) (*Permission, error)
	GetPermissionByID(tenantID, permissionID uuid.UUID) (*Permission, error)
	GetPermissionByName(tenantID uuid.UUID, name string) (*Permission, error)
	ListPermissions(tenantID uuid.UUID) ([]*Permission, error)
	UpdatePermission(tenantID uuid.UUID, permission *Permission) error
	DeletePermission(tenantID, permissionID uuid.UUID) error
}

// RoleService 定义角色相关操作的接口
type RoleService interface {
	CreateRole(tenantID uuid.UUID, name, description string) (*Role, error)
	GetRoleByID(tenantID, roleID uuid.UUID) (*Role, error)
	GetRoleByName(tenantID uuid.UUID, name string) (*Role, error)
	ListRoles(tenantID uuid.UUID) ([]*Role, error)
	UpdateRole(tenantID uuid.UUID, role *Role) error
	DeleteRole(tenantID, roleID uuid.UUID) error
	AddPermissionToRole(tenantID, roleID, permissionID uuid.UUID) error
	RemovePermissionFromRole(tenantID, roleID, permissionID uuid.UUID) error
	GetRolePermissions(tenantID, roleID uuid.UUID) ([]*Permission, error)
	AssignRoleToUser(tenantID, roleID, userID uuid.UUID) error
	RemoveRoleFromUser(tenantID, roleID, userID uuid.UUID) error
	GetUserRoles(tenantID, userID uuid.UUID) ([]*Role, error)
	HasPermission(tenantID, userID uuid.UUID, permissionName string) (bool, error)
}

// PermissionRepository 定义权限数据访问的接口
type PermissionRepository interface {
	Create(tenantID uuid.UUID, permission *Permission) error
	GetByID(tenantID, permissionID uuid.UUID) (*Permission, error)
	GetByName(tenantID uuid.UUID, name string) (*Permission, error)
	List(tenantID uuid.UUID) ([]*Permission, error)
	Update(tenantID uuid.UUID, permission *Permission) error
	Delete(tenantID, permissionID uuid.UUID) error
}

// RoleRepository 定义角色数据访问的接口
type RoleRepository interface {
	Create(tenantID uuid.UUID, role *Role) error
	GetByID(tenantID, roleID uuid.UUID) (*Role, error)
	GetByName(tenantID uuid.UUID, name string) (*Role, error)
	List(tenantID uuid.UUID) ([]*Role, error)
	Update(tenantID uuid.UUID, role *Role) error
	Delete(tenantID, roleID uuid.UUID) error
	AddPermission(tenantID, roleID, permissionID uuid.UUID) error
	RemovePermission(tenantID, roleID, permissionID uuid.UUID) error
	GetPermissions(tenantID, roleID uuid.UUID) ([]*Permission, error)
	AssignToUser(tenantID, roleID, userID uuid.UUID) error
	RemoveFromUser(tenantID, roleID, userID uuid.UUID) error
	GetUserRoles(tenantID, userID uuid.UUID) ([]*Role, error)
	CheckUserPermission(tenantID, userID uuid.UUID, permissionName string) (bool, error)
}