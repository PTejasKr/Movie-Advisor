"""
Movie similarity engine
"""
import sqlite3
import re
import sys
import os
from typing import List, Dict
from difflib import SequenceMatcher

# Add the parent directory to the path if needed
current_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)


class MovieSimilarityEngine:
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def find_similar_movies_by_title(self, target_title: str, limit: int = 5) -> List[Dict]:
        """
        Find similar movies based on the provided title
        """
        # First try to find the target movie in the database
        target_movie = self.get_movie_by_title(target_title)
        
        if not target_movie:
            # If exact match not found, try fuzzy matching
            possible_matches = self.search_movies_fuzzy(target_title)
            if possible_matches:
                # Use the first result as the target
                target_movie = possible_matches[0]
            else:
                return []
        
        # Now find movies similar to the target movie's genres
        similar_movies = self.get_similar_movies_by_genres(
            target_movie['genres'], 
            target_movie['title'], 
            limit
        )
        
        return similar_movies
    
    def get_movie_by_title(self, title: str) -> Dict:
        """Get a movie by exact or partial title match"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Try exact match first
        cursor.execute('''
            SELECT title, release_year, genres, director, stars, keywords, rating, final_score
            FROM Movies_sorted 
            WHERE LOWER(title) = LOWER(?)
            LIMIT 1
        ''', (title,))
        
        result = cursor.fetchone()
        
        if not result:
            # Try case-insensitive partial match
            cursor.execute('''
                SELECT title, release_year, genres, director, stars, keywords, rating, final_score
                FROM Movies_sorted 
                WHERE LOWER(title) LIKE LOWER(?)
                LIMIT 1
            ''', (f'%{title}%',))
            
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
                'rating': result[6],
                'final_score': result[7]
            }
        
        return {}
    
    def search_movies_fuzzy(self, title: str, limit: int = 5) -> List[Dict]:
        """Find movies using fuzzy string matching"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT title, release_year, genres, director, stars, keywords, rating, final_score
            FROM Movies_sorted
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        # Use difflib to find similar titles
        matches = []
        for row in results:
            similarity = SequenceMatcher(None, title.lower(), row[0].lower()).ratio()
            if similarity > 0.6:  # Threshold for similarity
                matches.append((similarity, {
                    'title': row[0],
                    'release_year': row[1],
                    'genres': row[2],
                    'director': row[3],
                    'stars': row[4],
                    'keywords': row[5],
                    'rating': row[6],
                    'final_score': row[7]
                }))
        
        # Sort by similarity and return top matches
        matches.sort(key=lambda x: x[0], reverse=True)
        return [movie for _, movie in matches[:limit]]
    
    def get_similar_movies_by_genres(self, target_genres: str, exclude_title: str, limit: int = 5) -> List[Dict]:
        """Find movies with similar genres, excluding the specified title"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Parse the target genres
        target_genre_list = [g.strip().lower() for g in target_genres.split(',') if g.strip()]
        
        if not target_genre_list:
            return []
        
        # Build query to find movies with similar genres
        # This will search for movies that have at least one similar genre
        placeholders = ','.join(['?'] * len(target_genre_list))
        
        query = f'''
            SELECT title, release_year, genres, director, stars, keywords, rating, final_score
            FROM Movies_sorted
            WHERE LOWER(title) != LOWER(?)
            AND ({" OR ".join([f"LOWER(genres) LIKE ?" for _ in target_genre_list])})
            ORDER BY final_score DESC
            LIMIT ?
        '''
        
        # Prepare parameters for query
        params = [exclude_title.lower()] + [f'%{genre}%' for genre in target_genre_list] + [str(limit)]
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        similar_movies = []
        for row in results:
            movie = {
                'title': row[0],
                'release_year': row[1],
                'genres': row[2],
                'director': row[3],
                'stars': row[4],
                'keywords': row[5],
                'rating': row[6],
                'final_score': row[7]
            }
            similar_movies.append(movie)
        
        return similar_movies
    
    def get_similar_movies_by_keywords(self, target_keywords: str, exclude_title: str, limit: int = 5) -> List[Dict]:
        """Find movies with similar keywords, excluding the specified title"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Parse the target keywords
        target_keywords_list = [k.strip().lower() for k in target_keywords.split(',') if k.strip()]
        
        if not target_keywords_list:
            return []
        
        # Build query to find movies with similar keywords
        query = f'''
            SELECT title, release_year, genres, director, stars, keywords, rating, final_score
            FROM Movies_sorted
            WHERE LOWER(title) != LOWER(?)
            AND ({" OR ".join([f"LOWER(keywords) LIKE ?" for _ in target_keywords_list])})
            ORDER BY final_score DESC
            LIMIT ?
        '''
        
        # Prepare parameters for query
        params = [exclude_title.lower()] + [f'%{keyword}%' for keyword in target_keywords_list] + [str(limit)]
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        conn.close()
        
        similar_movies = []
        for row in results:
            movie = {
                'title': row[0],
                'release_year': row[1],
                'genres': row[2],
                'director': row[3],
                'stars': row[4],
                'keywords': row[5],
                'rating': row[6],
                'final_score': row[7]
            }
            similar_movies.append(movie)
        
        return similar_movies
    
    def comprehensive_similarity_search(self, target_title: str, limit: int = 5) -> List[Dict]:
        """
        Comprehensive similarity search using multiple factors
        """
        # Get the target movie
        target_movie = self.get_movie_by_title(target_title)
        
        if not target_movie:
            # Try fuzzy matching
            possible_matches = self.search_movies_fuzzy(target_title)
            if possible_matches:
                target_movie = possible_matches[0]
            else:
                return []
        
        # Get similar movies based on genres (primary method)
        genre_similar = self.get_similar_movies_by_genres(
            target_movie['genres'], 
            target_movie['title'], 
            limit * 2  # Get more to have options
        )
        
        # If we have keywords, also find similar by keywords
        if target_movie.get('keywords'):
            keyword_similar = self.get_similar_movies_by_keywords(
                target_movie['keywords'],
                target_movie['title'],
                limit * 2
            )
            
            # Combine and deduplicate results
            combined_movies = {}
            for movie in genre_similar + keyword_similar:
                combined_movies[movie['title']] = movie
            
            # Sort by final score and return top
            sorted_movies = sorted(combined_movies.values(), key=lambda x: x['final_score'] or 0, reverse=True)
            return sorted_movies[:limit]
        else:
            return genre_similar[:limit]