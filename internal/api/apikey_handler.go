package api

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/pkg/apikey"
)

// APIKeyHandler 处理API密钥相关的API请求
type APIKeyHandler struct {
	apiKeyService apikey.APIKeyService
}

// NewAPIKeyHandler 创建新的API密钥处理器
func NewAPIKeyHandler(apiKeyService apikey.APIKeyService) *APIKeyHandler {
	return &APIKeyHandler{
		apiKeyService: apiKeyService,
	}
}

// GenerateAPIKey 生成新的API密钥
func (h *APIKeyHandler) GenerateAPIKey(c *gin.Context) {
	var req struct {
		Description string `json:"description"`
		ExpiryDays  int    `json:"expiry_days" binding:"required,min=1"`
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

	// 生成API密钥
	apiKey, err := h.apiKeyService.GenerateAPIKey(
		tenantID.(uuid.UUID),
		userID.(uuid.UUID),
		req.Description,
		req.ExpiryDays,
	)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, apiKey)
}

// ListAPIKeys 列出用户的所有API密钥
func (h *APIKeyHandler) ListAPIKeys(c *gin.Context) {
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

	// 列出API密钥
	apiKeys, err := h.apiKeyService.ListAPIKeysByUser(
		tenantID.(uuid.UUID),
		userID.(uuid.UUID),
	)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取API密钥列表失败"})
		return
	}

	c.JSON(http.StatusOK, apiKeys)
}

// DeactivateAPIKey 停用API密钥
func (h *APIKeyHandler) DeactivateAPIKey(c *gin.Context) {
	idStr := c.Param("id")
	id, err := uuid.Parse(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的API密钥ID"})
		return
	}

	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 停用API密钥
	err = h.apiKeyService.DeactivateAPIKey(tenantID.(uuid.UUID), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "API密钥已停用"})
}

// ActivateAPIKey 激活API密钥
func (h *APIKeyHandler) ActivateAPIKey(c *gin.Context) {
	idStr := c.Param("id")
	id, err := uuid.Parse(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的API密钥ID"})
		return
	}

	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 激活API密钥
	err = h.apiKeyService.ActivateAPIKey(tenantID.(uuid.UUID), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "API密钥已激活"})
}

// DeleteAPIKey 删除API密钥
func (h *APIKeyHandler) DeleteAPIKey(c *gin.Context) {
	idStr := c.Param("id")
	id, err := uuid.Parse(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的API密钥ID"})
		return
	}

	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 删除API密钥
	err = h.apiKeyService.DeleteAPIKey(tenantID.(uuid.UUID), id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "API密钥已删除"})
}