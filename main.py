import pickle
import streamlit as st
import requests


# function to fetch poster and rating
def fetch_poster_and_rating(movie_id):
    url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key=0b1a9dca42a4f7ec4785c488330ab2e8&language=en-US"
    data = requests.get(url).json()
    poster_path = data['poster_path']
    full_path = "https://image.tmdb.org/t/p/w500/" + poster_path
    rating = data.get('vote_average', 'N/A')  # TMDB rating
    return full_path, rating


# recommend function
def recommend(movie):
    index = movies[movies['title'] == movie].index[0]
    distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])
    recommended_movie_names = []
    recommended_movie_posters = []
    recommended_movie_ratings = []

    for i in distances[1:6]:
        movie_id = movies.iloc[i[0]].movie_id
        poster, rating = fetch_poster_and_rating(movie_id)
        recommended_movie_posters.append(poster)
        recommended_movie_names.append(movies.iloc[i[0]].title)
        recommended_movie_ratings.append(rating)

    return recommended_movie_names, recommended_movie_posters, recommended_movie_ratings


# Streamlit UI
st.header('🎬 Movie Recommendation System')

movies = pickle.load(open(r"C:\Users\sumit\ml_projects\movie_list.pkl", 'rb'))
similarity = pickle.load(open(r"C:\Users\sumit\ml_projects\similarity.pkl", 'rb'))

movie_list = movies['title'].values
selected_movie = st.selectbox(
    "Type or select a movie from the dropdown",
    movie_list
)

if st.button('Show Recommendation'):
    recommended_movie_names, recommended_movie_posters, recommended_movie_ratings = recommend(selected_movie)
    cols = st.columns(5)
    for i, col in enumerate(cols):
        with col:
            st.text(recommended_movie_names[i])
            st.image(recommended_movie_posters[i])
            st.write("⭐ Rating:", recommended_movie_ratings[i])
