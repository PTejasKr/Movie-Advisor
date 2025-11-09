try:
    import sqlite3 
    import pandas as pd  
except ImportError as error:
    print("⚠️ Modules could not be imported: ", error)

def catch_watched_movies(db_path, user_id):
    """
    Gets watched movie_id-s by user
    """
    try:
        with sqlite3.connect(db_path) as conn:
            query = "SELECT movie_id FROM Users_data WHERE user_id = ?"
            df = pd.read_sql(query, conn, params=(user_id,))
            return df['movie_id'].tolist()
    except Exception as error:
        # Just return empty list if there are issues (like no user data)
        return []

if __name__ == "__main__":
    db_path = "database/MovieDude.db"
    # Test with a dummy user ID (assuming user_id 1 might exist or return an empty list)
    user_id = 1 
    watched_movies = catch_watched_movies(db_path, user_id)
    print(f"Watched movies for user {user_id}: {watched_movies}")

    # Test with a user ID that likely doesn't exist
    user_id_non_existent = 9999
    watched_movies_non_existent = catch_watched_movies(db_path, user_id_non_existent)
    print(f"Watched movies for user {user_id_non_existent}: {watched_movies_non_existent}")
