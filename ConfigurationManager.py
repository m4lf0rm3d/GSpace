import configparser

# Create a ConfigParser object
config = configparser.ConfigParser()

# Read the configuration file 'settings.conf'
config.read('settings.conf')

# General Settings
APP_NAME = config.get('General', 'app_name')
APP_VERSION = config.get('General', 'version')
DEBUG = config.getboolean('General', 'debug')

# Google Drive API Settings
CLIENT_SECRET_PATH = config.get('GoogleDriveAPI', 'client_secret_path')
OUTPUT_TOKEN_FILE = config.get('GoogleDriveAPI', 'output_token_file')
ROOT_FOLDER_ID = config.get('GoogleDriveAPI', 'root_folder_id')
ROOT_FOLDER_NAME = config.get('GoogleDriveAPI', 'root_folder_name')

# Local Filesystem Settings
LOCAL_FILESYSTEM_FOLDER_PATH = config.get('LocalFilesystem', 'folder_path')
BACKUP_FOLDER_PATH = config.get('LocalFilesystem', 'backup_folder_path')

# Logs Settings
LOGS_FOLDER_PATH = config.get('Logs', 'logs_path')
