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
	"context"
	"log"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
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
	if err := database.InitDB(); err != nil {
		log.Fatalf("Failed to initialize database: %v", err)
	}

	// Setup Gin (gin.New is cleaner than Default when using custom middleware)
	r := gin.New()

	// Global Middleware
	r.Use(middleware.AdvancedLogger())
	r.Use(gin.Recovery()) // Panic recovery middleware

	// Middleware: CORS
	allowedOrigins := os.Getenv("CORS_ALLOWED_ORIGINS")
	if allowedOrigins == "" {
		allowedOrigins = "http://localhost,http://localhost:3000,http://localhost:8000"
	}
	origins := strings.Split(allowedOrigins, ",")
	allowOrigins := make([]string, 0, len(origins))
	for _, origin := range origins {
		if trimmed := strings.TrimSpace(origin); trimmed != "" {
			allowOrigins = append(allowOrigins, trimmed)
		}
	}
	r.Use(cors.New(cors.Config{
		AllowOrigins:  allowOrigins,
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
		// Public endpoints
		api.GET("/search", handlers.SearchSongs)
		api.GET("/song/:song_id", handlers.GetSong)
		api.GET("/timeline", handlers.GetTimeline)
		api.GET("/stats", handlers.GetStats)
		api.GET("/word-cloud", handlers.GetWordCloud)

		// Auth endpoints
		auth := api.Group("/auth")
		{
			auth.POST("/login", handlers.Login)
			auth.POST("/register", handlers.Register)
			auth.GET("/me", middleware.RequireAuth(), handlers.Me)
		}

		// Admin endpoints (require authentication)
		admin := api.Group("/admin", middleware.RequireAuth())
		{
			// Fonogramas — editor+ can read/write, admin can delete
			admin.GET("/fonogramas", middleware.RequireRole("viewer"), handlers.AdminListFonogramas)
			admin.GET("/fonogramas/:id", middleware.RequireRole("viewer"), handlers.AdminGetFonograma)
			admin.POST("/fonogramas", middleware.RequireRole("editor"), handlers.AdminCreateFonograma)
			admin.PUT("/fonogramas/:id", middleware.RequireRole("editor"), handlers.AdminUpdateFonograma)
			admin.DELETE("/fonogramas/:id", middleware.RequireRole("admin"), handlers.AdminDeleteFonograma)

			// Songs/Letras
			admin.GET("/songs", middleware.RequireRole("viewer"), handlers.AdminListSongs)
			admin.POST("/songs", middleware.RequireRole("editor"), handlers.AdminCreateSong)
			admin.PUT("/songs/:id", middleware.RequireRole("editor"), handlers.AdminUpdateSong)
			admin.DELETE("/songs/:id", middleware.RequireRole("admin"), handlers.AdminDeleteSong)

			// Users (admin only)
			admin.GET("/users", middleware.RequireRole("admin"), handlers.AdminListUsers)
			admin.POST("/users", middleware.RequireRole("admin"), handlers.AdminCreateUser)
			admin.PUT("/users/:id", middleware.RequireRole("admin"), handlers.AdminUpdateUser)
			admin.DELETE("/users/:id", middleware.RequireRole("admin"), handlers.AdminDeleteUser)
		}

		// Swagger documentation inside /api
		api.GET("/swagger/*any", ginSwagger.WrapHandler(swaggerFiles.Handler))
	}

	// Health check
	r.GET("/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{"status": "healthy"})
	})

	// Graceful shutdown
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	srv := &http.Server{
		Addr:    ":" + port,
		Handler: r,
	}

	go func() {
		log.Printf("Server starting on port %s", port)
		if err := srv.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("Critical server error: %v", err)
		}
	}()

	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
	<-quit

	log.Println("Shutting down server...")
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := srv.Shutdown(ctx); err != nil {
		log.Fatalf("Server forced to shutdown: %v", err)
	}
	log.Println("Server exited gracefully")
}
