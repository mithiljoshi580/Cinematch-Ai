import sqlite3
import pandas as pd
import json

print("Reading TMDB CSV file...")
df = pd.read_csv('tmdb_5000_movies.csv')

conn = sqlite3.connect('movies.db')
cursor = conn.cursor()

# Database table create karna
cursor.execute('''
    CREATE TABLE IF NOT EXISTS movies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        genres TEXT,
        director TEXT,
        description TEXT,
        poster TEXT,
        year INTEGER,
        rating REAL
    )
''')

print("Processing and inserting movies...")
for index, row in df.iterrows():
    title = str(row.get('title', 'Unknown'))
    
    # TMDB genres JSON parse karna taaki genres names nikal sakein
    genres_json = row.get('genres', '[]')
    genres_list = []
    try:
        parsed = json.loads(genres_json)
        genres_list = [g['name'] for g in parsed]
    except:
        genres_list = ["Drama"]
    genres = ", ".join(genres_list)

    description = str(row.get('overview', ''))
    
    try:
        rating = float(row.get('vote_average', 7.0))
    except:
        rating = 7.0

    poster = f"https://picsum.photos/300/450?random={index}"
    year = 2020  # Default year agar na ho

    cursor.execute('''
        INSERT INTO movies (title, genres, director, description, poster, year, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, genres, "Unknown", description, poster, year, rating))

conn.commit()
conn.close()
print("🎉 Success! All 5000+ TMDB movies imported into movies.db!")