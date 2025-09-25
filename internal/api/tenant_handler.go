package api

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

// TenantHandler 处理租户相关的API请求
type TenantHandler struct {
	tenantService models.TenantService
}

// NewTenantHandler 创建新的租户处理器
func NewTenantHandler(tenantService models.TenantService) *TenantHandler {
	return &TenantHandler{
		tenantService: tenantService,
	}
}

// CreateTenant 创建新租户
func (h *TenantHandler) CreateTenant(c *gin.Context) {
	var req struct {
		Name string `json:"name" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数"})
		return
	}

	// 创建租户
	tenant, err := h.tenantService.CreateTenant(req.Name)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, tenant)
}

// GetTenant 获取租户信息
func (h *TenantHandler) GetTenant(c *gin.Context) {
	idStr := c.Param("id")
	id, err := uuid.Parse(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的租户ID"})
		return
	}

	// 获取租户
	tenant, err := h.tenantService.GetTenantByID(id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "租户不存在"})
		return
	}

	c.JSON(http.StatusOK, tenant)
}

// ListTenants 列出所有租户
func (h *TenantHandler) ListTenants(c *gin.Context) {
	// 列出租户
	tenants, err := h.tenantService.ListTenants()
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "获取租户列表失败"})
		return
	}

	c.JSON(http.StatusOK, tenants)
}

// DeactivateTenant 停用租户
func (h *TenantHandler) DeactivateTenant(c *gin.Context) {
	idStr := c.Param("id")
	id, err := uuid.Parse(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的租户ID"})
		return
	}

	// 停用租户
	err = h.tenantService.DeactivateTenant(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "租户已停用"})
}

// ActivateTenant 激活租户
func (h *TenantHandler) ActivateTenant(c *gin.Context) {
	idStr := c.Param("id")
	id, err := uuid.Parse(idStr)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的租户ID"})
		return
	}

	// 激活租户
	err = h.tenantService.ActivateTenant(id)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "租户已激活"})
}