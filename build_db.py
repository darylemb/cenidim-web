import os
import sqlite3

BASE_DIR = 'LetrasTXT'
DB_PATH = 'letras.db'

def create_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Album table
    cursor.execute('''
        CREATE TABLE albums (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')
    
    # Song table
    cursor.execute('''
        CREATE TABLE songs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            album_id INTEGER,
            title TEXT NOT NULL,
            filename TEXT,
            lyrics TEXT,
            FOREIGN KEY (album_id) REFERENCES albums(id)
        )
    ''')
    
    conn.commit()
    return conn

def populate_db(conn):
    cursor = conn.cursor()
    
    # Iterate over folders (albums)
    for album_name in sorted(os.listdir(BASE_DIR)):
        album_path = os.path.join(BASE_DIR, album_name)
        
        # Skip if not a directory
        if not os.path.isdir(album_path):
            continue
            
        # Insert album (if not exists) and get its ID
        cursor.execute("INSERT OR IGNORE INTO albums (name) VALUES (?)", (album_name,))
        cursor.execute("SELECT id FROM albums WHERE name = ?", (album_name,))
        album_id = cursor.fetchone()[0]
        
        # Iterate over files txt (songs)
        for filename in sorted(os.listdir(album_path)):
            if not filename.endswith('.txt'):
                continue
                
            file_path = os.path.join(album_path, filename)
            

            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
                
            if not lines:
                continue
                
            # First line is the title
            title = lines[0].strip()
            
            # The rest is the lyrics (and additional metadata that we saw at the end of the files)
            lyrics = "".join(lines[1:]).strip()
            
            cursor.execute('''
                INSERT INTO songs (album_id, title, filename, lyrics)
                VALUES (?, ?, ?, ?)
            ''', (album_id, title, filename, lyrics))
            
    conn.commit()
    
if __name__ == '__main__':
    print("Creating SQLite database and building tables...")
    conn = create_db()
    
    print("Processing files...")
    populate_db(conn)
    
    # Check how many records were inserted
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM albums")
    num_albums = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM songs")
    num_songs = cursor.fetchone()[0]
    
    conn.close()
    
    print(f"Database built successfully in '{DB_PATH}'!")
    print(f"Summary: {num_albums} Albums and {num_songs} Songs inserted.")
