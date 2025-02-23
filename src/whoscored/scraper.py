import logging
import pandas as pd
import json
import numpy as np
from .whoscored import WhoScored

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def process_match_data(match_key, match_data, league):
    """Processes match data and returns the necessary information"""
    try:
        if isinstance(match_data, str):
            match = json.loads(match_data)
        elif isinstance(match_data, dict):
            match = match_data
        else:
            logging.warning(f"Unexpected type of data for {match_key}: {type(match_data)}")
            return None

        game = match_key.split("2025-")[1]
        game_id = match["matchId"]
        
        events_data = []
        playerIdNameDictionary = match["matchCentreData"].get("playerIdNameDictionary", {})
        date = match["matchCentreData"].get("startDate")
        score = match["matchCentreData"].get("score")

        for event in match["matchCentreData"].get("events", []):
            event_data = {
                "game": game,
                "game_id": game_id,
                "score": score,
                "event_id": event.get("id"),
                "period_id": event["period"].get("value"),
                "team_id": event.get("teamId"),
                "player_id": event.get("playerId"),
                "player_name": playerIdNameDictionary.get(str(event.get("playerId"))),
                "type_id": event.get("eventId"),
                "date": date,
                "minute": event.get("minute"),
                "second": event.get("second"),
                "outcome": event.get("outcomeType", {}).get("value") == 1,
                "start_x": event.get("x"),
                "start_y": event.get("y"),
                "end_x": event.get("endX"),
                "end_y": event.get("endY"),
                "qualifiers": event.get("qualifiers"),
                "touch": event.get("isTouch"),
                "shot": event.get("isShot", False),
                "goal": event.get("isGoal", False),
                "type_name": event["type"].get("displayName")
            }
            events_data.append(event_data)

        return {
            'events_df': pd.DataFrame(events_data),
            'game_info': {
                'game_id': game_id,
                'game': game,
                'league': league
            }
        }

    except Exception as e:
        logging.error(f"Error when processing the match {match_key}: {str(e)}")
        return None

def get_matches_data(year=2025):
    """Retrieves data for all matches in a given season"""
    scraper = WhoScored()
    all_matches_data = []
    games_info = []
    
    # leagues = ["Champions League", "Bundesliga", "EPL", "La Liga", "Ligue 1", "Serie A"]
    leagues = ["Bundesliga", "EPL", "La Liga", "Ligue 1", "Serie A"]
    
    try:
        for league in leagues:
            logging.info(f'Scraping {league} data in {year}')
            result = scraper.scrape_matches(year, league)
            
            if isinstance(result, dict):
                logging.info(f'Data collected {league} {year}. Games found: {len(result)}')
                
                for match_key, match_data in result.items():
                    processed_data = process_match_data(match_key, match_data, league)
                    if processed_data:
                        all_matches_data.append(processed_data['events_df'])
                        games_info.append(processed_data['game_info'])
            else:
                logging.error(f'Error when scraping {league} {year}')
                
    except Exception as e:
        logging.error(f"Error when scraping: {str(e)}")
    finally:
        scraper.close()
        
    return {
        'matches_data': all_matches_data,
        'games_info': pd.DataFrame(games_info)
    }

def preprocess_events_df(events_df, league, clubs_list, clubs_ids):
    """
    Applique le preprocessing aux données d'événements d'un match.
    """
    def find_clubs(ws_name, clubs_list):
        """
        Find the two clubs names in a single string.
        Parameters:
        - ws_name (string): The game string (ex: "paris-saint-germain-clermont-foot").
        - clubs_list (string): The clubs list referential.
        Returns:
        - list: The list with the two clubs in the right order.
        """
        ws_name = ws_name.replace(" ", "-")
        
        found_clubs = []
        for club in clubs_list:
            if club.lower() in ws_name.lower():
                found_clubs.append(club)
        
        return found_clubs

    def check_card_type(qualifiers):
        """
        Check the card type from the event.

        Parameters:
        - qualifiers (list): The dictionary list of qualifiers

        Returns:
        - string: A value between "Red", "Second Yellow", "Yellow" or None.
        """
        display_names = []
        for i in range (0, len(qualifiers)):
            display_names.append(qualifiers[i]["type"]["displayName"])
        if "Red" in display_names:
            return "Red"
        elif "SecondYellow" in display_names:
            return "SecondYellow"
        elif "Yellow" in display_names:
            return "Yellow"
        else:
            return None

    def calculate_expected_threat(row):
        """
        Calculate the "Expected Threat" metric for a pass (based only from the distance to the opponent goal, not the xT matrix).

        Parameters:
        - row (dict): The pass event dictionary from the dataframe.

        Returns:
        - float: The xT value, between 0 and 1.
        """
        if row['type_name'] == 'Pass':
            # provisional calculation
            distance_to_goal = np.sqrt((100 - row['start_x'])**2 + (50 - row['start_y'])**2)
            expected_threat = np.exp(-0.1 * distance_to_goal)
        else:
            expected_threat = 0
        return expected_threat

    try:
        events_df["league"] = league.replace("_", " ")
        original_game_name = events_df.loc[0, "game"]
        
        try:
            clubs = find_clubs(original_game_name, clubs_list)
            
            if len(clubs) != 2:
                logging.warning(f"Found {len(clubs)} clubs in '{original_game_name}', trying direct split")
                clubs = original_game_name.split(" - ")
            
            if len(clubs) == 2:
                home_team, away_team = clubs
                new_game_name = f"{home_team} - {away_team}"
                events_df["game"] = new_game_name

                team_ids = {value: key for key, value in clubs_ids.items()}
                events_df["team_name"] = events_df["team_id"].apply(
                    lambda x: team_ids.get(x, f"Team_{x}")
                )
                
                events_df["h_a"] = events_df["team_name"].apply(
                    lambda x: 'h' if x == home_team else 'a'
                )
            else:
                logging.warning(f"Could not process team names for {original_game_name}, keeping original data")

        except Exception as e:
            logging.warning(f"Error in team processing for {original_game_name}: {str(e)}")

        try:
            events_df["qualifiers"] = events_df["qualifiers"].apply(
                lambda x: eval(x) if isinstance(x, str) else x
            )
            events_df['cardType'] = events_df.apply(
                lambda row: check_card_type(row['qualifiers']) if row['type_name'] == 'Card' else None,
                axis=1
            )
        except Exception as e:
            logging.warning(f"Error in qualifiers processing: {str(e)}")

        try:
            events_df['xT_added'] = events_df.apply(calculate_expected_threat, axis=1)
            events_df = events_df.rename(columns={'start_x': 'x', 'start_y': 'y'})
        except Exception as e:
            logging.warning(f"Error in xT calculation: {str(e)}")

        return events_df

    except Exception as e:
        logging.error(f"Critical error in preprocessing for {original_game_name}: {str(e)}")
        return events_df