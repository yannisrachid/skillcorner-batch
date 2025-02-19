import pandas as pd
import numpy as np
import redis
import logging
import pickle
import os
from datetime import datetime

# Configuration des logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration Redis
REDIS_HOST = os.getenv('REDIS_HOST', 'redis')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))

def create_random_dataframe(size=1000):
    """Crée un DataFrame aléatoire avec des données de matchs"""
    dates = pd.date_range(start='2024-01-01', periods=size, freq='D')
    
    data = {
        'match_id': range(1, size + 1),
        'date': dates,
        'home_team': np.random.choice(['PSG', 'Lyon', 'Marseille'], size),
        'away_team': np.random.choice(['Lens', 'Rennes', 'Nice'], size),
        'home_score': np.random.randint(0, 5, size),
        'away_score': np.random.randint(0, 5, size)
    }
    
    return pd.DataFrame(data)

def load_data():
    """Charge les DataFrames dans Redis"""
    try:
        # Connexion à Redis
        logger.info(f"Connection to Redis ({REDIS_HOST}:{REDIS_PORT})")
        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
        redis_client.ping()

        logger.info("Loading cache data")
        
        # Création et stockage des DataFrames
        for i in range(3):
            df = create_random_dataframe(size=1000)
            key = f"match_data_{i}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"            
            redis_client.set(key, pickle.dumps(df))
            logger.info(f"DataFrame chargé dans Redis avec la clé: {key}")
            
    except Exception as e:
        logger.error(f"Erreur: {str(e)}")
        raise

if __name__ == "__main__":
    load_data()
    logger.info("Batch executed successfully")