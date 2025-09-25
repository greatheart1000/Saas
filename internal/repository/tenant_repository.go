package repository

import (
	"database/sql"
	"fmt"

	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

type TenantRepository struct {
	db *sql.DB
}

func NewTenantRepository(db *sql.DB) *TenantRepository {
	return &TenantRepository{db: db}
}

func (r *TenantRepository) Create(tenant *models.Tenant) error {
	query := `
		INSERT INTO tenants (id, name, schema_name, active, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6)
	`
	_, err := r.db.Exec(query, tenant.ID, tenant.Name, tenant.Schema, tenant.Active, tenant.CreatedAt, tenant.UpdatedAt)
	return err
}

func (r *TenantRepository) GetByID(id uuid.UUID) (*models.Tenant, error) {
	query := `
		SELECT id, name, schema_name, active, created_at, updated_at
		FROM tenants
		WHERE id = $1
	`
	
	tenant := &models.Tenant{}
	err := r.db.QueryRow(query, id).Scan(
		&tenant.ID, &tenant.Name, &tenant.Schema, &tenant.Active, &tenant.CreatedAt, &tenant.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("租户不存在")
	}
	if err != nil {
		return nil, err
	}

	return tenant, nil
}

func (r *TenantRepository) GetByName(name string) (*models.Tenant, error) {
	query := `
		SELECT id, name, schema_name, active, created_at, updated_at
		FROM tenants
		WHERE name = $1
	`
	
	tenant := &models.Tenant{}
	err := r.db.QueryRow(query, name).Scan(
		&tenant.ID, &tenant.Name, &tenant.Schema, &tenant.Active, &tenant.CreatedAt, &tenant.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("租户不存在")
	}
	if err != nil {
		return nil, err
	}

	return tenant, nil
}

func (r *TenantRepository) List() ([]*models.Tenant, error) {
	query := `
		SELECT id, name, schema_name, active, created_at, updated_at
		FROM tenants
		ORDER BY created_at DESC
	`
	
	rows, err := r.db.Query(query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var tenants []*models.Tenant
	for rows.Next() {
		tenant := &models.Tenant{}
		err := rows.Scan(
			&tenant.ID, &tenant.Name, &tenant.Schema, &tenant.Active, &tenant.CreatedAt, &tenant.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		tenants = append(tenants, tenant)
	}

	return tenants, nil
}

func (r *TenantRepository) Update(tenant *models.Tenant) error {
	query := `
		UPDATE tenants
		SET name = $2, schema_name = $3, active = $4, updated_at = $5
		WHERE id = $1
	`
	
	_, err := r.db.Exec(query, tenant.ID, tenant.Name, tenant.Schema, tenant.Active, tenant.UpdatedAt)
	return err
}