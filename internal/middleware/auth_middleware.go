package middleware

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/yourusername/saas-multitenant/pkg/apikey"
	"github.com/yourusername/saas-multitenant/pkg/jwt"
)

// AuthMiddleware 用于认证和授权
type AuthMiddleware struct {
	tokenService   *jwt.TokenService
	apiKeyService  apikey.APIKeyService
}

// NewAuthMiddleware 创建新的认证中间件
func NewAuthMiddleware(tokenService *jwt.TokenService, apiKeyService apikey.APIKeyService) *AuthMiddleware {
	return &AuthMiddleware{
		tokenService:   tokenService,
		apiKeyService:  apiKeyService,
	}
}

// JWTAuth JWT认证中间件
func (m *AuthMiddleware) JWTAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 从请求头中获取Authorization
		authHeader := c.GetHeader("Authorization")
		if authHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "未提供认证令牌"})
			c.Abort()
			return
		}

		// 检查Authorization格式
		parts := strings.SplitN(authHeader, " ", 2)
		if !(len(parts) == 2 && parts[0] == "Bearer") {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "认证格式无效"})
			c.Abort()
			return
		}

		// 获取令牌
		tokenString := parts[1]

		// 验证令牌
		claims, err := m.tokenService.ValidateToken(tokenString, jwt.AccessToken)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "无效的认证令牌"})
			c.Abort()
			return
		}

		// 从上下文中获取租户ID
		tenantID, exists := c.Get("tenant_id")
		if !exists {
			c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
			c.Abort()
			return
		}

		// 验证令牌中的租户ID与请求中的租户ID是否匹配
		if claims.TenantID.String() != tenantID.(string) {
			c.JSON(http.StatusForbidden, gin.H{"error": "租户不匹配"})
			c.Abort()
			return
		}

		// 将用户信息存储在上下文中
		c.Set("user_id", claims.UserID)
		c.Set("username", claims.Username)
		c.Set("email", claims.Email)
		c.Set("role", claims.Role)

		c.Next()
	}
}

// APIKeyAuth API密钥认证中间件
func (m *AuthMiddleware) APIKeyAuth() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 从请求头中获取API密钥
		apiKeyHeader := c.GetHeader("X-API-Key")
		if apiKeyHeader == "" {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "未提供API密钥"})
			c.Abort()
			return
		}

		// 从上下文中获取租户ID
		tenantID, exists := c.Get("tenant_id")
		if !exists {
			c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
			c.Abort()
			return
		}

		// 验证API密钥
		apiKey, err := m.apiKeyService.ValidateAPIKey(tenantID.(string), apiKeyHeader)
		if err != nil {
			c.JSON(http.StatusUnauthorized, gin.H{"error": "无效的API密钥"})
			c.Abort()
			return
		}

		// 将用户信息存储在上下文中
		c.Set("user_id", apiKey.UserID)

		c.Next()
	}
}

// RequireRole 角色要求中间件
func (m *AuthMiddleware) RequireRole(role string) gin.HandlerFunc {
	return func(c *gin.Context) {
		// 从上下文中获取用户角色
		userRole, exists := c.Get("role")
		if !exists {
			c.JSON(http.StatusForbidden, gin.H{"error": "未找到用户角色信息"})
			c.Abort()
			return
		}

		// 检查用户角色是否满足要求
		if userRole.(string) != role && userRole.(string) != "admin" {
			c.JSON(http.StatusForbidden, gin.H{"error": "权限不足"})
			c.Abort()
			return
		}

		c.Next()
	}
}