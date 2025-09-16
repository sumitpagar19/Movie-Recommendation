from flask import Flask, render_template, request, jsonify
import pickle
import requests
import os
from werkzeug.exceptions import RequestEntityTooLarge

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Global variables to store loaded data
movies = None
similarity = None


def load_data():
    """Load pickle files on app startup"""
    global movies, similarity
    try:
        # Update these paths to match your pickle file locations
        movies = pickle.load(open("c:\Users\sumit\ml_projects\movie_recommendation\movie_list.pkl", 'rb'))
        similarity = pickle.load(open("c:\Users\sumit\ml_projects\movie_recommendation\similarity.pkl", 'rb'))
        print(f"Loaded {len(movies)} movies successfully!")
    except FileNotFoundError as e:
        print(f"Error loading pickle files: {e}")
        print("Make sure movie_list.pkl and similarity.pkl are in the same directory as this script")

import os
import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")

import os
import requests

def fetch_poster_and_rating(movie_id):
    """
    Fetch poster and rating from TMDB API using environment variable for API key.
    Returns a tuple: (poster_url, rating)
    """
    try:
        # Get API key from environment variable
        TMDB_API_KEY = os.getenv("TMDB_API_KEY")
        if not TMDB_API_KEY:
            raise ValueError("TMDB_API_KEY environment variable not set.")

        # Build URL
        url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&language=en-US"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Poster URL
        if data.get('poster_path'):
            full_path = "https://image.tmdb.org/t/p/w500/" + data['poster_path']
        else:
            full_path = "https://via.placeholder.com/500x750?text=No+Poster"

        # Rating
        rating = data.get('vote_average', 'N/A')

        return full_path, rating

    except requests.exceptions.RequestException as req_err:
        print(f"Request error for movie_id {movie_id}: {req_err}")
    except Exception as e:
        print(f"Error fetching data for movie_id {movie_id}: {e}")

    # Fallback values if error occurs
    return "https://via.placeholder.com/500x750?text=Error+Loading", "N/A"


def recommend(movie):
    """Generate movie recommendations"""
    try:
        # Find the movie in the dataset
        movie_matches = movies[movies['title'].str.contains(movie, case=False, na=False)]

        if movie_matches.empty:
            return [], [], []

        index = movie_matches.index[0]
        distances = sorted(list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1])

        recommended_movie_names = []
        recommended_movie_posters = []
        recommended_movie_ratings = []

        # Get top 5 recommendations (excluding the input movie itself)
        for i in distances[1:6]:
            movie_id = movies.iloc[i[0]].movie_id
            poster, rating = fetch_poster_and_rating(movie_id)
            recommended_movie_posters.append(poster)
            recommended_movie_names.append(movies.iloc[i[0]].title)
            recommended_movie_ratings.append(rating)

        return recommended_movie_names, recommended_movie_posters, recommended_movie_ratings
    except Exception as e:
        print(f"Error in recommend function: {e}")
        return [], [], []


@app.route('/')
def index():
    """Main page"""
    if movies is None:
        return render_template('error.html', error="Movie data not loaded. Please check pickle files.")
    return render_template('index.html')


@app.route('/api/movies')
def get_movies():
    """API endpoint to get all movie titles for autocomplete"""
    if movies is None:
        return jsonify({'error': 'Movie data not loaded'}), 500

    query = request.args.get('q', '').lower()
    if query:
        filtered_movies = movies[movies['title'].str.contains(query, case=False, na=False)]['title'].tolist()
        return jsonify(filtered_movies[:20])  # Limit to 20 results
    else:
        return jsonify(movies['title'].tolist()[:50])  # Return first 50 movies


@app.route('/api/recommend', methods=['POST'])
def get_recommendations():
    """API endpoint to get movie recommendations"""
    if movies is None or similarity is None:
        return jsonify({'error': 'Movie data not loaded'}), 500

    data = request.get_json()
    movie_name = data.get('movie', '')

    if not movie_name:
        return jsonify({'error': 'Movie name is required'}), 400

    names, posters, ratings = recommend(movie_name)

    recommendations = []
    for i in range(len(names)):
        recommendations.append({
            'title': names[i],
            'poster': posters[i],
            'rating': ratings[i]
        })

    return jsonify({
        'selected_movie': movie_name,
        'recommendations': recommendations
    })


