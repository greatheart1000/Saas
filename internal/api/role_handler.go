package api

import (
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

// RoleHandler 处理角色相关的API请求
type RoleHandler struct {
	roleService models.RoleService
}

// NewRoleHandler 创建新的角色处理器
func NewRoleHandler(roleService models.RoleService) *RoleHandler {
	return &RoleHandler{
		roleService: roleService,
	}
}

// CreateRole 创建新角色
func (h *RoleHandler) CreateRole(c *gin.Context) {
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

	role, err := h.roleService.CreateRole(
		tenantID.(uuid.UUID),
		req.Name,
		req.Description,
	)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusCreated, role)
}

// GetRole 获取单个角色信息
func (h *RoleHandler) GetRole(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析角色ID
	roleID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的角色ID"})
		return
	}

	role, err := h.roleService.GetRoleByID(tenantID.(uuid.UUID), roleID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "角色不存在"})
		return
	}

	c.JSON(http.StatusOK, role)
}

// ListRoles 获取角色列表
func (h *RoleHandler) ListRoles(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	roles, err := h.roleService.ListRoles(tenantID.(uuid.UUID))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, roles)
}

// UpdateRole 更新角色信息
func (h *RoleHandler) UpdateRole(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析角色ID
	roleID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的角色ID"})
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

	// 获取现有角色信息
	role, err := h.roleService.GetRoleByID(tenantID.(uuid.UUID), roleID)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{"error": "角色不存在"})
		return
	}

	// 更新角色信息
	role.Name = req.Name
	role.Description = req.Description
	role.UpdatedAt = time.Now()

	if err := h.roleService.UpdateRole(tenantID.(uuid.UUID), role); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, role)
}

// DeleteRole 删除角色
func (h *RoleHandler) DeleteRole(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析角色ID
	roleID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的角色ID"})
		return
	}

	if err := h.roleService.DeleteRole(tenantID.(uuid.UUID), roleID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "角色删除成功"})
}

// AddPermissionToRole 为角色添加权限
func (h *RoleHandler) AddPermissionToRole(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析角色ID
	roleID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的角色ID"})
		return
	}

	var req struct {
		PermissionID string `json:"permission_id" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数"})
		return
	}

	permissionID, err := uuid.Parse(req.PermissionID)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的权限ID"})
		return
	}

	if err := h.roleService.AddPermissionToRole(tenantID.(uuid.UUID), roleID, permissionID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "权限添加成功"})
}

// RemovePermissionFromRole 从角色移除权限
func (h *RoleHandler) RemovePermissionFromRole(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析角色ID和权限ID
	roleID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的角色ID"})
		return
	}

	permissionID, err := uuid.Parse(c.Param("permission_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的权限ID"})
		return
	}

	if err := h.roleService.RemovePermissionFromRole(tenantID.(uuid.UUID), roleID, permissionID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "权限移除成功"})
}

// AssignRoleToUser 为用户分配角色
func (h *RoleHandler) AssignRoleToUser(c *gin.Context) {
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
		RoleID string `json:"role_id" binding:"required"`
	}

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的请求参数"})
		return
	}

	roleID, err := uuid.Parse(req.RoleID)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的角色ID"})
		return
	}

	if err := h.roleService.AssignRoleToUser(tenantID.(uuid.UUID), roleID, userID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "角色分配成功"})
}

// RemoveRoleFromUser 从用户移除角色
func (h *RoleHandler) RemoveRoleFromUser(c *gin.Context) {
	// 从上下文中获取租户ID
	tenantID, exists := c.Get("tenant_id")
	if !exists {
		c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户信息"})
		return
	}

	// 解析用户ID和角色ID
	userID, err := uuid.Parse(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的用户ID"})
		return
	}

	roleID, err := uuid.Parse(c.Param("role_id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "无效的角色ID"})
		return
	}

	if err := h.roleService.RemoveRoleFromUser(tenantID.(uuid.UUID), roleID, userID); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}

	c.JSON(http.StatusOK, gin.H{"message": "角色移除成功"})
}