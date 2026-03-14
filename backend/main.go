package main

import (
	"log"
	"net/http"
	"os"
	"time"

	"github.com/daryl/cenidim-go-api/database"
	"github.com/daryl/cenidim-go-api/handlers"
	"github.com/daryl/cenidim-go-api/middleware"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func main() {
	// Initialize Database
	database.InitDB()

	// Setup Gin (gin.New is cleaner than Default when using custom middleware)
	r := gin.New()

	// Global Middleware
	r.Use(middleware.AdvancedLogger())
	r.Use(gin.Recovery()) // Panic recovery middleware

	// Middleware: CORS
	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"*"},
		AllowMethods:     []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:     []string{"Origin", "Content-Type", "Accept", "Authorization"},
		ExposeHeaders:    []string{"Content-Length"},
		AllowCredentials: true,
		MaxAge:           12 * time.Hour,
	}))

	// Routes
	r.GET("/", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"message": "Welcome to the Cenidim songs API (Go Version). " +
				"The available routes are /api/search and /api/song/:id",
		})
	})

	api := r.Group("/api")
	{
		api.GET("/search", handlers.SearchSongs)
		api.GET("/song/:song_id", handlers.GetSong)
	}

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

	// Run
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	log.Printf("Server starting on port %s", port)
	if err := r.Run(":" + port); err != nil {
		log.Fatalf("Critical server error: %v", err)
	}
}