# HTML Templates as strings
templates = {
    'index.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎬 CineAI - Movie Recommendation System</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Poppins', sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }

        /* Animated Background */
        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 20% 80%, rgba(120, 0, 255, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 80% 20%, rgba(0, 255, 255, 0.1) 0%, transparent 50%),
                        radial-gradient(circle at 40% 40%, rgba(255, 0, 150, 0.08) 0%, transparent 50%);
            z-index: -1;
            animation: backgroundShift 20s ease-in-out infinite;
        }

        @keyframes backgroundShift {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        /* Particle Effect */
        .particles {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            pointer-events: none;
            z-index: 0;
        }

        .particle {
            position: absolute;
            width: 2px;
            height: 2px;
            background: linear-gradient(45deg, #00ffff, #7b00ff);
            border-radius: 50%;
            animation: float 6s infinite linear;
        }

        @keyframes float {
            0% {
                transform: translateY(100vh) rotate(0deg);
                opacity: 0;
            }
            10% {
                opacity: 1;
            }
            90% {
                opacity: 1;
            }
            100% {
                transform: translateY(-10vh) rotate(360deg);
                opacity: 0;
            }
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 40px 20px;
            position: relative;
            z-index: 1;
        }

        /* Header */
        .header {
            text-align: center;
            margin-bottom: 80px;
            position: relative;
        }

        .header::before {
            content: '';
            position: absolute;
            top: -30px;
            left: 50%;
            transform: translateX(-50%);
            width: 120px;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            border-radius: 1px;
        }

        @keyframes pulse {
            0%, 100% { transform: translateX(-50%) scaleX(1); }
            50% { transform: translateX(-50%) scaleX(1.2); }
        }

        .header h1 {
            font-size: 4.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #e8e8e8 0%, #ffffff 50%, #f0f0f0 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 20px;
            text-shadow: 0 0 30px rgba(255, 255, 255, 0.1);
            letter-spacing: -1px;
        }

        @keyframes textGlow {
            0% { filter: drop-shadow(0 0 10px rgba(0, 255, 255, 0.5)); }
            100% { filter: drop-shadow(0 0 30px rgba(123, 0, 255, 0.7)); }
        }

        .header p {
            color: #a0a0a0;
            font-size: 1.4rem;
            font-weight: 300;
            max-width: 600px;
            margin: 0 auto;
            line-height: 1.6;
        }

        /* Search Section */
        .search-section {
            margin-bottom: 80px;
            position: relative;
        }

        .search-container {
            max-width: 800px;
            margin: 0 auto;
            position: relative;
        }

        .search-wrapper {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.05) 0%, rgba(0, 0, 0, 0.3) 100%);
            border-radius: 30px;
            padding: 8px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            box-shadow: 
                0 20px 40px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            position: relative;
            overflow: hidden;
        }

        .search-wrapper::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.1), transparent);
            transition: left 1s ease;
        }

        .search-wrapper:hover::before {
            left: 100%;
        }

        .search-input {
            width: 100%;
            padding: 25px 30px;
            font-size: 1.3rem;
            border: none;
            border-radius: 25px;
            outline: none;
            background: rgba(0, 0, 0, 0.3);
            color: #ffffff;
            font-family: 'Poppins', sans-serif;
            font-weight: 400;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        }

        .search-input::placeholder {
            color: #666;
        }

        .search-input:focus {
            background: rgba(0, 0, 0, 0.5);
            box-shadow: 
                0 0 0 2px rgba(0, 255, 255, 0.4),
                0 0 40px rgba(0, 255, 255, 0.2),
                inset 0 0 20px rgba(0, 255, 255, 0.05);
            transform: scale(1.02);
        }

        .dropdown {
            position: absolute;
            top: 100%;
            left: 8px;
            right: 8px;
            background: rgba(0, 0, 0, 0.9);
            border: 1px solid rgba(0, 255, 255, 0.2);
            border-radius: 20px;
            max-height: 300px;
            overflow-y: auto;
            z-index: 1000;
            display: none;
            backdrop-filter: blur(20px);
            margin-top: 10px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.6);
        }

        .dropdown-item {
            padding: 18px 25px;
            cursor: pointer;
            border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.3s ease;
            color: #ccc;
            font-weight: 400;
            position: relative;
            overflow: hidden;
        }

        .dropdown-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.1), transparent);
            transition: left 0.3s ease;
        }

        .dropdown-item:hover {
            background: rgba(255, 255, 255, 0.08);
            color: #ffffff;
            transform: translateX(8px);
            border-left: 2px solid rgba(255, 255, 255, 0.3);
        }

        .dropdown-item:hover::before {
            left: 0;
        }

        .dropdown-item:last-child {
            border-bottom: none;
        }

        .recommend-btn {
            display: block;
            margin: 40px auto 0;
            padding: 18px 48px;
            font-size: 1.1rem;
            font-weight: 500;
            background: rgba(255, 255, 255, 0.08);
            color: #ffffff;
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 12px;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            font-family: 'Poppins', sans-serif;
            backdrop-filter: blur(10px);
            position: relative;
            overflow: hidden;
            text-transform: none;
            letter-spacing: 0.5px;
        }

        .recommend-btn::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.6s;
        }

        .recommend-btn:hover {
            background: rgba(255, 255, 255, 0.12);
            border-color: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 
                0 8px 25px rgba(0, 0, 0, 0.3),
                0 0 0 1px rgba(255, 255, 255, 0.1);
        }

        .recommend-btn:hover::before {
            left: 100%;
        }

        .recommend-btn:disabled {
            opacity: 0.7;
            cursor: not-allowed;
            transform: none;
        }

        /* Selected Movie */
        .selected-movie {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 30px;
            border-radius: 16px;
            margin: 40px 0;
            text-align: center;
            display: none;
            backdrop-filter: blur(20px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .selected-movie h3 {
            color: rgba(255, 255, 255, 0.7);
            margin-bottom: 15px;
            font-weight: 500;
            font-size: 1.2rem;
        }

        .selected-movie p {
            color: #ffffff;
            font-size: 1.2rem;
            font-weight: 500;
        }

        /* Recommendations Grid */
        .recommendations {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 40px;
            margin-top: 80px;
        }

        .movie-card {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.03), rgba(0, 0, 0, 0.3));
            border-radius: 25px;
            padding: 25px;
            text-align: center;
            border: 1px solid rgba(255, 255, 255, 0.05);
            transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            backdrop-filter: blur(10px);
        }

        .movie-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
            transform: scaleX(0);
            transition: transform 0.5s ease;
        }

        .movie-card::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at center, rgba(255, 255, 255, 0.02) 0%, transparent 70%);
            opacity: 0;
            transition: opacity 0.5s ease;
        }

        .movie-card:hover {
            transform: translateY(-8px);
            box-shadow: 
                0 20px 40px rgba(0, 0, 0, 0.4),
                0 0 0 1px rgba(255, 255, 255, 0.1);
        }

        .movie-card:hover::before {
            transform: scaleX(1);
        }

        .movie-card:hover::after {
            opacity: 1;
        }

        .movie-poster {
            width: 100%;
            height: 350px;
            object-fit: cover;
            border-radius: 20px;
            margin-bottom: 25px;
            transition: all 0.5s ease;
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.4);
        }

        .movie-card:hover .movie-poster {
            transform: scale(1.02);
            box-shadow: 0 15px 35px rgba(0, 0, 0, 0.5);
        }

        .movie-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #ffffff;
            margin-bottom: 15px;
            line-height: 1.4;
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .movie-rating {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
            font-size: 1.2rem;
            font-weight: 600;
        }

        .rating-star {
            color: #ffd700;
            filter: none;
            animation: none;
        }

        .rating-value {
            color: rgba(255, 255, 255, 0.9);
            text-shadow: none;
        }

        @keyframes starTwinkle {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.2); }
        }

        /* Loading */
        .loading {
            text-align: center;
            padding: 80px;
            display: none;
        }

        .spinner {
            width: 40px;
            height: 40px;
            border: 3px solid rgba(255, 255, 255, 0.1);
            border-top: 3px solid rgba(255, 255, 255, 0.6);
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 30px;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        .loading p {
            font-size: 1.4rem;
            color: #a0a0a0;
            font-weight: 500;
        }

        /* Error Message */
        .error-message {
            background: rgba(220, 38, 38, 0.1);
            border: 1px solid rgba(220, 38, 38, 0.3);
            color: #fca5a5;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            margin: 30px 0;
            display: none;
            backdrop-filter: blur(20px);
            font-weight: 400;
        }

        /* Responsive */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }

            .container {
                padding: 20px 15px;
            }

            .header h1 {
                font-size: 3rem;
            }

            .header p {
                font-size: 1.1rem;
            }

            .search-input {
                padding: 20px 25px;
                font-size: 1.1rem;
            }

            .recommend-btn {
                padding: 18px 40px;
                font-size: 1.1rem;
            }

            .recommendations {
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 30px;
            }

            .movie-poster {
                height: 300px;
            }
        }

        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 10px;
        }

        ::-webkit-scrollbar-track {
            background: rgba(255, 255, 255, 0.05);
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.3), rgba(255, 255, 255, 0.1));
            border-radius: 10px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.4), rgba(255, 255, 255, 0.2));
        }
    </style>
