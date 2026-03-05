import json
import os
import logging

logger = logging.getLogger("ConfigLoader")

def load_json_config(filepath: str) -> dict:
    """Loads a JSON configuration file and returns it as a dictionary."""
    if not os.path.exists(filepath):
        logger.error(f"Configuration file missing: {filepath}")
        return {}
    
    with open(filepath, 'r') as file:
        try:
            return json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON in {filepath}: {e}")
            return {}
