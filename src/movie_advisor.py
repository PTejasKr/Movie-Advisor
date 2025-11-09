"""
Console-based movie advisor interface
"""
import os
import sqlite3
from difflib import SequenceMatcher

from similarity_engine import MovieSimilarityEngine
from termcolor import colored


def clear_screen():
    """Clear the console screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def display_movie(movie):
    """Display a single movie with formatting"""
    print(f"  • {colored(movie['title'], 'cyan', attrs=['bold'])} ({movie['release_year']})")
    print(f"    Genres: {movie['genres']}")
    if movie.get('director') and movie['director'] != 'Unknown':
        print(f"    Director: {movie['director']}")
    if movie.get('stars') and movie['stars'] != 'Unknown':
        print(f"    Stars: {movie['stars']}")
    print(f"    Rating: {movie['rating']}/10")
    print()


def main():
    """Main console interface"""
    print(colored("Welcome to the Movie Advisor!", "green", attrs=['bold']))
    print(colored("=" * 50, "yellow"))
    
    user_name = input(colored("Please enter your name: ", "green")).strip()
    if not user_name:
        user_name = "User" # Default name if none provided

    print(f"\nHello, {colored(user_name, 'cyan', attrs=['bold'])}!")
    print("Enter a movie title to get 5 similar movie recommendations!")
    print("Type 'quit' or 'exit' to leave the program.\n")
    
    # Initialize similarity engine
    db_path = "database/MovieDude.db"
    if not os.path.exists(db_path):
        print(colored(f"Error: Database not found at {db_path}", "red"))
        return
    
    engine = MovieSimilarityEngine(db_path)
    
    while True:
        try:
            # Get user input
            user_movie_input = input(colored("Enter a movie title: ", "green")).strip()
            
            # Check for exit commands
            if user_movie_input.lower() in ['quit', 'exit', 'q']:
                print(colored(f"\nThanks for using Movie Advisor, {user_name}! Enjoy your movies!", "green"))
                break
            
            # Validate input
            if not user_movie_input:
                print(colored("Please enter a valid movie title.\n", "red"))
                continue
            
            print(colored(f"\nSearching for movies similar to '{user_movie_input}'...", "yellow"))
            
            # Find similar movies
            similar_movies = engine.comprehensive_similarity_search(user_movie_input, 5)
            
            if not similar_movies:
                print(colored(f"\nNo similar movies found for '{user_movie_input}'. Please try another title.\n", "red"))
            else:
                print(colored(f"\n--- Similar Movies for '{user_movie_input}' ---", "green", attrs=['bold']))
                print(colored("-" * 50, "yellow"))
                
                for i, movie in enumerate(similar_movies, 1):
                    print(colored(f"{i}. ", "yellow", attrs=['bold']), end="")
                    display_movie(movie)
                
                print(colored("-" * 50, "yellow"))
        
        except KeyboardInterrupt:
            print(colored("\n\nProgram interrupted. Goodbye!", "red"))
            break
        except Exception as e:
            print(colored(f"An error occurred: {e}", "red"))


if __name__ == "__main__":
    main()