</head>
<body>
    <div class="particles" id="particles"></div>

    <div class="container">
        <div class="header">
            <h1>CineAI</h1>
            <p>Discover your next cinematic adventure with AI-powered recommendations tailored just for you</p>
        </div>

        <div class="search-section">
            <div class="search-container">
                <div class="search-wrapper">
                    <input type="text" 
                           id="movieSearch" 
                           class="search-input" 
                           placeholder="Search for your favorite movie..."
                           autocomplete="off">
                </div>
                <div id="dropdown" class="dropdown"></div>
            </div>
            <button id="recommendBtn" class="recommend-btn">
                Get Recommendations
            </button>
        </div>

        <div id="selectedMovie" class="selected-movie">
            <h3>Selected Movie:</h3>
            <p id="selectedMovieTitle"></p>
        </div>

        <div id="errorMessage" class="error-message"></div>

        <div id="loading" class="loading">
            <div class="spinner"></div>
            <p>Analyzing your preferences and finding perfect matches...</p>
        </div>

        <div id="recommendations" class="recommendations"></div>
    </div>

    <script>
        // Create floating particles
        function createParticles() {
            const particlesContainer = document.getElementById('particles');
            const numberOfParticles = 50;

            for (let i = 0; i < numberOfParticles; i++) {
                const particle = document.createElement('div');
                particle.className = 'particle';
                particle.style.left = Math.random() * 100 + '%';
                particle.style.animationDelay = Math.random() * 6 + 's';
                particle.style.animationDuration = (Math.random() * 4 + 4) + 's';
                particlesContainer.appendChild(particle);
            }
        }

        let allMovies = [];
        let selectedMovie = '';

        async function loadMovies() {
            try {
                const response = await fetch('/api/movies');
                allMovies = await response.json();
                console.log('Movies loaded successfully');
            } catch (error) {
                showError('Failed to load movie database');
                console.error('Error loading movies:', error);
            }
        }

        const searchInput = document.getElementById('movieSearch');
        const dropdown = document.getElementById('dropdown');

        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase().trim();
            if (query.length === 0) {
                dropdown.style.display = 'none';
                return;
            }

            const filtered = allMovies.filter(movie => 
                movie.toLowerCase().includes(query)
            ).slice(0, 12);

            if (filtered.length > 0) {
                dropdown.innerHTML = filtered.map(movie => 
                    `<div class="dropdown-item" onclick="selectMovie('${movie.replace(/'/g, "\\\'")}')">
                        ${movie}
                    </div>`
                ).join('');
                dropdown.style.display = 'block';
            } else {
                dropdown.innerHTML = '<div class="dropdown-item" style="color: #666; cursor: default;">No movies found</div>';
                dropdown.style.display = 'block';
            }
        });

        document.addEventListener('click', function(event) {
            if (!searchInput.contains(event.target) && !dropdown.contains(event.target)) {
                dropdown.style.display = 'none';
            }
        });

        function selectMovie(movie) {
            selectedMovie = movie;
            searchInput.value = movie;
            dropdown.style.display = 'none';

            const selectedDiv = document.getElementById('selectedMovie');
            document.getElementById('selectedMovieTitle').textContent = movie;
            selectedDiv.style.display = 'block';

            // Smooth animation
            selectedDiv.style.transform = 'scale(0.9) translateY(20px)';
            selectedDiv.style.opacity = '0';
            setTimeout(() => {
                selectedDiv.style.transition = 'all 0.5s ease';
                selectedDiv.style.transform = 'scale(1) translateY(0)';
                selectedDiv.style.opacity = '1';
            }, 100);
        }

        document.getElementById('recommendBtn').addEventListener('click', async function() {
            const movieToRecommend = selectedMovie || searchInput.value.trim();

            if (!movieToRecommend) {
                showError('Please select a movie first to get personalized recommendations');
                return;
            }

            await getRecommendations(movieToRecommend);
        });

        async function getRecommendations(movie) {
            const loading = document.getElementById('loading');
            const recommendations = document.getElementById('recommendations');
            const recommendBtn = document.getElementById('recommendBtn');

            loading.style.display = 'block';
            recommendations.innerHTML = '';
            recommendBtn.disabled = true;
            recommendBtn.textContent = 'Analyzing Your Taste...';
            hideError();

            try {
                const response = await fetch('/api/recommend', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ movie: movie })
                });

                const data = await response.json();

                if (data.error) {
                    throw new Error(data.error);
                }

                loading.style.display = 'none';

                if (data.recommendations && data.recommendations.length > 0) {
                    recommendations.innerHTML = data.recommendations.map((movie, index) => `
                        <div class="movie-card" style="animation-delay: ${index * 0.15}s; opacity: 0;">
                            <img src="${movie.poster}" alt="${movie.title}" class="movie-poster" 
                                 onerror="this.src='https://via.placeholder.com/500x750/1a1a1a/ffffff?text=${encodeURIComponent(movie.title)}'">
                            <div class="movie-title">${movie.title}</div>
                            <div class="movie-rating">
                                <span class="rating-star">⭐</span>
                                <span class="rating-value">${movie.rating}/10</span>
                            </div>
                        </div>
                    `).join('');

                    // Animate cards in
                    const cards = recommendations.querySelectorAll('.movie-card');
                    cards.forEach((card, index) => {
                        setTimeout(() => {
                            card.style.animation = 'fadeInUp 0.8s ease forwards';
                        }, index * 100);
                    });
                } else {
                    recommendations.innerHTML = `
                        <div style="text-align: center; color: #666; grid-column: 1/-1; padding: 60px;">
                            <div style="font-size: 4rem; margin-bottom: 20px;">🤔</div>
                            <h3 style="color: #fff; margin-bottom: 10px;">No recommendations found</h3>
                            <p>Try searching for a different movie or check the spelling!</p>
                        </div>`;
                }

            } catch (error) {
                loading.style.display = 'none';
                showError('Failed to get recommendations: ' + error.message);
                console.error('Recommendation error:', error);
            } finally {
                recommendBtn.disabled = false;
                recommendBtn.innerHTML = 'Get Recommendations';
            }
        }

        function showError(message) {
            const errorDiv = document.getElementById('errorMessage');
            errorDiv.innerHTML = message;
            errorDiv.style.display = 'block';

            // Shake animation
            errorDiv.style.animation = 'shake 0.6s ease-in-out';
            setTimeout(() => {
                errorDiv.style.animation = '';
            }, 600);
        }

        function hideError() {
            document.getElementById('errorMessage').style.display = 'none';
        }

        // Add CSS animations
        const style = document.createElement('style');
        style.textContent = `
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
                20%, 40%, 60%, 80% { transform: translateX(5px); }
            }

            @keyframes fadeInUp {
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            .movie-card {
                transform: translateY(30px);
            }

            /* Glow effect for selected movie */
            .selected-movie {
                animation: none;
            }

            /* Button loading state */
            .recommend-btn:disabled {
                background: rgba(255, 255, 255, 0.05);
                color: #999;
                border-color: rgba(255, 255, 255, 0.1);
                animation: buttonPulse 2s ease-in-out infinite;
            }

            @keyframes buttonPulse {
                0%, 100% { opacity: 0.7; }
                50% { opacity: 1; }
            }
        `;
        document.head.appendChild(style);

        // Initialize
        createParticles();
        loadMovies();

        // Add keyboard support
        searchInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter') {
                const movieToRecommend = selectedMovie || searchInput.value.trim();
                if (movieToRecommend) {
                    getRecommendations(movieToRecommend);
                }
            }
        });

        // Add smooth scroll to results
        function scrollToResults() {
            const recommendations = document.getElementById('recommendations');
            if (recommendations.children.length > 0) {
                recommendations.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'start' 
                });
            }
        }

        // Auto-scroll when recommendations are loaded
        const originalGetRecommendations = getRecommendations;
        getRecommendations = async function(movie) {
            await originalGetRecommendations(movie);
            setTimeout(scrollToResults, 1000);
        };
    </script>
