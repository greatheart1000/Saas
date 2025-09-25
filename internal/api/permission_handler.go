package api

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

// PermissionHandler 处理权限相关的API请求
type PermissionHandler struct {
	permissionService models.PermissionService
}

// NewPermissionHandler 创建新的权限处理器
func NewPermissionHandler(permissionService models.PermissionService) *PermissionHandler {
	return &PermissionHandler{
		permissionService: permissionService,
	}
}

// CreatePermission 创建新权限
func (h *PermissionHandler) CreatePermission(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	var req struct {
		Name        string `json:"name" binding:"required"`
		Description string `json:"description"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数"})
		return
	}

	permission, err := h.permissionService.CreatePermission(
		tenantID.(uuid.UUID),
		req.Name,
		req.Description,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, permission)
}

// GetPermission 获取单个权限信息
func (h *PermissionHandler) GetPermission(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析权限ID
	permissionID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的权限ID"})
		return
	}

	permission, err := h.permissionService.GetPermissionByID(tenantID.(uuid.UUID), permissionID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "权限不存在"})
		return
	}

	c.JSON(http.StatusOK, permission)
}

// ListPermissions 获取权限列表
func (h *PermissionHandler) ListPermissions(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	permissions, err := h.permissionService.ListPermissions(tenantID.(uuid.UUID))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, permissions)
}

// UpdatePermission 更新权限信息
func (h *PermissionHandler) UpdatePermission(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析权限ID
	permissionID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的权限ID"})
		return
	}

	var req struct {
		Name        string `json:"name" binding:"required"`
		Description string `json:"description"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数"})
		return
	}

	// 获取现有权限信息
	permission, err := h.permissionService.GetPermissionByID(tenantID.(uuid.UUID), permissionID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "权限不存在"})
		return
	}

	// 更新权限信息
	permission.Name = req.Name
	permission.Description = req.Description
	permission.UpdatedAt = time.Now()

	if err := h.permissionService.UpdatePermission(tenantID.(uuid.UUID), permission); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, permission)
}

// DeletePermission 删除权限
func (h *PermissionHandler) DeletePermission(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析权限ID
	permissionID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的权限ID"})
		return
	}

	if err := h.permissionService.DeletePermission(tenantID.(uuid.UUID), permissionID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "权限删除成功"})
}