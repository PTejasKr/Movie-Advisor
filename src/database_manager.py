"""
Database manager for the movie advisor
"""
import sqlite3
import os
from typing import List, Dict


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.ensure_database_exists()
    
    def ensure_database_exists(self):
        """Create database and required tables if they don't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create movies table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                release_year TEXT,
                genres TEXT,
                director TEXT,
                stars TEXT,
                keywords TEXT,
                rating REAL,
                rating_count INTEGER,
                final_score REAL,
                UNIQUE(title, release_year)
            )
        ''')
        
        # Create indexes for faster searches
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_title ON movies(title)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_genres ON movies(genres)')
        
        conn.commit()
        conn.close()
    
    def add_movie(self, movie_data: Dict):
        """Add a single movie to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO movies 
                (title, release_year, genres, director, stars, keywords, rating, rating_count, final_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                movie_data.get('title', ''),
                movie_data.get('release_year', ''),
                movie_data.get('genres', ''),
                movie_data.get('director', ''),
                movie_data.get('stars', ''),
                movie_data.get('keywords', ''),
                movie_data.get('rating', 0.0),
                movie_data.get('rating_count', 0),
                movie_data.get('final_score', 0.0)
            ))
            
            conn.commit()
            return cursor.rowcount > 0  # Returns True if a new movie was added
            
        except sqlite3.Error as e:
            print(f"Database error when adding movie: {e}")
            return False
        finally:
            conn.close()
    
    def add_movies(self, movies: List[Dict]):
        """Add multiple movies to the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        added_count = 0
        for movie in movies:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO movies 
                    (title, release_year, genres, director, stars, keywords, rating, rating_count, final_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    movie.get('title', ''),
                    movie.get('release_year', ''),
                    movie.get('genres', ''),
                    movie.get('director', ''),
                    movie.get('stars', ''),
                    movie.get('keywords', ''),
                    movie.get('rating', 0.0),
                    movie.get('rating_count', 0),
                    movie.get('final_score', 0.0)
                ))
                
                if cursor.rowcount > 0:
                    added_count += 1
                    
            except sqlite3.Error as e:
                print(f"Database error when adding movie {movie.get('title', '')}: {e}")
        
        conn.commit()
        conn.close()
        
        return added_count
    
    def search_movie_by_title(self, title: str) -> List[Dict]:
        """Search for movies by title (case-insensitive partial match)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, release_year, genres, director, stars, keywords, rating
            FROM movies 
            WHERE LOWER(title) LIKE LOWER(?)
            ORDER BY rating DESC
            LIMIT 10
        ''', (f'%{title}%',))
        
        results = cursor.fetchall()
        conn.close()
        
        movies = []
        for row in results:
            movie = {
                'title': row[0],
                'release_year': row[1],
                'genres': row[2],
                'director': row[3],
                'stars': row[4],
                'keywords': row[5],
                'rating': row[6]
            }
            movies.append(movie)
        
        return movies
    
    def get_movie_by_title_exact(self, title: str) -> Dict:
        """Get a movie by exact title match"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, release_year, genres, director, stars, keywords, rating
            FROM movies 
            WHERE LOWER(title) = LOWER(?)
            LIMIT 1
        ''', (title,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return {
                'title': result[0],
                'release_year': result[1],
                'genres': result[2],
                'director': result[3],
                'stars': result[4],
                'keywords': result[5],
                'rating': result[6]
            }
        
        return {}
    
    def get_all_movies(self) -> List[Dict]:
        """Get all movies from the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, release_year, genres, director, stars, keywords, rating
            FROM movies
            ORDER BY rating DESC
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        movies = []
        for row in results:
            movie = {
                'title': row[0],
                'release_year': row[1],
                'genres': row[2],
                'director': row[3],
                'stars': row[4],
                'keywords': row[5],
                'rating': row[6]
            }
            movies.append(movie)
        
        return movies
    
    def get_similar_movies(self, target_genres: str, exclude_title: str, limit: int = 5) -> List[Dict]:
        """Find movies similar to the target genres, excluding the specified title"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Split genres and search for movies containing any of these genres
        genre_list = [g.strip().lower() for g in target_genres.split(',') if g.strip()]
        
        # Construct the query to match any of the genres
        genre_conditions = " OR ".join(["LOWER(genres) LIKE ?" for _ in genre_list])
        params = [f"%{genre}%" for genre in genre_list] + [exclude_title.lower()]
        
        query = f'''
            SELECT title, release_year, genres, director, stars, keywords, rating
            FROM movies 
            WHERE ({genre_conditions})
            AND LOWER(title) != ?
            ORDER BY rating DESC
            LIMIT ?
        '''
        params.append(str(limit))
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        movies = []
        for row in results:
            movie = {
                'title': row[0],
                'release_year': row[1],
                'genres': row[2],
                'director': row[3],
                'stars': row[4],
                'keywords': row[5],
                'rating': row[6]
            }
            movies.append(movie)
        
        return movies