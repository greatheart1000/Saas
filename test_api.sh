#!/bin/bash

# SaaS系统API测试脚本

BASE_URL="http://localhost:8080/api/v1"
echo "=== SaaS多租户系统API测试 ==="
echo "测试地址: $BASE_URL"
echo ""

# 测试1: 创建租户
echo "1. 创建租户..."
curl -X POST "$BASE_URL/tenants" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-tenant"}' \
  -s | jq '.'
echo ""

# 测试2: 用户注册
echo "2. 用户注册..."
REGISTER_RESPONSE=$(curl -X POST "$BASE_URL/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "password123",
    "role": "user"
  }' \
  -s)
echo "$REGISTER_RESPONSE" | jq '.'
echo ""

# 提取租户ID（简化处理，实际应该从前面的响应中获取）
TENANT_ID="00000000-0000-0000-0000-000000000001"

# 测试3: 用户登录
echo "3. 用户登录..."
LOGIN_RESPONSE=$(curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "test@example.com",
    "password": "password123"
  }' \
  -s)
echo "$LOGIN_RESPONSE" | jq '.'
echo ""

# 提取访问令牌
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.refresh_token')

if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
    echo "✅ 登录成功，获得访问令牌"
    echo ""
    
    # 测试4: 获取用户信息
    echo "4. 获取用户信息..."
    curl -X GET "$BASE_URL/users" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -s | jq '.'
    echo ""
    
    # 测试5: 刷新令牌
    echo "5. 刷新令牌..."
    REFRESH_RESPONSE=$(curl -X POST "$BASE_URL/auth/refresh" \
      -H "Content-Type: application/json" \
      -d "{\"refresh_token\": \"$REFRESH_TOKEN\"}" \
      -s)
    echo "$REFRESH_RESPONSE" | jq '.'
    echo ""
    
    # 测试6: 创建权限
    echo "6. 创建权限..."
    curl -X POST "$BASE_URL/permissions" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "test.permission",
        "description": "测试权限"
      }' \
      -s | jq '.'
    echo ""
    
    # 测试7: 获取权限列表
    echo "7. 获取权限列表..."
    curl -X GET "$BASE_URL/permissions" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -s | jq '.'
    echo ""
    
    # 测试8: 创建角色
    echo "8. 创建角色..."
    curl -X POST "$BASE_URL/roles" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "test-role",
        "description": "测试角色"
      }' \
      -s | jq '.'
    echo ""
    
    # 测试9: 获取角色列表
    echo "9. 获取角色列表..."
    curl -X GET "$BASE_URL/roles" \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      -H "Content-Type: application/json" \
      -s | jq '.'
    echo ""
    
else
    echo "❌ 登录失败，无法继续测试"
    exit 1
fi

echo "=== API测试完成 ==="
echo ""
echo "🌐 Web界面地址: http://localhost:8080"
echo "📖 API文档地址: http://localhost:8080/swagger/index.html"
echo ""
echo "您可以访问以下页面："
echo "- 首页: http://localhost:8080/"
echo "- 登录: http://localhost:8080/login"
echo "- 注册: http://localhost:8080/register"
echo "- 控制台: http://localhost:8080/dashboard" 
echo ""
echo "测试用户："
echo "- 用户名: testuser"
echo "- 邮箱: test@example.com"
echo "- 密码: password123" 
echo ""
echo "🎉 SaaS多租户系统已就绪！" 
echo "请使用 'docker-compose down' 停止服务"