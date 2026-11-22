
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

import sqlite3
import pandas as pd
import os

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


# ==========================================
# 1. BASE DIRECTORY CONFIGURATION
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_DIR = os.path.join(BASE_DIR, "Templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")
DATABASE_PATH = os.path.join(BASE_DIR, "movies.db")


# ==========================================
# 2. FASTAPI APPLICATION
# ==========================================

app = FastAPI(
    title="CineMatch AI",
    description="AI-powered Movie Recommendation System",
    version="1.0.0"
)


# ==========================================
# 3. STATIC FILES CONFIGURATION
# ==========================================

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static"
)


# ==========================================
# 4. HTML TEMPLATES CONFIGURATION
# ==========================================

templates = Jinja2Templates(
    directory=TEMPLATE_DIR
)


# ==========================================
# 5. DATABASE CONNECTION
# ==========================================

def get_database_connection():
    if not os.path.exists(DATABASE_PATH):
        raise FileNotFoundError(
            f"Database not found: {DATABASE_PATH}"
        )

    return sqlite3.connect(
        f"file:{DATABASE_PATH}?mode=ro",
        uri=True
    )


# ==========================================
# 6. HOME PAGE ROUTE
# ==========================================

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):

    return templates.TemplateResponse(
        request,
        "index.html",
        {}
    )


# ==========================================
# 7. MOVIE RECOMMENDATION API
# ==========================================

@app.get("/api/recommend")
async def recommend_movies(title: str):

    try:

        # Validate input
        if not title or title.strip() == "":
            return JSONResponse({
                "recommendations": []
            })

        # Connect to SQLite database
        conn = get_database_connection()

        try:
            df = pd.read_sql_query(
                "SELECT * FROM movies",
                conn
            )
        finally:
            conn.close()

        # Validate database
        if df.empty or "title" not in df.columns:
            return JSONResponse({
                "recommendations": []
            })

        # Reset dataframe index
        df = df.reset_index(drop=True)

        # Handle missing columns
        for column in ["genres", "description"]:
            if column not in df.columns:
                df[column] = ""

            df[column] = df[column].fillna("").astype(str)

        # ======================================
        # FEATURE ENGINEERING
        # ======================================

        df["title"] = df["title"].fillna("").astype(str)

        df["combined_features"] = (
            df["title"] + " " +
            df["genres"] + " " +
            df["description"]
        )

        # ======================================
        # TF-IDF VECTORIZATION
        # ======================================

        vectorizer = TfidfVectorizer(
            stop_words="english"
        )

        tfidf_matrix = vectorizer.fit_transform(
            df["combined_features"]
        )

        # ======================================
        # COSINE SIMILARITY
        # ======================================

        cosine_sim = cosine_similarity(
            tfidf_matrix,
            tfidf_matrix
        )

        # ======================================
        # MOVIE SEARCH
        # ======================================

        df["title_lower"] = (
            df["title"].str.lower().str.strip()
        )

        search_title = title.lower().strip()

        matched_rows = df[
            df["title_lower"] == search_title
        ]

        if matched_rows.empty:

            matched_rows = df[
                df["title_lower"].str.contains(
                    search_title,
                    na=False,
                    regex=False
                )
            ]

        if matched_rows.empty:
            return JSONResponse({
                "recommendations": []
            })

        # Get matched movie index
        idx = matched_rows.index[0]

        # ======================================
        # GET TOP SIMILAR MOVIES
        # ======================================

        sim_scores = list(
            enumerate(cosine_sim[idx])
        )

        sim_scores = sorted(
            sim_scores,
            key=lambda x: x[1],
            reverse=True
        )

        # Exclude searched movie and get top 6
        sim_scores = sim_scores[1:7]

        movie_indices = [
            i[0] for i in sim_scores
        ]

        result_df = df.iloc[movie_indices]

        # ======================================
        # PREPARE RECOMMENDATION RESPONSE
        # ======================================

        recommendations = []

        for _, row in result_df.iterrows():

            year = row.get("year", 2020)
            rating = row.get("rating", 7.0)

            # Handle missing year and rating
            year = (
                2020 if pd.isna(year) else int(year)
            )

            rating = (
                7.0 if pd.isna(rating) else float(rating)
            )

            recommendations.append({

                "title": row.get(
                    "title", "Unknown"
                ),

                "year": year,

                "rating": rating,

                "genres": str(
                    row.get("genres", "")
                ),

                "director": str(
                    row.get("director", "Unknown")
                ),

                "description": str(
                    row.get("description", "")
                ),

                "poster": str(
                    row.get(
                        "poster",
                        "https://picsum.photos/300/450"
                    )
                )

            })

        return JSONResponse({
            "recommendations": recommendations
        })

    except Exception as e:

        print(
            f"CineMatch AI Error: {str(e)}"
        )

        return JSONResponse(
            {
                "recommendations": [],
                "error": str(e)
            },
            status_code=500
        )


# ==========================================
# 8. APPLICATION ENTRY POINT
# ==========================================

# Vercel will import the 'app' object directly.
# For local development, run:
# uvicorn main:app --reload
