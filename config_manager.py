# config_manager.py
import configparser
import os

CONFIG_FILE = 'config.ini'
DEFAULT_SECTION = 'Settings'
LAST_DIR_KEY = 'last_download_directory'

def load_settings():
    """Carga las configuraciones desde el archivo CONFIG_FILE."""
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
    """Guarda las configuraciones en el archivo CONFIG_FILE."""
    config = configparser.ConfigParser()
    config[DEFAULT_SECTION] = {}
    
    if LAST_DIR_KEY in settings and settings[LAST_DIR_KEY]:
        config[DEFAULT_SECTION][LAST_DIR_KEY] = settings[LAST_DIR_KEY]
        
    try:
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    except IOError as e:
        print(f"Error writing config file {CONFIG_FILE}: {e}")

# Ejemplo de uso (no se ejecuta directamente)
if __name__ == '__main__':
    # Cargar (o crear si no existe)
    current_settings = load_settings()
    print(f"Loaded settings: {current_settings}")

    # Modificar y guardar
    current_settings[LAST_DIR_KEY] = os.path.expanduser("~") # Ejemplo: guardar home
    save_settings(current_settings)
    print("Saved settings.")

    # Volver a cargar para verificar
    reloaded_settings = load_settings()
    print(f"Reloaded settings: {reloaded_settings}")