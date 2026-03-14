# Cenidim Web Application

This repository contains the full stack web application for **Cenidim** (Centro Nacional de Investigación, Documentación e Información Musical "Carlos Chávez").

The application serves a digital archive of musical lyrics, allowing users to search by title, album, or lyric content. It includes statistical dashboards and follows professional software development standards (Linting, CI/CD, and Unit Testing).

## Architecture

The project follows a modern decoupled architecture:

1.  **Backend (Go - Gin)**: A high-performance, low-latency API written in Go. It runs on a **Distroless** image for maximum security, handling search logic with millisecond response times.
2.  **Frontend (React)**: A "Premium White" minimalist user interface, served via an **unprivileged Nginx** container for a reduced attack surface.
3.  **Data Management**: A custom Go-based builder script that parses raw text data into a structured SQLite database during the Docker build phase.

## Setup Instructions

### 1. Database Initialization
Before running the application, you must build the database from the raw metadata:
```bash
./scripts/build_db.sh
```
*This requires Go to be installed on your machine.*

### 2. Running with Docker (Recommended)
You can spin up the entire stack using Docker Compose:
```bash
docker compose up --build -d
```
- **Frontend**: Available at `http://localhost` (served via Nginx).
- **Backend API**: Internal port 8080, mapped to `http://localhost:8000`.
- **Health Check**: `http://localhost:8000/health`.

### 3. Local Development

**Backend (Go):**
```bash
cd backend
go run main.go
```

**Frontend (React):**
```bash
cd frontend
npm install
npm start
```

## Testing and Quality
- **Backend**: `go test ./...` (includes Unit and Integration tests).
- **Frontend**: `npm test` (React Testing Library).
- **CI/CD**: Fully automated pipeline via GitHub Actions.
