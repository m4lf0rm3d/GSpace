import io
import os
import pickle
import traceback  # Import traceback module for detailed error information
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from Logger import Logger
import ConfigurationManager

class GoogleDriveHelper:
    logger = Logger()

    def __init__(self):
        # If modifying these SCOPES, delete the output pickle file.
        self.SCOPES = ['https://www.googleapis.com/auth/drive']
        self.CLIENT_CREDENTIALS_JSON = ConfigurationManager.CLIENT_SECRET_PATH
        self.service = None
        self.ROOT_FOLDER_ID = ConfigurationManager.ROOT_FOLDER_ID
        self.ROOT_FOLDER_NAME = ConfigurationManager.ROOT_FOLDER_NAME

    def get_credentials(self):
        try:
            credentials = None

            # The file token.pickle stores the user's access and refresh tokens and is
            # created automatically when the authorization flow completes for the first time.
            if os.path.exists(ConfigurationManager.OUTPUT_TOKEN_FILE):
                with open(ConfigurationManager.OUTPUT_TOKEN_FILE, 'rb') as token:
                    credentials = pickle.load(token)

            # If there are no (valid) credentials available, let the user log in.
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(self.CLIENT_CREDENTIALS_JSON, self.SCOPES)
                    credentials = flow.run_local_server(port=0)

                # Save the credentials for the next run
                with open(ConfigurationManager.OUTPUT_TOKEN_FILE, 'wb') as token:
                    pickle.dump(credentials, token)

            return credentials
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in get_credentials: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def initialize_service(self):
        try:
            # Create a Google Drive API service using the saved or new credentials
            print("============================================\nInitializing Google Drive service ...")
            self.service = build('drive', 'v3', credentials=self.get_credentials())
            print("Initializing Complete!\n============================================")
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in initialize_service: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def generate_tree_from_google_drive(self, tree_root, parent_id=ConfigurationManager.ROOT_FOLDER_ID, path=[]):
        try:
            results = self.service.files().list(q=f"parents in '{parent_id}'", pageSize=1000,
                                                fields="nextPageToken, files(id, name, mimeType, trashed, size)").execute()
            items = results.get('files', [])

            for i, item in enumerate(items):
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    if not item['trashed']: tree_root.add([self.ROOT_FOLDER_NAME] + path + [item['name']], item['id'], isDir=True)
                    if not item['trashed']: self.generate_tree_from_google_drive(tree_root, item['id'], path + [item['name']])
                else:
                    if not item['trashed']: tree_root.add([self.ROOT_FOLDER_NAME] + path + [item['name']], item['id'], isDir=False, fileSize=item['size'])
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in generate_tree_from_google_drive: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def upload_file(self, file_path, folder_id):
        try:
            file_name = os.path.basename(file_path)
            media_body = MediaFileUpload(ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + file_path, resumable=True)
            request = self.service.files().create(
                media_body=media_body,
                body={
                    'name': file_name,
                    'parents': [folder_id]
                }
            )
            response = None
            print(f"===============================\nStarting upload for: {file_name}")
            while response is None:
                status, response = request.next_chunk()
            print(f"Upload complete!\nFile path: {file_path}\n===============================")
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in upload_file: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def create_folder(self, folder_name, parent_folder_id):
        try:
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [parent_folder_id]
            }
            folder = self.service.files().create(body=folder_metadata, fields='id').execute()
            return folder['id']
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in create_folder: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def create_folders_for_upload(self, names, parent_folder_id):
        try:
            last_id = parent_folder_id
            for name in names:
                folder_metadata = {
                    'name': name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [last_id]
                }
                folder = self.service.files().create(body=folder_metadata, fields='id').execute()
                last_id = folder['id']
            return last_id
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in create_folders_for_upload: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def upload_folder(self, folder_path, parent_folder_id):
        try:
            folder_name = os.path.basename(folder_path)
            folder_id = self.create_folder(folder_name, parent_folder_id)

            for item in os.listdir(ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + item_path):
                    self.upload_file(item_path, folder_id)
                elif os.path.isdir(ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + item_path):
                    self.upload_folder(item_path, folder_id)

            print(f"===============================\nUpload complete for folder: {folder_name}.\n===============================")
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in upload_folder: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def upload_helper(self, gdrive_tree, folder_path):
        try:
            folder_path = folder_path[0]
            to_upload_path = folder_path.split("/")
            nearest_node, folders_already_created = gdrive_tree.get_node(to_upload_path[1:])
            final_id = nearest_node.id
            if folders_already_created != len(to_upload_path[1:-1]):
                final_id = self.create_folders_for_upload(to_upload_path[folders_already_created + 1:], nearest_node.id)
            self.upload_file(folder_path, final_id) if not os.path.isdir(
                ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + folder_path) else self.upload_folder(
                folder_path, final_id)
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in upload_helper: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def hard_delete_file(self, file_id):
        try:
            self.service.files().delete(fileId=file_id).execute()
            print(f"File/Folder with ID {file_id} deleted successfully.")
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in hard_delete_file: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def delete_file(self, file_id, gdrive_tree=None):
        try:
            body_value = {'trashed': True}
            self.service.files().update(fileId=file_id, body=body_value).execute()

            parent_node_of_file = gdrive_tree.find_parent_node_by_id(file_id)
            if parent_node_of_file:
                for file_name in parent_node_of_file.children:
                    if(parent_node_of_file.children[file_name].id == file_id):
                        del parent_node_of_file.children[file_name]
                        break


            print(f"File/Folder with ID {file_id} moved to trash successfully.")
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in delete_file: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def download_file(self, output_path, drive_file_id):
        try:
            request = self.service.files().get_media(fileId=drive_file_id)

            dir_path = (ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + output_path).removesuffix(
                os.path.basename((ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + output_path)))
            os.makedirs(dir_path, exist_ok=True)

            with io.FileIO(ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + output_path, 'wb') as output_file:
                downloader = MediaIoBaseDownload(output_file, request)
                done = False

                print(f"===============================\nStarting download for: {output_path.split('/')[-1]}")

                while not done:
                    status, done = downloader.next_chunk()

            print(f"Download complete!\nFile saved to: {output_path}\n===============================")
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in download_file: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def download_folder(self, output_path, drive_folder_id):
        try:
            os.makedirs(ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + output_path, exist_ok=True)

            results = self.service.files().list(
                q=f"parents in '{drive_folder_id}'",
                fields="files(id, name, mimeType)").execute()
            items = results.get('files', [])

            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    subfolder_path = os.path.join(output_path, item['name'])
                    self.download_folder(subfolder_path, item['id'])
                else:
                    file_path = os.path.join(output_path, item['name'])
                    self.download_file(file_path, item['id'])

        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in download_folder: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def download_helper(self, output_path, drive_folder_id, isDir):
        try:
            self.download_file(output_path, drive_folder_id) if not isDir else self.download_folder(output_path,
                                                                                                     drive_folder_id)
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in download_helper: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e
