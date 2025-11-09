try:
    import sqlite3
    import pandas as pd
    from sklearn.preprocessing import MinMaxScaler
    from collections import Counter
    from itertools import chain

except ImportError as error:
    print("⚠️ Modules could not be imported: ", error)

def find_user_interests(db_path, user_id=None):
    # Number of each feature to return
    top_n_genres = 6 
    top_n_keywords = 10

    # Giving weight to features as their value in the processing
    col1 = "user_rate"
    col2 = "liked"
    w1 = 0.75
    w2 = 0.25

    # If user_id is provided and not None, try to get user-specific data
    if user_id is not None:
        conn = sqlite3.connect(db_path)
        query = '''
        SELECT ud.user_id, ud.movie_id, ud.user_rate, ud.liked, ms.genres, ms.keywords
        FROM Users_data ud
        JOIN Movies_sorted ms ON ud.movie_id = ms.movie_id
        WHERE ud.user_id = ?
        '''
        df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()

        if not df.empty:
            # Normalize user ratings
            scaler = MinMaxScaler()
            df["normalized_rate"] = scaler.fit_transform(df[[col1]])
            df["like_weight"] = df[col2].astype(int)

            # Calculate the final score combining normalized rating and like weight
            df["final_score"] = w1 * df["normalized_rate"] + w2 * df["like_weight"]
            # Sort the DataFrame by the final score in descending order
            df = df.sort_values(by="final_score", ascending=False)
            top_list = min(len(df) // 3, 20)  # Limit to max 20 to avoid empty results
            df = df.head(top_list)

            # convert to lowercase and split by comma+space
            df["genres"] = df["genres"].str.lower().str.split(", ")
            df["keywords"] = df["keywords"].str.lower().str.split(", ")

            top_genres = Counter(chain.from_iterable(df["genres"].dropna())).most_common(top_n_genres)
            top_keywords = Counter(chain.from_iterable(df["keywords"].dropna())).most_common(top_n_keywords)

            return [g[0] for g in top_genres], [k[0] for k in top_keywords]

    # If no user-specific data is available, return popular genres and keywords
    print("No user data found. Providing popular recommendations.")
    conn = sqlite3.connect(db_path)
    
    # Get most popular genres and keywords from the main movies table
    query = '''
    SELECT genres, keywords
    FROM Movies_sorted
    ORDER BY final_score DESC
    LIMIT 100  -- Take top 100 highest rated movies
    '''
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Process the data to extract genres and keywords
    all_genres = []
    all_keywords = []
    
    for _, row in df.iterrows():
        if pd.notna(row['genres']):
            genres = [g.strip().lower() for g in str(row['genres']).split(',')]
            all_genres.extend(genres)
        if pd.notna(row['keywords']):
            keywords = [k.strip().lower() for k in str(row['keywords']).split(',')]
            all_keywords.extend(keywords)

    # Get most common genres and keywords
    top_genres = Counter(all_genres).most_common(top_n_genres)
    top_keywords = Counter(all_keywords).most_common(top_n_keywords)

    return [g[0] for g in top_genres], [k[0] for k in top_keywords]
