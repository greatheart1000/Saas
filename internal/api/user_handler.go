package api

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

// UserHandler 处理用户相关的API请求
type UserHandler struct {
	userService models.UserService
}

// NewUserHandler 创建新的用户处理器
func NewUserHandler(userService models.UserService) *UserHandler {
	return &UserHandler{
		userService: userService,
	}
}

// ListUsers 获取用户列表
func (h *UserHandler) ListUsers(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	users, err := h.userService.ListUsers(tenantID.(uuid.UUID))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// 隐藏敏感信息
	for _, user := range users {
		user.PasswordHash = ""
	}

	c.JSON(http.StatusOK, users)
}

// GetUser 获取单个用户信息
func (h *UserHandler) GetUser(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析用户ID
	userID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的用户ID"})
		return
	}

	user, err := h.userService.GetUserByID(tenantID.(uuid.UUID), userID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "用户不存在"})
		return
	}

	// 隐藏敏感信息
	user.PasswordHash = ""

	c.JSON(http.StatusOK, user)
}

// UpdateUser 更新用户信息
func (h *UserHandler) UpdateUser(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析用户ID
	userID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的用户ID"})
		return
	}

	var req struct {
		Username string `json:"username"`
		Email    string `json:"email"`
		Role     string `json:"role"`
		Active   *bool  `json:"active"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数"})
		return
	}

	// 获取现有用户信息
	user, err := h.userService.GetUserByID(tenantID.(uuid.UUID), userID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "用户不存在"})
		return
	}

	// 更新用户信息
	if req.Username != "" {
		user.Username = req.Username
	}
	if req.Email != "" {
		user.Email = req.Email
	}
	if req.Role != "" {
		user.Role = req.Role
	}
	if req.Active != nil {
		user.Active = *req.Active
	}

	if err := h.userService.UpdateUser(tenantID.(uuid.UUID), user); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	// 隐藏敏感信息
	user.PasswordHash = ""

	c.JSON(http.StatusOK, user)
}

// DeleteUser 删除用户
func (h *UserHandler) DeleteUser(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析用户ID
	userID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的用户ID"})
		return
	}

	// 停用用户（逻辑删除）
	if err := h.userService.DeactivateUser(tenantID.(uuid.UUID), userID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "用户删除成功"})
}