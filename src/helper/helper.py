import base64
import numpy as np

def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

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
        # Calcul de la distance entre le début de la passe et le but adverse
        distance_to_goal = np.sqrt((100 - row['start_x'])**2 + (50 - row['start_y'])**2)
        # Calcul de l'Expected Threat
        # Plus la distance au but est faible, plus l'Expected Threat est élevé
        expected_threat = np.exp(-0.1 * distance_to_goal)
    else:
        expected_threat = 0
    return expected_threat

def find_clubs(ws_name, clubs_list):
    """
    Find the two clubs names in a single string.
    Parameters:
    - ws_name (string): The game string (ex: "paris-saint-germain-clermont-foot").
    - clubs_list (string): The clubs list referential.
    Returns:
    - list: The list with the two clubs in the right order.
    """
    # Normaliser d'abord le nom du match
    ws_name = ws_name.replace(" ", "-")
    
    # Garder l'ordre original des équipes
    found_clubs = []
    for club in clubs_list:
        if club.lower() in ws_name.lower():
            found_clubs.append(club)
    
    return found_clubs