// @title Cenidim Songs API
// @version 1.0
// @description This is a sample server for Cenidim songs.
// @termsOfService http://swagger.io/terms/

// @contact.name API Support
// @contact.url http://www.swagger.io/support
// @contact.email support@swagger.io

// @license.name Apache 2.0
// @license.url http://www.apache.org/licenses/LICENSE-2.0.html

// @BasePath /api
package main

import (
	"log"
	"net/http"
	"os"
	"time"

	"github.com/daryl/cenidim-go-api/database"
	_ "github.com/daryl/cenidim-go-api/docs"
	"github.com/daryl/cenidim-go-api/handlers"
	"github.com/daryl/cenidim-go-api/middleware"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
	swaggerFiles "github.com/swaggo/files"
	ginSwagger "github.com/swaggo/gin-swagger"
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
		AllowOrigins:  []string{"*"},
		AllowMethods:  []string{"GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"},
		AllowHeaders:  []string{"Origin", "Content-Type", "Accept", "Authorization"},
		ExposeHeaders: []string{"Content-Length"},
		MaxAge:        12 * time.Hour,
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

		// Swagger documentation inside /api
		api.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
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
