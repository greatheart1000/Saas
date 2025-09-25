package service

import (
	"database/sql"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

// PermissionServiceImpl 实现权限服务接口
type PermissionServiceImpl struct {
	db         *sql.DB
	repository models.PermissionRepository
}

// NewPermissionService 创建新的权限服务实例
func NewPermissionService(db *sql.DB, repo models.PermissionRepository) models.PermissionService {
	return &PermissionServiceImpl{
		db:         db,
		repository: repo,
	}
}

// CreatePermission 创建新权限
func (s *PermissionServiceImpl) CreatePermission(tenantID uuid.UUID, name, description string) (*models.Permission, error) {
	// 检查权限名是否已存在
	existingPermission, err := s.repository.GetByName(tenantID, name)
	if err != nil && err != sql.ErrNoRows {
		return nil, fmt.Errorf("检查权限名时出错: %w", err)
	}
	if existingPermission != nil {
		return nil, fmt.Errorf("权限名 '%s' 已存在", name)
	}

	// 创建新权限
	permission := &models.Permission{
		ID:          uuid.New(),
		Name:        name,
		Description: description,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// 保存权限到数据库
	if err := s.repository.Create(tenantID, permission); err != nil {
		return nil, fmt.Errorf("创建权限时出错: %w", err)
	}

	return permission, nil
}

// GetPermissionByID 通过ID获取权限
func (s *PermissionServiceImpl) GetPermissionByID(tenantID, permissionID uuid.UUID) (*models.Permission, error) {
	return s.repository.GetByID(tenantID, permissionID)
}

// GetPermissionByName 通过名称获取权限
func (s *PermissionServiceImpl) GetPermissionByName(tenantID uuid.UUID, name string) (*models.Permission, error) {
	return s.repository.GetByName(tenantID, name)
}

// ListPermissions 列出所有权限
func (s *PermissionServiceImpl) ListPermissions(tenantID uuid.UUID) ([]*models.Permission, error) {
	return s.repository.List(tenantID)
}

// UpdatePermission 更新权限信息
func (s *PermissionServiceImpl) UpdatePermission(tenantID uuid.UUID, permission *models.Permission) error {
	permission.UpdatedAt = time.Now()
	return s.repository.Update(tenantID, permission)
}

// DeletePermission 删除权限
func (s *PermissionServiceImpl) DeletePermission(tenantID, permissionID uuid.UUID) error {
	return s.repository.Delete(tenantID, permissionID)
}

// RoleServiceImpl 实现角色服务接口
type RoleServiceImpl struct {
	db         *sql.DB
	repository models.RoleRepository
}

// NewRoleService 创建新的角色服务实例
func NewRoleService(db *sql.DB, repo models.RoleRepository) models.RoleService {
	return &RoleServiceImpl{
		db:         db,
		repository: repo,
	}
}

// CreateRole 创建新角色
func (s *RoleServiceImpl) CreateRole(tenantID uuid.UUID, name, description string) (*models.Role, error) {
	// 检查角色名是否已存在
	existingRole, err := s.repository.GetByName(tenantID, name)
	if err != nil && err != sql.ErrNoRows {
		return nil, fmt.Errorf("检查角色名时出错: %w", err)
	}
	if existingRole != nil {
		return nil, fmt.Errorf("角色名 '%s' 已存在", name)
	}

	// 创建新角色
	role := &models.Role{
		ID:          uuid.New(),
		Name:        name,
		Description: description,
		Permissions: []*models.Permission{},
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}

	// 保存角色到数据库
	if err := s.repository.Create(tenantID, role); err != nil {
		return nil, fmt.Errorf("创建角色时出错: %w", err)
	}

	return role, nil
}

// GetRoleByID 通过ID获取角色
func (s *RoleServiceImpl) GetRoleByID(tenantID, roleID uuid.UUID) (*models.Role, error) {
	return s.repository.GetByID(tenantID, roleID)
}

// GetRoleByName 通过名称获取角色
func (s *RoleServiceImpl) GetRoleByName(tenantID uuid.UUID, name string) (*models.Role, error) {
	return s.repository.GetByName(tenantID, name)
}

// ListRoles 列出所有角色
func (s *RoleServiceImpl) ListRoles(tenantID uuid.UUID) ([]*models.Role, error) {
	return s.repository.List(tenantID)
}

// UpdateRole 更新角色信息
func (s *RoleServiceImpl) UpdateRole(tenantID uuid.UUID, role *models.Role) error {
	role.UpdatedAt = time.Now()
	return s.repository.Update(tenantID, role)
}

// DeleteRole 删除角色
func (s *RoleServiceImpl) DeleteRole(tenantID, roleID uuid.UUID) error {
	return s.repository.Delete(tenantID, roleID)
}

// AddPermissionToRole 向角色添加权限
func (s *RoleServiceImpl) AddPermissionToRole(tenantID, roleID, permissionID uuid.UUID) error {
	return s.repository.AddPermission(tenantID, roleID, permissionID)
}

// RemovePermissionFromRole 从角色移除权限
func (s *RoleServiceImpl) RemovePermissionFromRole(tenantID, roleID, permissionID uuid.UUID) error {
	return s.repository.RemovePermission(tenantID, roleID, permissionID)
}

// GetRolePermissions 获取角色的所有权限
func (s *RoleServiceImpl) GetRolePermissions(tenantID, roleID uuid.UUID) ([]*models.Permission, error) {
	return s.repository.GetPermissions(tenantID, roleID)
}

// AssignRoleToUser 将角色分配给用户
func (s *RoleServiceImpl) AssignRoleToUser(tenantID, roleID, userID uuid.UUID) error {
	return s.repository.AssignToUser(tenantID, roleID, userID)
}

// RemoveRoleFromUser 从用户移除角色
func (s *RoleServiceImpl) RemoveRoleFromUser(tenantID, roleID, userID uuid.UUID) error {
	return s.repository.RemoveFromUser(tenantID, roleID, userID)
}

// GetUserRoles 获取用户的所有角色
func (s *RoleServiceImpl) GetUserRoles(tenantID, userID uuid.UUID) ([]*models.Role, error) {
	return s.repository.GetUserRoles(tenantID, userID)
}

// HasPermission 检查用户是否拥有指定权限
func (s *RoleServiceImpl) HasPermission(tenantID, userID uuid.UUID, permissionName string) (bool, error) {
	return s.repository.CheckUserPermission(tenantID, userID, permissionName)
}