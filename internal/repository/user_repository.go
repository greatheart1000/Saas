package repository

import (
	"database/sql"
	"fmt"

	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

type UserRepository struct {
	db *sql.DB
}

func NewUserRepository(db *sql.DB) *UserRepository {
	return &UserRepository{db: db}
}

func (r *UserRepository) Create(tenantID uuid.UUID, user *models.User) error {
	query := `
		INSERT INTO users (id, tenant_id, username, email, password_hash, role, active, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`
	_, err := r.db.Exec(query, user.ID, tenantID, user.Username, user.Email, user.PasswordHash, user.Role, user.Active, user.CreatedAt, user.UpdatedAt)
	return err
}

func (r *UserRepository) GetByID(tenantID, userID uuid.UUID) (*models.User, error) {
	query := `
		SELECT id, username, email, password_hash, role, active, created_at, updated_at
		FROM users
		WHERE id = $1 AND tenant_id = $2
	`
	
	user := &models.User{}
	err := r.db.QueryRow(query, userID, tenantID).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.Role, &user.Active, &user.CreatedAt, &user.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("用户不存在")
	}
	if err != nil {
		return nil, err
	}

	return user, nil
}

func (r *UserRepository) GetByUsername(tenantID uuid.UUID, username string) (*models.User, error) {
	query := `
		SELECT id, username, email, password_hash, role, active, created_at, updated_at
		FROM users
		WHERE username = $1 AND tenant_id = $2
	`
	
	user := &models.User{}
	err := r.db.QueryRow(query, username, tenantID).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.Role, &user.Active, &user.CreatedAt, &user.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("用户不存在")
	}
	if err != nil {
		return nil, err
	}

	return user, nil
}

func (r *UserRepository) GetByEmail(tenantID uuid.UUID, email string) (*models.User, error) {
	query := `
		SELECT id, username, email, password_hash, role, active, created_at, updated_at
		FROM users
		WHERE email = $1 AND tenant_id = $2
	`
	
	user := &models.User{}
	err := r.db.QueryRow(query, email, tenantID).Scan(
		&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.Role, &user.Active, &user.CreatedAt, &user.UpdatedAt,
	)
	
	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("用户不存在")
	}
	if err != nil {
		return nil, err
	}

	return user, nil
}

func (r *UserRepository) List(tenantID uuid.UUID) ([]*models.User, error) {
	query := `
		SELECT id, username, email, password_hash, role, active, created_at, updated_at
		FROM users
		WHERE tenant_id = $1
		ORDER BY created_at DESC
	`
	
	rows, err := r.db.Query(query, tenantID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var users []*models.User
	for rows.Next() {
		user := &models.User{}
		err := rows.Scan(
			&user.ID, &user.Username, &user.Email, &user.PasswordHash, &user.Role, &user.Active, &user.CreatedAt, &user.UpdatedAt,
		)
		if err != nil {
			return nil, err
		}
		users = append(users, user)
	}

	return users, nil
}

func (r *UserRepository) Update(tenantID uuid.UUID, user *models.User) error {
	query := `
		UPDATE users
		SET username = $3, email = $4, password_hash = $5, role = $6, active = $7, updated_at = $8
		WHERE id = $1 AND tenant_id = $2
	`
	
	_, err := r.db.Exec(query, user.ID, tenantID, user.Username, user.Email, user.PasswordHash, user.Role, user.Active, user.UpdatedAt)
	return err
}