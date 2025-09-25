package apikey

import (
	"crypto/rand"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"fmt"
	"time"

	"github.com/google/uuid"
)

// APIKey 表示API密钥
type APIKey struct {
	ID          uuid.UUID  `json:"id"`
	UserID      uuid.UUID  `json:"user_id"`
	Key         string     `json:"key"`
	Description string     `json:"description"`
	ExpiresAt   *time.Time `json:"expires_at"`
	Active      bool       `json:"active"`
	CreatedAt   time.Time  `json:"created_at"`
	UpdatedAt   time.Time  `json:"updated_at"`
}

// APIKeyService 定义API密钥相关操作的接口
type APIKeyService interface {
	GenerateAPIKey(tenantID, userID uuid.UUID, description string, expiryDays int) (*APIKey, error)
	ValidateAPIKey(tenantID uuid.UUID, apiKey string) (*APIKey, error)
	GetAPIKeyByID(tenantID, keyID uuid.UUID) (*APIKey, error)
	ListAPIKeysByUser(tenantID, userID uuid.UUID) ([]*APIKey, error)
	DeactivateAPIKey(tenantID, keyID uuid.UUID) error
	ActivateAPIKey(tenantID, keyID uuid.UUID) error
	DeleteAPIKey(tenantID, keyID uuid.UUID) error
}

// APIKeyRepository 定义API密钥数据访问的接口
type APIKeyRepository interface {
	Create(tenantID uuid.UUID, apiKey *APIKey) error
	GetByID(tenantID, keyID uuid.UUID) (*APIKey, error)
	GetByKey(tenantID uuid.UUID, key string) (*APIKey, error)
	ListByUser(tenantID, userID uuid.UUID) ([]*APIKey, error)
	Update(tenantID uuid.UUID, apiKey *APIKey) error
	Delete(tenantID, keyID uuid.UUID) error
}

// APIKeyGenerator 提供API密钥生成和验证功能
type APIKeyGenerator struct {}

// NewAPIKeyGenerator 创建新的API密钥生成器
func NewAPIKeyGenerator() *APIKeyGenerator {
	return &APIKeyGenerator{}
}

// Generate 生成新的API密钥
func (g *APIKeyGenerator) Generate() (string, error) {
	// 生成32字节的随机数据
	bytes := make([]byte, 32)
	_, err := rand.Read(bytes)
	if err != nil {
		return "", err
	}

	// 使用hex编码生成可读的API密钥
	return hex.EncodeToString(bytes), nil
}

// GenerateWithPrefix 生成带有前缀的API密钥
func (g *APIKeyGenerator) GenerateWithPrefix(prefix string) (string, error) {
	// 生成24字节的随机数据（前缀会占用一些空间）
	bytes := make([]byte, 24)
	_, err := rand.Read(bytes)
	if err != nil {
		return "", err
	}

	// 使用base64编码生成可读的API密钥部分
	randomPart := base64.URLEncoding.EncodeToString(bytes)

	// 组合前缀和随机部分
	return fmt.Sprintf("%s_%s", prefix, randomPart), nil
}

// ValidateFormat 验证API密钥格式
func (g *APIKeyGenerator) ValidateFormat(apiKey string) error {
	if len(apiKey) < 32 {
		return errors.New("API密钥格式无效：长度不足")
	}

	return nil
}