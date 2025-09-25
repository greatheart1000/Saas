package models

import (
	"time"

	"github.com/google/uuid"
)

// User 表示系统中的用户
type User struct {
	ID           uuid.UUID `json:"id"`
	Username     string    `json:"username"`
	Email        string    `json:"email"`
	PasswordHash string    `json:"password_hash,omitempty"`
	Role         string    `json:"role"`
	Active       bool      `json:"active"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
}

// UserService 定义用户相关操作的接口
type UserService interface {
	CreateUser(tenantID uuid.UUID, username, email, password, role string) (*User, error)
	GetUserByID(tenantID, userID uuid.UUID) (*User, error)
	GetUserByUsername(tenantID uuid.UUID, username string) (*User, error)
	GetUserByEmail(tenantID uuid.UUID, email string) (*User, error)
	ListUsers(tenantID uuid.UUID) ([]*User, error)
	UpdateUser(tenantID uuid.UUID, user *User) error
	DeactivateUser(tenantID, userID uuid.UUID) error
	ActivateUser(tenantID, userID uuid.UUID) error
	AuthenticateUser(tenantID uuid.UUID, usernameOrEmail, password string) (*User, error)
	ChangePassword(tenantID, userID uuid.UUID, currentPassword, newPassword string) error
}

// UserRepository 定义用户数据访问的接口
type UserRepository interface {
	Create(tenantID uuid.UUID, user *User) error
	GetByID(tenantID, userID uuid.UUID) (*User, error)
	GetByUsername(tenantID uuid.UUID, username string) (*User, error)
	GetByEmail(tenantID uuid.UUID, email string) (*User, error)
	List(tenantID uuid.UUID) ([]*User, error)
	Update(tenantID uuid.UUID, user *User) error
}

// LoginRequest 表示登录请求
type LoginRequest struct {
	UsernameOrEmail string `json:"username_or_email" binding:"required"`
	Password        string `json:"password" binding:"required"`
}

// LoginResponse 表示登录响应
type LoginResponse struct {
	AccessToken  string    `json:"access_token"`
	RefreshToken string    `json:"refresh_token"`
	ExpiresAt    time.Time `json:"expires_at"`
	User         *User     `json:"user"`
}