from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sqlite3
from typing import List, Optional

app = FastAPI(title="Cenidim API", description="API para consulta de letras de canciones")

# Habilitar CORS para que el frontend pueda consultar sin problemas
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción cambiar esto a los dominios específicos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "letras.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row # Para devolver diccionarios
    return conn

# Modelos de respuesta
class Song(BaseModel):
    id: int
    title: str
    album: str
    filename: str

class SongDetail(Song):
    lyrics: str

@app.get("/")
def read_root():
    return {"message": "Bienvenido a la API del Cenidim. Las rutas disponibles son /search y /song/{id}"}

@app.get("/api/search", response_model=List[Song])
def search_songs(
    query: str = "",
    field: Optional[str] = "all"
):
    """
    Busca canciones en la base de datos.
    - query: El texto a buscar.
    - field: El campo donde buscar ("title", "album", "lyrics", o "all").
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Preparamos la búsqueda con LIKE
    search_term = f"%{query}%"
    
    # Consulta base haciendo JOIN entre songs y albums
    base_query = """
        SELECT s.id, s.title, a.name as album, s.filename
        FROM songs s
        JOIN albums a ON s.album_id = a.id
    """
    
    if query:
        if field == "title":
            cursor.execute(base_query + " WHERE s.title LIKE ?", (search_term,))
        elif field == "album":
            cursor.execute(base_query + " WHERE a.name LIKE ?", (search_term,))
        elif field == "lyrics":
            # No devolvemos las lyrics en la búsqueda para que sea rápida, pero filtramos por ellas
            cursor.execute(base_query + " WHERE s.lyrics LIKE ?", (search_term,))
        else: # "all"
            cursor.execute(
                base_query + " WHERE s.title LIKE ? OR a.name LIKE ? OR s.lyrics LIKE ?",
                (search_term, search_term, search_term)
            )
    else:
        # Si no hay query, devolvemos todo (con un límite para no saturar)
        cursor.execute(base_query + " LIMIT 100")
        
    results = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in results]

@app.get("/api/song/{song_id}", response_model=SongDetail)
def get_song(song_id: int):
    """Obtiene el detalle completo y la letra de una canción por su ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT s.id, s.title, a.name as album, s.filename, s.lyrics
        FROM songs s
        JOIN albums a ON s.album_id = a.id
        WHERE s.id = ?
    """, (song_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row is None:
        raise HTTPException(status_code=404, detail="Canción no encontrada")
        
    return dict(row)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
