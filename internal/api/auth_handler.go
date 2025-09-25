package api

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
	"github.com/yourusername/saas-multitenant/pkg/jwt"
)

// AuthHandler 处理认证相关的API请求
type AuthHandler struct {
	userService  models.UserService
	tokenService *jwt.TokenService
}

// NewAuthHandler 创建新的认证处理器
func NewAuthHandler(userService models.UserService, tokenService *jwt.TokenService) *AuthHandler {
	return &AuthHandler{
		userService:  userService,
		tokenService: tokenService,
	}
}

// Register 注册新用户
func (h *AuthHandler) Register(c *gin.Context) {
	var req struct {
		Username string `json:"username" binding:"required"`
		Email    string `json:"email" binding:"required,email"`
		Password string `json:"password" binding:"required,min=8"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数"})
		return
	}

	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 创建用户
	user, err := h.userService.CreateUser(
		tenantID.(uuid.UUID),
		req.Username,
		req.Email,
		req.Password,
		"user", // 默认角色
	)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// 隐藏敏感信息
	user.PasswordHash = ""

	c.JSON(http.StatusCreated, user)
}

// Login 用户登录
func (h *AuthHandler) Login(c *gin.Context) {
	var req models.LoginRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数"})
		return
	}

	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 验证用户凭据
	user, err := h.userService.AuthenticateUser(
		tenantID.(uuid.UUID),
		req.UsernameOrEmail,
		req.Password,
	)

	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "无效的凭据"})
		return
	}

	// 生成令牌
	response, err := h.userService.GenerateTokens(tenantID.(uuid.UUID), user)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "生成令牌失败"})
		return
	}

	c.JSON(http.StatusOK, response)
}

// RefreshToken 刷新访问令牌
func (h *AuthHandler) RefreshToken(c *gin.Context) {
	var req struct {
		RefreshToken string `json:"refresh_token" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数"})
		return
	}

	// 验证刷新令牌
	claims, err := h.tokenService.ValidateToken(req.RefreshToken, jwt.RefreshToken)
	if err != nil {
		c.JSON(http.StatusUnauthorized, gin.H{"error": "无效的刷新令牌"})
		return
	}

	// 生成新的访问令牌和刷新令牌
	newAccessToken, newRefreshToken, expiresAt, err := h.tokenService.RefreshTokens(req.RefreshToken)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "生成新令牌失败"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"access_token":  newAccessToken,
		"refresh_token": newRefreshToken,
		"expires_at":    expiresAt,
	})
}

// ChangePassword 修改用户密码
func (h *AuthHandler) ChangePassword(c *gin.Context) {
	var req struct {
		CurrentPassword string `json:"current_password" binding:"required"`
		NewPassword     string `json:"new_password" binding:"required,min=8"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数"})
		return
	}

	// 从上下文中获取租户ID和用户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	userID, exists := c.Get("user_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到用户信息"})
		return
	}

	// 修改密码
	err := h.userService.ChangePassword(
		tenantID.(uuid.UUID),
		userID.(uuid.UUID),
		req.CurrentPassword,
		req.NewPassword,
	)

	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "密码修改成功"})
}