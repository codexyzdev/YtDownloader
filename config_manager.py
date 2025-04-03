# config_manager.py
import configparser
import os

CONFIG_FILE = 'config.ini'
DEFAULT_SECTION = 'Settings'
LAST_DIR_KEY = 'last_download_directory'

def load_settings():
    """Loads settings from the CONFIG_FILE."""
    config = configparser.ConfigParser()
    settings = {}
    if os.path.exists(CONFIG_FILE):
        try:
            config.read(CONFIG_FILE)
            if DEFAULT_SECTION in config:
                settings[LAST_DIR_KEY] = config[DEFAULT_SECTION].get(LAST_DIR_KEY)
        except configparser.Error as e:
            print(f"Error reading config file {CONFIG_FILE}: {e}")
            # Optionally return default settings or raise error
    return settings

def save_settings(settings):
    """Saves settings to the CONFIG_FILE."""
    config = configparser.ConfigParser()
    config[DEFAULT_SECTION] = {}
    
    if LAST_DIR_KEY in settings and settings[LAST_DIR_KEY]:
        config[DEFAULT_SECTION][LAST_DIR_KEY] = settings[LAST_DIR_KEY]
        
    try:
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    except IOError as e:
        print(f"Error writing config file {CONFIG_FILE}: {e}")

# Usage example (not executed directly)
if __name__ == '__main__':
    # Load (or create if it doesn't exist)
    current_settings = load_settings()
    print(f"Loaded settings: {current_settings}")

    # Modify and save
    current_settings[LAST_DIR_KEY] = os.path.expanduser("~") # Example: save home directory
    save_settings(current_settings)
    print("Saved settings.")

    # Reload to verify
    reloaded_settings = load_settings()
    print(f"Reloaded settings: {reloaded_settings}")