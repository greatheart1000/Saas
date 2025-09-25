package repository

import (
	"database/sql"
	"fmt"

	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

type PermissionRepository struct {
	db *sql.DB
}

func NewPermissionRepository(db *sql.DB) *PermissionRepository {
	return &PermissionRepository{db: db}
}

func (r *PermissionRepository) Create(tenantID uuid.UUID, permission *models.Permission) error {
	query := `
		INSERT INTO permissions (id, tenant_id, name, description, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6)
	`
	_, err := r.db.Exec(query, permission.ID, tenantID, permission.Name, permission.Description, permission.CreatedAt, permission.UpdatedAt)
	return err
}

func (r *PermissionRepository) GetByID(tenantID, permissionID uuid.UUID) (*models.Permission, error) {
	query := `
		SELECT id, name, description, created_at, updated_at
		FROM permissions
		WHERE id = $1 AND tenant_id = $2
	`
	
	permission := &models.Permission{}
	err := r.db.QueryRow(query, permissionID, tenantID).Scan(
		&permission.ID, &permission.Name, &permission.Description, &permission.CreatedAt, &permission.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("权限不存在")
	}
	if err != nil {
		return nil, err
	}

	return permission, nil
}

func (r *PermissionRepository) GetByName(tenantID uuid.UUID, name string) (*models.Permission, error) {
	query := `
		SELECT id, name, description, created_at, updated_at
		FROM permissions
		WHERE name = $1 AND tenant_id = $2
	`
	
	permission := &models.Permission{}
	err := r.db.QueryRow(query, name, tenantID).Scan(
		&permission.ID, &permission.Name, &permission.Description, &permission.CreatedAt, &permission.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("权限不存在")
	}
	if err != nil {
		return nil, err
	}

	return permission, nil
}

func (r *PermissionRepository) List(tenantID uuid.UUID) ([]*models.Permission, error) {
	query := `
		SELECT id, name, description, created_at, updated_at
		FROM permissions
		WHERE tenant_id = $1
		ORDER BY created_at DESC
	`
	
	rows, err := r.db.Query(query, tenantID)
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

func (r *PermissionRepository) Update(tenantID uuid.UUID, permission *models.Permission) error {
	query := `
		UPDATE permissions
		SET name = $3, description = $4, updated_at = $5
		WHERE id = $1 AND tenant_id = $2
	`
	
	_, err := r.db.Exec(query, permission.ID, tenantID, permission.Name, permission.Description, permission.UpdatedAt)
	return err
}

func (r *PermissionRepository) Delete(tenantID, permissionID uuid.UUID) error {
	query := `DELETE FROM permissions WHERE id = $1 AND tenant_id = $2`
	_, err := r.db.Exec(query, permissionID, tenantID)
	return err
}