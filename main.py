from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import requests
from typing import List


movie_df = pickle.load(open("movie_df.pkl", "rb"))
movie_similarity_df = pickle.load(open("movie_similarity_df.pkl", "rb"))
restricted_movies = pickle.load(open("restricted_movies.pkl", "rb"))


app = FastAPI()

def fetch_movie_poster(movie_id):
    api_key = "291596fc4042cc91839854d0a821c41f"
    base_url = "https://api.themoviedb.org/3/movie/"
    poster_base_url = "https://image.tmdb.org/t/p/w500"

    url = f"{base_url}{movie_id}?api_key={api_key}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        poster_path = data.get("poster_path")
        if poster_path:
            return f"{poster_base_url}{poster_path}"
        else:
            return None
    else:
        print(f"Error: Unable to fetch details for movie ID {movie_id}.")
        return None


def recommend(movie_name: str, rating: float):
    if movie_name not in movie_similarity_df.columns:
        raise ValueError("Movie not found in the dataset.")

    similar_score = movie_similarity_df[movie_name] * (rating - 2.5)
    similar_score = similar_score.sort_values(ascending=False)
    similar_score = list(similar_score.index)

    list1 = list(restricted_movies["title"])
    movieList = []
    posterList = []
    count = 1

    for i in similar_score:
        if i in list1 and count < 7:
            mid = restricted_movies.loc[restricted_movies["title"] == i].movie_id.values[0]
            movieList.append(i)
            posterList.append(fetch_movie_poster(mid))
            count += 1

    return movieList[1:6], posterList[1:6]


class RecommendationRequest(BaseModel):
    movie_name: str
    rating: float


@app.get("/")
def root():
    return {"message": "Welcome to the Collaborative Filtering Movie Recommendation API!"}

@app.post("/recommend")
def get_recommendations(request: RecommendationRequest):
    try:
        movie_name = request.movie_name
        rating = request.rating

        if not (0 <= rating <= 5):
            raise HTTPException(status_code=400, detail="Rating must be between 0 and 5.")

        movieList, posterList = recommend(movie_name, rating)
        recommendations = [
            {"title": movie, "poster_url": poster}
            for movie, poster in zip(movieList, posterList)
        ]

        return {"recommendations": recommendations}

    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
