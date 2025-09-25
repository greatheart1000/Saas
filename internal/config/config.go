package config

import (
	"os"
	"time"
)

type Config struct {
	DatabaseURL    string
	JWTSecret      string
	JWTExpiration  time.Duration
	ServerPort     string
	Environment    string
}

func Load() *Config {
	return &Config{
		DatabaseURL:    getEnv("DATABASE_URL", "postgres://localhost/saas?sslmode=disable"),
		JWTSecret:      getEnv("JWT_SECRET", "your-secret-key-change-in-production"),
		JWTExpiration:  getDurationEnv("JWT_EXPIRATION", 24*time.Hour),
		ServerPort:     getEnv("PORT", "8080"),
		Environment:    getEnv("ENVIRONMENT", "development"),
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

func getDurationEnv(key string, defaultValue time.Duration) time.Duration {
	if value := os.Getenv(key); value != "" {
		if duration, err := time.ParseDuration(value); err == nil {
			return duration
		}
	}
	return defaultValue
}