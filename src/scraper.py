"""
Web scraper for movie data
"""
import sqlite3
import requests
from bs4 import BeautifulSoup
import time
import random
from typing import List, Dict


class MovieScraper:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.base_url = "https://www.imdb.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_top_movies(self, max_pages: int = 5) -> List[Dict]:
        """
        Scrape top movies from IMDb
        """
        movies = []
        
        for page in range(1, max_pages + 1):
            url = f"https://www.imdb.com/search/title/?groups=top_1000&start={(page-1)*50 + 1}&ref_=adv_nxt"
            try:
                response = requests.get(url, headers=self.headers)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                movie_containers = soup.find_all('div', class_='lister-item')
                
                for container in movie_containers:
                    try:
                        title_element = container.find('h3', class_='lister-item-header').find('a')
                        title = title_element.text.strip() if title_element else "Unknown"
                        
                        year_element = container.find('span', class_='lister-item-year')
                        year = year_element.text.strip('()') if year_element else "Unknown"
                        
                        rating_element = container.find('strong')
                        rating = rating_element.text if rating_element else "0"
                        
                        # Get genre
                        genre_element = container.find('span', class_='genre')
                        genre = genre_element.text.strip() if genre_element else "Unknown"
                        
                        # Get description
                        description_element = container.find('p', class_='').find_next_sibling('p')
                        if description_element and 'text-muted' not in description_element.get('class', []):
                            description = description_element.text.strip()
                        else:
                            description = "No description available"
                        
                        movie_data = {
                            'title': title,
                            'year': year,
                            'rating': float(rating) if rating.replace('.', '').isdigit() else 0.0,
                            'genre': genre,
                            'description': description
                        }
                        
                        movies.append(movie_data)
                        print(f"Scraped: {title} ({year})")
                        
                    except Exception as e:
                        print(f"Error processing movie: {e}")
                        continue
                
                # Be respectful to the server
                time.sleep(random.uniform(1, 3))
                
            except requests.RequestException as e:
                print(f"Error fetching page {page}: {e}")
                continue
        
        return movies
    
    def search_movie_details(self, movie_title: str) -> Dict:
        """
        Search for detailed info about a specific movie
        """
        search_url = f"{self.base_url}/find?q={movie_title.replace(' ', '+')}&s=tt&ttype=ft"
        
        try:
            response = requests.get(search_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            # Get the first result
            result_link = soup.find('td', class_='result_text')
            if result_link:
                link = result_link.find('a')
                if link:
                    movie_url = self.base_url + link['href']
                    return self.scrape_movie_details(movie_url)
        
        except Exception as e:
            print(f"Error searching for {movie_title}: {e}")
        
        return {}
    
    def scrape_movie_details(self, url: str) -> Dict:
        """
        Scrape detailed info from a movie page
        """
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract various details
            title_element = soup.find('h1')
            title = title_element.text.strip() if title_element else "Unknown"
            
            # Year
            year_element = soup.find('a', href=lambda x: x and '/year/' in x if x else False)
            year = year_element.text.strip() if year_element else "Unknown"
            
            # Rating
            rating_element = soup.find('span', class_='sc-bde20123-1')
            rating = float(rating_element.text) if rating_element and rating_element.text.replace('.', '').isdigit() else 0.0
            
            # Genres
            genre_elements = soup.find_all('a', href=lambda x: x and '/genre/' in x if x else False)
            genres = [g.text.strip() for g in genre_elements][:3]  # Take first 3 genres
            genre_str = ','.join(genres) if genres else "Unknown"
            
            # Director
            director_element = soup.find('a', href=lambda x: x and 'tt_ov_dr' in x if x else False)
            director = director_element.text.strip() if director_element else "Unknown"
            
            # Cast
            cast_elements = soup.find_all('a', href=lambda x: x and 'tt_ov_st' in x if x else False)
            cast = [c.text.strip() for c in cast_elements[:3]]  # Take first 3 actors
            cast_str = ','.join(cast) if cast else "Unknown"
            
            # Description/Overview
            summary_element = soup.find('span', {'data-testid': 'plot-xl'})
            summary = summary_element.text.strip() if summary_element else "No summary available"
            
            return {
                'title': title,
                'year': year,
                'rating': rating,
                'genres': genre_str,
                'director': director,
                'cast': cast_str,
                'summary': summary
            }
        
        except Exception as e:
            print(f"Error scraping movie details from {url}: {e}")
            return {}
    
    def save_movies_to_db(self, movies: List[Dict]):
        """
        Save scraped movies to the database
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if table exists and create if needed
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraped_movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                release_year TEXT,
                genres TEXT,
                director TEXT,
                cast TEXT,
                rating REAL,
                summary TEXT,
                UNIQUE(title, release_year)
            )
        ''')
        
        added_count = 0
        for movie in movies:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO scraped_movies 
                    (title, release_year, genres, director, cast, rating, summary) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    movie.get('title', ''),
                    movie.get('year', ''),
                    movie.get('genres', ''),
                    movie.get('director', ''),
                    movie.get('cast', ''),
                    movie.get('rating', 0.0),
                    movie.get('summary', '')
                ))
                
                if cursor.rowcount > 0:
                    added_count += 1
                    print(f"Added to DB: {movie.get('title', '')}")
                    
            except sqlite3.Error as e:
                print(f"Database error for {movie.get('title', '')}: {e}")
        
        conn.commit()
        conn.close()
        
        print(f"Successfully added {added_count} movies to database")
    
    def scrape_and_save(self, max_pages: int = 3):
        """
        Main method to scrape movies and save to database
        """
        print("Starting to scrape top movies...")
        movies = self.get_top_movies(max_pages)
        
        if movies:
            self.save_movies_to_db(movies)
        else:
            print("No movies were scraped.")