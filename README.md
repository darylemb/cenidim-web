# Cenidim Web Application

This repository contains the full stack web application for **Cenidim** (Centro Nacional de Investigación, Documentación e Información Musical "Carlos Chávez").

The application serves a database of musical lyrics, allowing users to search by title, album, or lyric content. It also includes statistical dashboards built as a foundation for future Natural Language Processing (NLP) sentiment analysis integrations.

## Architecture

This project is decoupled into a backend API and a frontend client:

1. **Backend (Python / FastAPI)**: A lightweight, high-performance API that connects to a local SQLite database (`letras.db`). It serves the search results and provides raw text data ready to be consumed by AI models.
2. **Frontend (React)**: A responsive, modern user interface that authentically replicates the institutional design system.

## Setup Instructions

### 1. Running Locally (Development)

**Backend Setup:**
Open a terminal in the root directory and run:
```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install the Python dependencies
pip install -r requirements.txt

# Run the FastAPI server
uvicorn main:app --reload --port 8000
```
The interactive API documentation will be automatically available at `http://localhost:8000/docs`.

**Frontend Setup:**
Open a new terminal window and run:
```bash
cd frontend
npm install
npm start
```
The React application will open in your browser at `http://localhost:3000`.

### 2. Running with Docker (Production)

You can easily spin up the entire application stack using Docker Compose. Make sure Docker is running on your machine, then run:

```bash
docker compose up --build -d
```

- The React frontend will be built and served via a lightning-fast Nginx container on port `80` (`http://localhost`).
- The FastAPI backend will run on port `8000`.
- The local SQLite database (`letras.db`) is mounted as a volume to ensure data persistence.

To stop the containers, use:
```bash
docker compose down
```
