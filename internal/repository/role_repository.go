package repository

import (
	"database/sql"
	"fmt"

	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

type RoleRepository struct {
	db *sql.DB
}

func NewRoleRepository(db *sql.DB) *RoleRepository {
	return &RoleRepository{db: db}
}

func (r *RoleRepository) Create(tenantID uuid.UUID, role *models.Role) error {
	query := `
		INSERT INTO roles (id, tenant_id, name, description, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6)
	`
	_, err := r.db.Exec(query, role.ID, tenantID, role.Name, role.Description, role.CreatedAt, role.UpdatedAt)
	return err
}

func (r *RoleRepository) GetByID(tenantID, roleID uuid.UUID) (*models.Role, error) {
	query := `
		SELECT id, name, description, created_at, updated_at
		FROM roles
		WHERE id = $1 AND tenant_id = $2
	`
	
	role := &models.Role{}
	err := r.db.QueryRow(query, roleID, tenantID).Scan(
		&role.ID, &role.Name, &role.Description, &role.CreatedAt, &role.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("角色不存在")
	}
	if err != nil {
		return nil, err
	}

	return role, nil
}

func (r *RoleRepository) GetByName(tenantID uuid.UUID, name string) (*models.Role, error) {
	query := `
		SELECT id, name, description, created_at, updated_at
		FROM roles
		WHERE name = $1 AND tenant_id = $2
	`
	
	role := &models.Role{}
	err := r.db.QueryRow(query, name, tenantID).Scan(
		&role.ID, &role.Name, &role.Description, &role.CreatedAt, &role.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("角色不存在")
	}
	if err != nil {
		return nil, err
	}

	return role, nil
}

func (r *RoleRepository) List(tenantID uuid.UUID) ([]*models.Role, error) {
	query := `
		SELECT id, name, description, created_at, updated_at
		FROM roles
		WHERE tenant_id = $1
		ORDER BY created_at DESC
	`
	
	rows, err := r.db.Query(query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var roles []*models.Role
	for rows.Next() {
		role := &models.Role{}
		err := rows.Scan(
			&role.ID, &role.Name, &role.Description, &role.CreatedAt, &role.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		roles = append(roles, role)
	}

	return roles, nil
}

func (r *RoleRepository) Update(tenantID uuid.UUID, role *models.Role) error {
	query := `
		UPDATE roles
		SET name = $3, description = $4, updated_at = $5
		WHERE id = $1 AND tenant_id = $2
	`
	
	_, err := r.db.Exec(query, role.ID, tenantID, role.Name, role.Description, role.UpdatedAt)
	return err
}

func (r *RoleRepository) Delete(tenantID, roleID uuid.UUID) error {
	query := `DELETE FROM roles WHERE id = $1 AND tenant_id = $2`
	_, err := r.db.Exec(query, roleID, tenantID)
	return err
}

func (r *RoleRepository) AddPermission(tenantID, roleID, permissionID uuid.UUID) error {
	query := `
		INSERT INTO role_permissions (role_id, permission_id, created_at)
		VALUES ($1, $2, NOW())
		ON CONFLICT (role_id, permission_id) DO NOTHING
	`
	_, err := r.db.Exec(query, roleID, permissionID)
	return err
}

func (r *RoleRepository) RemovePermission(tenantID, roleID, permissionID uuid.UUID) error {
	query := `DELETE FROM role_permissions WHERE role_id = $1 AND permission_id = $2`
	_, err := r.db.Exec(query, roleID, permissionID)
	return err
}

func (r *RoleRepository) GetPermissions(tenantID, roleID uuid.UUID) ([]*models.Permission, error) {
	query := `
		SELECT p.id, p.name, p.description, p.created_at, p.updated_at
		FROM permissions p
		JOIN role_permissions rp ON p.id = rp.permission_id
		WHERE rp.role_id = $1 AND p.tenant_id = $2
		ORDER BY p.name
	`
	
	rows, err := r.db.Query(query, roleID, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var permissions []*models.Permission
	for rows.Next() {
		permission := &models.Permission{}
		err := rows.Scan(
			&permission.ID, &permission.Name, &permission.Description, &permission.CreatedAt, &permission.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		permissions = append(permissions, permission)
	}

	return permissions, nil
}

func (r *RoleRepository) AssignToUser(tenantID, roleID, userID uuid.UUID) error {
	query := `
		INSERT INTO user_roles (user_id, role_id, created_at)
		VALUES ($1, $2, NOW())
		ON CONFLICT (user_id, role_id) DO NOTHING
	`
	_, err := r.db.Exec(query, userID, roleID)
	return err
}

func (r *RoleRepository) RemoveFromUser(tenantID, roleID, userID uuid.UUID) error {
	query := `DELETE FROM user_roles WHERE user_id = $1 AND role_id = $2`
	_, err := r.db.Exec(query, userID, roleID)
	return err
}

func (r *RoleRepository) GetUserRoles(tenantID, userID uuid.UUID) ([]*models.Role, error) {
	query := `
		SELECT r.id, r.name, r.description, r.created_at, r.updated_at
		FROM roles r
		JOIN user_roles ur ON r.id = ur.role_id
		WHERE ur.user_id = $1 AND r.tenant_id = $2
		ORDER BY r.name
	`
	
	rows, err := r.db.Query(query, userID, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var roles []*models.Role
	for rows.Next() {
		role := &models.Role{}
		err := rows.Scan(
			&role.ID, &role.Name, &role.Description, &role.CreatedAt, &role.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		roles = append(roles, role)
	}

	return roles, nil
}

func (r *RoleRepository) CheckUserPermission(tenantID, userID uuid.UUID, permissionName string) (bool, error) {
	query := `
		SELECT COUNT(*)
		FROM permissions p
		JOIN role_permissions rp ON p.id = rp.permission_id
		JOIN roles r ON rp.role_id = r.id
		JOIN user_roles ur ON r.id = ur.role_id
		WHERE ur.user_id = $1 AND p.tenant_id = $2 AND p.name = $3
	`
	
	var count int
	err := r.db.QueryRow(query, userID, tenantID, permissionName).Scan(&count)
	if err != nil {
		return false, err
	}

	return count > 0, nil
}