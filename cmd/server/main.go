package main

import (
	"log"
	"os"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/joho/godotenv"
	"github.com/yourusername/saas-multitenant/internal/api"
	"github.com/yourusername/saas-multitenant/internal/config"
	middleware "github.com/yourusername/saas-multitenant/internal/middleware"
	"github.com/yourusername/saas-multitenant/internal/repository"
	"github.com/yourusername/saas-multitenant/internal/service"
	"github.com/yourusername/saas-multitenant/pkg/database"
	"github.com/yourusername/saas-multitenant/pkg/jwt"
)

func main() {
	// 加载环境变量
	if err := godotenv.Load(); err != nil {
		log.Println("未找到 .env 文件，使用默认配置")
	}

	// 加载配置
	cfg := config.Load()

	// 初始化数据库
	db, err := database.Initialize(cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("数据库初始化失败: %v", err)
	}
	defer db.Close()

	// 运行数据库迁移
	if err := database.Migrate(db); err != nil {
		log.Fatalf("数据库迁移失败: %v", err)
	}

	// 初始化 JWT 服务
	tokenService := jwt.NewTokenService(
		cfg.JWTSecret, 
		cfg.JWTSecret, // 使用相同的密钥用于刷新令牌
		cfg.JWTExpiration,
		7*24*time.Hour, // 刷新令牌有效期7天
	)

	// 初始化服务层
	tenantService := service.NewTenantService(db, repository.NewTenantRepository(db))
	userService := service.NewUserService(db, repository.NewUserRepository(db), tokenService)
	permissionService := service.NewPermissionService(db, repository.NewPermissionRepository(db))
	roleService := service.NewRoleService(db, repository.NewRoleRepository(db))

	// 初始化处理器
	authHandler := api.NewAuthHandler(userService, tokenService)
	tenantHandler := api.NewTenantHandler(tenantService)
	userHandler := api.NewUserHandler(userService)
	permissionHandler := api.NewPermissionHandler(permissionService)
	roleHandler := api.NewRoleHandler(roleService)

	// 创建 Gin 路由器
	r := gin.Default()

	// 设置静态文件服务
	r.Static("/static", "./web/static")
	r.LoadHTMLGlob("web/templates/*")

	// 设置首页路由
	r.GET("/", func(c *gin.Context) {
		c.HTML(200, "index.html", gin.H{
			"title": "SaaS 多租户系统",
		})
	})

	// API 路由组
	api := r.Group("/api/v1")
	{
		// 租户相关路由
		api.POST("/tenants", tenantHandler.CreateTenant)
		api.GET("/tenants", tenantHandler.ListTenants)
		api.GET("/tenants/:id", tenantHandler.GetTenant)
		api.PUT("/tenants/:id", tenantHandler.UpdateTenant)
		api.DELETE("/tenants/:id", tenantHandler.DeleteTenant)

		// 认证相关路由
		api.POST("/auth/register", authHandler.Register)
		api.POST("/auth/login", authHandler.Login)
		api.POST("/auth/refresh", authHandler.RefreshToken)
		api.POST("/auth/change-password", middleware.AuthMiddleware(tokenService), authHandler.ChangePassword)

		// 受保护的路由
		protected := api.Group("")
		protected.Use(middleware.AuthMiddleware(tokenService))
		{
			// 用户相关路由
			protected.GET("/users", userHandler.ListUsers)
			protected.GET("/users/:id", userHandler.GetUser)
			protected.PUT("/users/:id", userHandler.UpdateUser)
			protected.DELETE("/users/:id", userHandler.DeleteUser)

			// 权限相关路由
			protected.GET("/permissions", permissionHandler.ListPermissions)
			protected.POST("/permissions", permissionHandler.CreatePermission)
			protected.PUT("/permissions/:id", permissionHandler.UpdatePermission)
			protected.DELETE("/permissions/:id", permissionHandler.DeletePermission)

			// 角色相关路由
			protected.GET("/roles", roleHandler.ListRoles)
			protected.POST("/roles", roleHandler.CreateRole)
			protected.PUT("/roles/:id", roleHandler.UpdateRole)
			protected.DELETE("/roles/:id", roleHandler.DeleteRole)
			protected.POST("/roles/:id/permissions", roleHandler.AddPermissionToRole)
			protected.DELETE("/roles/:id/permissions/:permission_id", roleHandler.RemovePermissionFromRole)
			protected.POST("/users/:id/roles", roleHandler.AssignRoleToUser)
			protected.DELETE("/users/:id/roles/:role_id", roleHandler.RemoveRoleFromUser)
		}
	}

	// 前端页面路由
	r.GET("/login", func(c *gin.Context) {
		c.HTML(200, "login.html", gin.H{
			"title": "登录 - SaaS 系统",
		})
	})

	r.GET("/register", func(c *gin.Context) {
		c.HTML(200, "register.html", gin.H{
			"title": "注册 - SaaS 系统",
		})
	})

	r.GET("/dashboard", middleware.AuthMiddleware(tokenService), func(c *gin.Context) {
		c.HTML(200, "dashboard.html", gin.H{
			"title": "控制台 - SaaS 系统",
		})
	})

	// 获取端口
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("服务器启动在端口 %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("服务器启动失败: %v", err)
	}
}