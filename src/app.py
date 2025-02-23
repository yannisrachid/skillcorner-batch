import logging
import redis
import pickle
import os
import pandas as pd
from whoscored import get_matches_data, preprocess_events_df
from helper import *

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

def store_df_in_redis(redis_client, key, df):
    """Stores a DataFrame in Redis"""
    try:
        pickled_data = pickle.dumps(df)
        redis_client.set(key, pickled_data)
        # redis_client.expire(key, 24 * 60 * 60)  # expire after 24h
        logging.info(f"DataFrame stored in Redis with the key: {key}")
    except Exception as e:
        logging.error(f"Error storing in Redis: {str(e)}")
        raise
    

def load_data():
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)

    logging.info("Start of batch job")
    scraped_data = get_matches_data()
    logging.info("Scraping done!")
    logging.info("Starting data preprocessing...")

    processed_games_info = []

    for game_info, match_data in zip(scraped_data['games_info'].to_dict('records'), scraped_data['matches_data']):
        game_id = game_info['game_id']
        league = game_info['league']

        logging.info(f"Starting preprocessing of game_id: {game_id}")

        events_df = pd.DataFrame(match_data)
        
        processed_df = preprocess_events_df(
            events_df,
            league,
            clubs_list,
            clubs_ids
        )
        
        game_info['game'] = processed_df.loc[0, 'game']
        processed_games_info.append(game_info)
        
        store_df_in_redis(redis_client, f"game_data_{game_id}", processed_df)
        logging.info(f"Processed game data {game_id} stored in Redis")
            

    games_df = pd.DataFrame(processed_games_info)
    store_df_in_redis(redis_client, "games", games_df)
    logging.info(f"List of processed games stored in Redis. Total: {len(processed_games_info)} games")
        

if __name__ == "__main__":
    load_data()
    logging.info("Batch executed successfully")