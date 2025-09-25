package jwt

import (
	"errors"
	"time"

	"github.com/dgrijalva/jwt-go"
	"github.com/google/uuid"
)

type JWTService interface {
	GenerateToken(tenantID, userID uuid.UUID, role string) (string, error)
	GenerateRefreshToken(tenantID, userID uuid.UUID) (string, error)
	ValidateToken(tokenString string) (*JWTClaims, error)
	GetClaims(tokenString string) (*JWTClaims, error)
}

type jwtService struct {
	secret        []byte
	expiration    time.Duration
	refreshExp    time.Duration
}

type JWTClaims struct {
	TenantID uuid.UUID `json:"tenant_id"`
	UserID   uuid.UUID `json:"user_id"`
	Role     string    `json:"role"`
	jwt.StandardClaims
}

func NewJWTService(secret string, expiration time.Duration) JWTService {
	return &jwtService{
		secret:     []byte(secret),
		expiration: expiration,
		refreshExp: 7 * 24 * time.Hour, // 7 days for refresh token
	}
}

func (s *jwtService) GenerateToken(tenantID, userID uuid.UUID, role string) (string, error) {
	claims := &JWTClaims{
		TenantID: tenantID,
		UserID:   userID,
		Role:     role,
		StandardClaims: jwt.StandardClaims{
			ExpiresAt: time.Now().Add(s.expiration).Unix(),
			IssuedAt:  time.Now().Unix(),
			NotBefore: time.Now().Unix(),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(s.secret)
}

func (s *jwtService) GenerateRefreshToken(tenantID, userID uuid.UUID) (string, error) {
	claims := &JWTClaims{
		TenantID: tenantID,
		UserID:   userID,
		StandardClaims: jwt.StandardClaims{
			ExpiresAt: time.Now().Add(s.refreshExp).Unix(),
			IssuedAt:  time.Now().Unix(),
			NotBefore: time.Now().Unix(),
		},
	}

	token := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	return token.SignedString(s.secret)
}

func (s *jwtService) ValidateToken(tokenString string) (*JWTClaims, error) {
	claims, err := s.GetClaims(tokenString)
	if err != nil {
		return nil, err
	}

	if time.Now().Unix() > claims.ExpiresAt {
		return nil, errors.New("token has expired")
	}

	return claims, nil
}

func (s *jwtService) GetClaims(tokenString string) (*JWTClaims, error) {
	token, err := jwt.ParseWithClaims(tokenString, &JWTClaims{}, func(token *jwt.Token) (interface{}, error) {
		if _, ok := token.Method.(*jwt.SigningMethodHMAC); !ok {
			return nil, errors.New("unexpected signing method")
		}
		return s.secret, nil
	})

	if err != nil {
		return nil, err
	}

	if claims, ok := token.Claims.(*JWTClaims); ok && token.Valid {
		return claims, nil
	}

	return nil, errors.New("invalid token")
}