package service

import (
	"database/sql"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
	"github.com/yourusername/saas-multitenant/pkg/jwt"
	"golang.org/x/crypto/bcrypt"
)

// UserServiceImpl 实现用户服务接口
type UserServiceImpl struct {
	db         *sql.DB
	repository models.UserRepository
	tokenSvc   *jwt.TokenService
}

// NewUserService 创建新的用户服务实例
func NewUserService(db *sql.DB, repo models.UserRepository, tokenSvc *jwt.TokenService) models.UserService {
	return &UserServiceImpl{
		db:         db,
		repository: repo,
		tokenSvc:   tokenSvc,
	}
}

// CreateUser 创建新用户
func (s *UserServiceImpl) CreateUser(tenantID uuid.UUID, username, email, password, role string) (*models.User, error) {
	// 检查用户名是否已存在
	existingUser, err := s.repository.GetByUsername(tenantID, username)
	if err != nil && err != sql.ErrNoRows {
		return nil, fmt.Errorf("检查用户名时出错: %w", err)
	}
	if existingUser != nil {
		return nil, fmt.Errorf("用户名 '%s' 已存在", username)
	}

	// 检查邮箱是否已存在
	existingUser, err = s.repository.GetByEmail(tenantID, email)
	if err != nil && err != sql.ErrNoRows {
		return nil, fmt.Errorf("检查邮箱时出错: %w", err)
	}
	if existingUser != nil {
		return nil, fmt.Errorf("邮箱 '%s' 已存在", email)
	}

	// 生成密码哈希
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		return nil, fmt.Errorf("生成密码哈希时出错: %w", err)
	}

	// 创建新用户
	user := &models.User{
		ID:           uuid.New(),
		Username:     username,
		Email:        email,
		PasswordHash: string(hashedPassword),
		Role:         role,
		Active:       true,
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
	}

	// 保存用户到数据库
	if err := s.repository.Create(tenantID, user); err != nil {
		return nil, fmt.Errorf("创建用户时出错: %w", err)
	}

	return user, nil
}

// GetUserByID 通过ID获取用户
func (s *UserServiceImpl) GetUserByID(tenantID, userID uuid.UUID) (*models.User, error) {
	return s.repository.GetByID(tenantID, userID)
}

// GetUserByUsername 通过用户名获取用户
func (s *UserServiceImpl) GetUserByUsername(tenantID uuid.UUID, username string) (*models.User, error) {
	return s.repository.GetByUsername(tenantID, username)
}

// GetUserByEmail 通过邮箱获取用户
func (s *UserServiceImpl) GetUserByEmail(tenantID uuid.UUID, email string) (*models.User, error) {
	return s.repository.GetByEmail(tenantID, email)
}

// ListUsers 列出所有用户
func (s *UserServiceImpl) ListUsers(tenantID uuid.UUID) ([]*models.User, error) {
	return s.repository.List(tenantID)
}

// UpdateUser 更新用户信息
func (s *UserServiceImpl) UpdateUser(tenantID uuid.UUID, user *models.User) error {
	user.UpdatedAt = time.Now()
	return s.repository.Update(tenantID, user)
}

// DeactivateUser 停用用户
func (s *UserServiceImpl) DeactivateUser(tenantID, userID uuid.UUID) error {
	user, err := s.repository.GetByID(tenantID, userID)
	if err != nil {
		return err
	}
	user.Active = false
	user.UpdatedAt = time.Now()
	return s.repository.Update(tenantID, user)
}

// ActivateUser 激活用户
func (s *UserServiceImpl) ActivateUser(tenantID, userID uuid.UUID) error {
	user, err := s.repository.GetByID(tenantID, userID)
	if err != nil {
		return err
	}
	user.Active = true
	user.UpdatedAt = time.Now()
	return s.repository.Update(tenantID, user)
}

// AuthenticateUser 验证用户凭据并返回用户信息
func (s *UserServiceImpl) AuthenticateUser(tenantID uuid.UUID, usernameOrEmail, password string) (*models.User, error) {
	// 尝试通过用户名查找用户
	user, err := s.repository.GetByUsername(tenantID, usernameOrEmail)
	if err != nil && err != sql.ErrNoRows {
		return nil, err
	}

	// 如果通过用户名未找到，尝试通过邮箱查找
	if user == nil {
		user, err = s.repository.GetByEmail(tenantID, usernameOrEmail)
		if err != nil {
			return nil, err
		}
	}

	// 检查用户是否存在
	if user == nil {
		return nil, errors.New("用户名或密码无效")
	}

	// 检查用户是否激活
	if !user.Active {
		return nil, errors.New("用户账户已停用")
	}

	// 验证密码
	err = bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(password))
	if err != nil {
		return nil, errors.New("用户名或密码无效")
	}

	return user, nil
}

// ChangePassword 更改用户密码
func (s *UserServiceImpl) ChangePassword(tenantID, userID uuid.UUID, currentPassword, newPassword string) error {
	// 获取用户
	user, err := s.repository.GetByID(tenantID, userID)
	if err != nil {
		return err
	}

	// 验证当前密码
	err = bcrypt.CompareHashAndPassword([]byte(user.PasswordHash), []byte(currentPassword))
	if err != nil {
		return errors.New("当前密码无效")
	}

	// 生成新密码哈希
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
	if err != nil {
		return fmt.Errorf("生成密码哈希时出错: %w", err)
	}

	// 更新密码
	user.PasswordHash = string(hashedPassword)
	user.UpdatedAt = time.Now()

	return s.repository.Update(tenantID, user)
}

// GenerateTokens 为用户生成访问令牌和刷新令牌
func (s *UserServiceImpl) GenerateTokens(tenantID uuid.UUID, user *models.User) (*models.LoginResponse, error) {
	// 生成访问令牌
	accessToken, expiresAt, err := s.tokenSvc.GenerateToken(
		user.ID,
		user.Username,
		user.Email,
		tenantID,
		user.Role,
		jwt.AccessToken,
	)
	if err != nil {
		return nil, fmt.Errorf("生成访问令牌时出错: %w", err)
	}

	// 生成刷新令牌
	refreshToken, _, err := s.tokenSvc.GenerateToken(
		user.ID,
		user.Username,
		user.Email,
		tenantID,
		user.Role,
		jwt.RefreshToken,
	)
	if err != nil {
		return nil, fmt.Errorf("生成刷新令牌时出错: %w", err)
	}

	// 创建登录响应
	response := &models.LoginResponse{
		AccessToken:  accessToken,
		RefreshToken: refreshToken,
		ExpiresAt:    expiresAt,
		User:         user,
	}

	return response, nil
}