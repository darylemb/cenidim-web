package middleware

import (
	"log"
	"time"

	"github.com/gin-gonic/gin"
)

// AdvancedLogger is a custom middleware for advanced request logging with performance metrics
func AdvancedLogger() gin.HandlerFunc {
	return func(c *gin.Context) {
		// Start timer
		start := time.Now()
		path := c.Request.URL.Path
		raw := c.Request.URL.RawQuery

		// Process request
		c.Next()

		// Stop timer
		latency := time.Since(start)

		clientIP := c.ClientIP()
		method := c.Request.Method
		statusCode := c.Writer.Status()

		if raw != "" {
			path = path + "?" + raw
		}

		// Choose a "visual" status indicator
		statusColor := "✅"
		if statusCode >= 400 && statusCode < 500 {
			statusColor = "⚠️"
		} else if statusCode >= 500 {
			statusColor = "❌"
		}

		log.Printf("[GIN] %s %3d | %13v | %15s | %-7s %#v\n",
			statusColor,
			statusCode,
			latency,
			clientIP,
			method,
			path,
		)
	}
}
