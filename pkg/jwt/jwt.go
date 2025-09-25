package jwt

import (
	"errors"
	"fmt"
	"time"

	"github.com/dgrijalva/jwt-go"
	"github.com/google/uuid"
)

// Claims 自定义JWT声明结构
type Claims struct {
	UserID   uuid.UUID `json:"user_id"`
	Username string    `json:"username"`
	Email    string    `json:"email"`
	TenantID uuid.UUID `json:"tenant_id"`
	Role     string    `json:"role"`
	jwt.StandardClaims
}

// TokenType 定义令牌类型
type TokenType string

const (
	// AccessToken 访问令牌
	AccessToken TokenType = "access"
	// RefreshToken 刷新令牌
	RefreshToken TokenType = "refresh"
)

// TokenService 提供JWT令牌相关的功能
type TokenService struct {
	accessSecret  string
	refreshSecret string
	accessExpiry  time.Duration
	refreshExpiry time.Duration
}

// NewTokenService 创建新的令牌服务实例
func NewTokenService(accessSecret, refreshSecret string, accessExpiry, refreshExpiry time.Duration) *TokenService {
	return &TokenService{
		accessSecret:  accessSecret,
		refreshSecret: refreshSecret,
		accessExpiry:  accessExpiry,
		refreshExpiry: refreshExpiry,
	}
}

// GenerateToken 生成JWT令牌
func (s *TokenService) GenerateToken(userID uuid.UUID, username, email string, tenantID uuid.UUID, role string, tokenType TokenType) (string, time.Time, error) {
	var expiry time.Duration
	var secret string

	switch tokenType {
	case AccessToken:
		expiry = s.accessExpiry
		secret = s.accessSecret
	case RefreshToken:
		expiry = s.refreshExpiry
		secret = s.refreshSecret
	default:
		return "", time.Time{}, errors.New("无效的令牌类型")
	}

	expirationTime := time.Now().Add(expiry)

	claims := &Claims{
		UserID:   userID,
		Username: username,
		Email:    email,
		TenantID: tenantID,
		Role:     role,
		StandardClaims: jwt.StandardClaims{
			ExpiresAt: expirationTime.Unix(),
			IssuedAt:  time.Now().Unix(),
			Issuer:    "saas-multitenant",
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	tokenString, err := token.SignedString([]byte(secret))
	if err != nil {
		return "", time.Time{}, err
	}

	return tokenString, expirationTime, nil
}

// ValidateToken 验证JWT令牌
func (s *TokenService) ValidateToken(tokenString string, tokenType TokenType) (*Claims, error) {
	var secret string

	switch tokenType {
	case AccessToken:
		secret = s.accessSecret
	case RefreshToken:
		secret = s.refreshSecret
	default:
		return nil, errors.New("无效的令牌类型")
	}

	claims := &Claims{}

	token, err := jwt.ParseWithClaims(tokenString, claims, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, fmt.Errorf("意外的签名方法: %v", token.Header["alg"])
		}
		return []byte(secret), nil
	})

	if err != nil {
		return nil, err
	}

	if !token.Valid {
		return nil, errors.New("无效的令牌")
	}

	return claims, nil
}

// RefreshTokens 使用刷新令牌生成新的访问令牌和刷新令牌
func (s *TokenService) RefreshTokens(refreshToken string) (string, string, time.Time, error) {
	claims, err := s.ValidateToken(refreshToken, RefreshToken)
	if err != nil {
		return "", "", time.Time{}, err
	}

	// 生成新的访问令牌
	newAccessToken, expiresAt, err := s.GenerateToken(
		claims.UserID,
		claims.Username,
		claims.Email,
		claims.TenantID,
		claims.Role,
		AccessToken,
	)
	if err != nil {
		return "", "", time.Time{}, err
	}

	// 生成新的刷新令牌
	newRefreshToken, _, err := s.GenerateToken(
		claims.UserID,
		claims.Username,
		claims.Email,
		claims.TenantID,
		claims.Role,
		RefreshToken,
	)
	if err != nil {
		return "", "", time.Time{}, err
	}

	return newAccessToken, newRefreshToken, expiresAt, nil
}