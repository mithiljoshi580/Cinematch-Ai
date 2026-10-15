from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = FastAPI()

# Static files (CSS/JS) mount karna
app.mount("/static", StaticFiles(directory="static"), name="static")

# HTML templates setup (Folder ka naam Templates hai)
templates = Jinja2Templates(directory="Templates")

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse(request, "index.html", {})

@app.get("/api/recommend")
async def recommend_movies(title: str):
    try:
        if not title or title.strip() == "":
            return JSONResponse({"recommendations": []})
            
        conn = sqlite3.connect('movies.db')
        df = pd.read_sql_query("SELECT * FROM movies", conn)
        conn.close()

        if df.empty or 'title' not in df.columns:
            return JSONResponse({"recommendations": []})

        df['genres'] = df['genres'].fillna('')
        df['description'] = df['description'].fillna('')
        df['combined_features'] = df['title'] + " " + df['genres'] + " " + df['description']
        
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(df['combined_features'])
        cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
        
        df['title_lower'] = df['title'].str.lower().str.strip()
        search_title = title.lower().strip()
        
        matched_rows = df[df['title_lower'] == search_title]
        if matched_rows.empty:
            matched_rows = df[df['title_lower'].str.contains(search_title, na=False)]
            
        if matched_rows.empty:
            return JSONResponse({"recommendations": []})
            
        idx = matched_rows.index[0]
        sim_scores = list(enumerate(cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:7]
        
        movie_indices = [i[0] for i in sim_scores]
        result_df = df.iloc[movie_indices]
        
        recommendations = []
        for _, row in result_df.iterrows():
            recommendations.append({
                "title": row.get('title', 'Unknown'),
                "year": int(row.get('year', 2020)),
                "rating": float(row.get('rating', 7.0)),
                "genres": str(row.get('genres', '')),
                "director": str(row.get('director', 'Unknown')),
                "description": str(row.get('description', '')),
                "poster": str(row.get('poster', 'https://picsum.photos/300/450'))
            })
            
        return JSONResponse({"recommendations": recommendations})
    except Exception as e:
        print("Error:", e)
        return JSONResponse({"recommendations": []})