</body>
</html>''',

    'error.html': '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Error - CineAI</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Poppins', sans-serif;
            background: #0a0a0a;
            color: #ffffff;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            position: relative;
            overflow: hidden;
        }

        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle at 30% 70%, rgba(255, 0, 100, 0.15) 0%, transparent 50%),
                        radial-gradient(circle at 70% 30%, rgba(0, 255, 255, 0.15) 0%, transparent 50%);
            z-index: -1;
        }

        .error-container {
            background: linear-gradient(145deg, rgba(255, 255, 255, 0.05), rgba(0, 0, 0, 0.3));
            padding: 60px 50px;
            border-radius: 30px;
            text-align: center;
            box-shadow: 
                0 30px 60px rgba(0, 0, 0, 0.5),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            max-width: 600px;
            position: relative;
            animation: errorFloat 3s ease-in-out infinite;
        }

        @keyframes errorFloat {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
        }

        .error-icon {
            font-size: 5rem;
            margin-bottom: 30px;
            animation: errorPulse 2s ease-in-out infinite;
        }

        @keyframes errorPulse {
            0%, 100% { transform: scale(1); filter: drop-shadow(0 0 10px rgba(255, 0, 100, 0.5)); }
            50% { transform: scale(1.1); filter: drop-shadow(0 0 20px rgba(255, 0, 100, 0.8)); }
        }

        h1 {
            color: #ff0064;
            margin-bottom: 25px;
            font-size: 2.5rem;
            font-weight: 700;
            text-shadow: 0 0 20px rgba(255, 0, 100, 0.3);
        }

        p {
            color: #a0a0a0;
            line-height: 1.8;
            margin-bottom: 20px;
            font-size: 1.1rem;
        }

        .error-details {
            background: rgba(255, 0, 100, 0.1);
            border: 1px solid rgba(255, 0, 100, 0.3);
            padding: 25px;
            border-radius: 15px;
            margin: 30px 0;
            color: #ff6b9d;
        }

        ul {
            text-align: left;
            color: #ccc;
            margin: 20px 0;
            padding-left: 20px;
        }

        li {
            margin: 10px 0;
            line-height: 1.6;
        }

        .back-btn {
            display: inline-block;
            margin-top: 30px;
            padding: 15px 40px;
            background: linear-gradient(135deg, #00ffff 0%, #ff0064 100%);
            color: #000;
            text-decoration: none;
            border-radius: 25px;
            font-weight: 600;
            transition: all 0.3s ease;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .back-btn:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(0, 255, 255, 0.4);
        }
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <h1>System Error</h1>
        <div class="error-details">
            <p><strong>{{ error }}</strong></p>
        </div>

        <p><strong>Please make sure:</strong></p>
        <ul>
            <li>movie_list.pkl and similarity.pkl files are in the same directory as app.py</li>
            <li>The pickle files contain the correct data structure</li>
            <li>You have an active internet connection for movie posters</li>
            <li>All required Python packages are installed</li>
        </ul>

        <a href="javascript:window.location.reload()" class="back-btn">🔄 Retry</a>
    </div>
</body>
</html>'''
}


def create_templates():
    """Create templates directory and save HTML files"""
    import os
    if not os.path.exists('templates'):
        os.makedirs('templates')

    for filename, content in templates.items():
        with open(f'templates/{filename}', 'w', encoding='utf-8') as f:
            f.write(content)


if __name__ == '__main__':
    # Create templates directory and files
    create_templates()

    # Load data on startup
    load_data()

    print("🎬 CineAI Movie Recommendation System")
    print("=" * 60)
    print("🚀 Starting Flask server with modern black design...")
    print("📋 Requirements checklist:")
    print("   ✓ movie_list.pkl")
    print("   ✓ similarity.pkl")
    print("   ✓ Active internet connection")
    print("=" * 60)
    print("🌐 Server will start at: http://localhost:5000")
    print("🎨 New Features:")
    print("   • Modern black theme with neon accents")
    print("   • Animated particle background")
    print("   • Smooth hover effects and transitions")
    print("   • Enhanced visual feedback")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)