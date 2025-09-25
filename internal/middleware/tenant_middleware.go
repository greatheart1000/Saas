package middleware

import (
	"net/http"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
	"github.com/yourusername/saas-multitenant/internal/models"
)

// TenantMiddleware 用于识别和验证租户
type TenantMiddleware struct {
	tenantService models.TenantService
}

// NewTenantMiddleware 创建新的租户中间件
func NewTenantMiddleware(tenantService models.TenantService) *TenantMiddleware {
	return &TenantMiddleware{
		tenantService: tenantService,
	}
}

// IdentifyTenant 从请求中识别租户
func (m *TenantMiddleware) IdentifyTenant() gin.HandlerFunc {
	return func(c *gin.Context) {
		// 从请求头中获取租户标识
		tenantIdentifier := c.GetHeader("X-Tenant")
		if tenantIdentifier == "" {
			// 尝试从子域名中获取租户标识
			host := c.Request.Host
			parts := strings.Split(host, ".")
			if len(parts) > 0 {
				tenantIdentifier = parts[0]
			}
		}

		if tenantIdentifier == "" {
			c.JSON(http.StatusBadRequest, gin.H{"error": "未找到租户标识"})
			c.Abort()
			return
		}

		// 尝试通过名称查找租户
		tenant, err := m.tenantService.GetTenantByName(tenantIdentifier)
		if err != nil {
			// 尝试通过ID查找租户
			id, uuidErr := uuid.Parse(tenantIdentifier)
			if uuidErr != nil {
				c.JSON(http.StatusNotFound, gin.H{"error": "租户不存在"})
				c.Abort()
				return
			}

			tenant, err = m.tenantService.GetTenantByID(id)
			if err != nil {
				c.JSON(http.StatusNotFound, gin.H{"error": "租户不存在"})
				c.Abort()
				return
			}
		}

		// 检查租户是否激活
		if !tenant.Active {
			c.JSON(http.StatusForbidden, gin.H{"error": "租户已停用"})
			c.Abort()
			return
		}

		// 将租户信息存储在上下文中
		c.Set("tenant_id", tenant.ID)
		c.Set("tenant_name", tenant.Name)
		c.Set("tenant_schema", tenant.Schema)

		c.Next()
	}
}