// 认证相关的JavaScript函数

function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    
    if (token && user && user.id) {
        // 用户已登录
        document.getElementById('nav-login').style.display = 'none';
        document.getElementById('nav-register').style.display = 'none';
        document.getElementById('nav-dashboard').style.display = 'block';
        document.getElementById('nav-logout').style.display = 'block';
        
        // 更新导航栏显示用户名
        const navDashboard = document.querySelector('#nav-dashboard a');
        if (navDashboard && user.username) {
            navDashboard.textContent = `控制台 (${user.username})`;
        }
    } else {
        // 用户未登录
        document.getElementById('nav-login').style.display = 'block';
        document.getElementById('nav-register').style.display = 'block';
        document.getElementById('nav-dashboard').style.display = 'none';
        document.getElementById('nav-logout').style.display = 'none';
    }
}

function logout() {
    // 清除本地存储的认证信息
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    // 显示提示信息
    alert('您已成功退出登录');
    
    // 更新导航栏
    checkAuthStatus();
    
    // 重定向到首页
    window.location.href = '/';
}

// 检查令牌是否过期
function isTokenExpired() {
    const token = localStorage.getItem('access_token');
    if (!token) return true;
    
    try {
        // 简单的JWT令牌过期检查（解码payload部分）
        const payload = JSON.parse(atob(token.split('.')[1]));
        const currentTime = Math.floor(Date.now() / 1000);
        return payload.exp < currentTime;
    } catch (error) {
        console.error('解析令牌失败:', error);
        return true;
    }
}

// 刷新访问令牌
async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) return false;
    
    try {
        const response = await fetch('/api/v1/auth/refresh', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });
        
        if (response.ok) {
            const result = await response.json();
            localStorage.setItem('access_token', result.access_token);
            localStorage.setItem('refresh_token', result.refresh_token);
            return true;
        } else {
            // 刷新失败，需要重新登录
            logout();
            return false;
        }
    } catch (error) {
        console.error('刷新令牌失败:', error);
        return false;
    }
}

// 发送带认证的请求
async function authenticatedFetch(url, options = {}) {
    let token = localStorage.getItem('access_token');
    
    if (!token) {
        throw new Error('未找到访问令牌');
    }
    
    // 检查令牌是否过期
    if (isTokenExpired()) {
        const refreshed = await refreshAccessToken();
        if (!refreshed) {
            throw new Error('令牌已过期，请重新登录');
        }
        token = localStorage.getItem('access_token');
    }
    
    // 设置认证头
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${token}`
    };
    
    return fetch(url, {
        ...options,
        headers
    });
}

// 获取用户信息
async function getCurrentUser() {
    const user = localStorage.getItem('user');
    if (user) {
        return JSON.parse(user);
    }
    return null;
}

// 检查用户权限
function hasRole(role) {
    const user = getCurrentUser();
    return user && user.role === role;
}

function hasAnyRole(roles) {
    const user = getCurrentUser();
    return user && roles.includes(user.role);
}

// 页面加载时检查认证状态
document.addEventListener('DOMContentLoaded', function() {
    checkAuthStatus();
});

// 导出函数供其他脚本使用
window.AuthUtils = {
    checkAuthStatus,
    logout,
    isTokenExpired,
    refreshAccessToken,
    authenticatedFetch,
    getCurrentUser,
    hasRole,
    hasAnyRole
};