import io
import json
import os
import traceback

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

from Logger import Logger
import ConfigurationManager

# Rich UI
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TransferSpeedColumn, TimeRemainingColumn

_console = Console()


class GoogleDriveHelper:
    logger = Logger()

    def __init__(self):
        self.SCOPES             = ['https://www.googleapis.com/auth/drive']
        self.CLIENT_CREDENTIALS = ConfigurationManager.CLIENT_SECRET_PATH
        # Token is now stored as plain JSON instead of a binary pickle file.
        # This is safer, human-readable, and works on every platform including Termux.
        self.TOKEN_FILE         = ConfigurationManager.OUTPUT_TOKEN_FILE.replace('.pickle', '.json')
        self.service            = None
        self.ROOT_FOLDER_ID     = ConfigurationManager.ROOT_FOLDER_ID
        self.ROOT_FOLDER_NAME   = ConfigurationManager.ROOT_FOLDER_NAME

    # ------------------------------------------------------------------
    # Auth
    # ------------------------------------------------------------------

    def get_credentials(self):
        try:
            creds = None

            if os.path.exists(self.TOKEN_FILE):
                creds = Credentials.from_authorized_user_file(self.TOKEN_FILE, self.SCOPES)

            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    # Token expired — refresh silently using the stored refresh token.
                    # No user interaction needed; this happens automatically.
                    _console.print("[dim]Token expired, refreshing…[/]")
                    creds.refresh(Request())
                else:
                    # First-time auth (or refresh token was revoked).
                    # URL is printed as plain text so it can be copied easily
                    # on Termux / SSH without a box border breaking the selection.
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.CLIENT_CREDENTIALS, self.SCOPES,
                        redirect_uri="urn:ietf:wg:oauth:2.0:oob"
                    )
                    auth_url, _ = flow.authorization_url(prompt="consent")

                    _console.print()
                    _console.print("[bold yellow]Google auth required[/]")
                    _console.print("[dim]Open this URL in your browser:[/]")
                    _console.print()
                    _console.print(auth_url)   # plain text — no box, easy to copy/tap
                    _console.print()
                    code = _console.input("[bold]Paste the auth code:[/] ").strip()
                    flow.fetch_token(code=code)
                    creds = flow.credentials

                # Persist credentials after any update (first-time or refresh)
                with open(self.TOKEN_FILE, 'w') as f:
                    f.write(creds.to_json())

            return creds

        except Exception as e:
            self.logger.error(f"Error in get_credentials: {e}\n{traceback.format_exc()}")
            raise

    def initialize_service(self):
        try:
            with _console.status("[bold cyan]Connecting to Google Drive…[/]", spinner="dots"):
                self.service = build('drive', 'v3', credentials=self.get_credentials())
            _console.print("[bold green]✓[/] Google Drive connected")
        except Exception as e:
            self.logger.error(f"Error in initialize_service: {e}\n{traceback.format_exc()}")
            raise

    # ------------------------------------------------------------------
    # Tree generation
    # ------------------------------------------------------------------

    def generate_tree_from_google_drive(self, tree_root, parent_id=None, path=None):
        if parent_id is None:
            parent_id = ConfigurationManager.ROOT_FOLDER_ID
        if path is None:
            path = []
        try:
            results = self.service.files().list(
                q=f"parents in '{parent_id}'",
                pageSize=1000,
                fields="nextPageToken, files(id, name, mimeType, trashed, size)"
            ).execute()

            for item in results.get('files', []):
                if item['trashed']:
                    continue
                is_folder = item['mimeType'] == 'application/vnd.google-apps.folder'
                tree_root.add(
                    [self.ROOT_FOLDER_NAME] + path + [item['name']],
                    item['id'],
                    isDir=is_folder,
                    fileSize=item.get('size', 0) if not is_folder else 0
                )
                if is_folder:
                    self.generate_tree_from_google_drive(tree_root, item['id'], path + [item['name']])

        except Exception as e:
            self.logger.error(f"Error in generate_tree_from_google_drive: {e}\n{traceback.format_exc()}")
            raise

    # ------------------------------------------------------------------
    # Upload
    # ------------------------------------------------------------------

    def upload_file(self, file_path, folder_id):
        try:
            file_name  = os.path.basename(file_path)
            local_path = ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + file_path
            media_body = MediaFileUpload(local_path, resumable=True)
            request    = self.service.files().create(
                media_body=media_body,
                body={'name': file_name, 'parents': [folder_id]}
            )
            response = None
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]Uploading[/] [bold]{task.description}[/]"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=_console,
            ) as progress:
                task = progress.add_task(file_name, total=100)
                while response is None:
                    status, response = request.next_chunk()
                    if status:
                        progress.update(task, completed=int(status.progress() * 100))
                progress.update(task, completed=100)
            _console.print(f"  [green]↑[/] {file_path}")
        except Exception as e:
            self.logger.error(f"Error in upload_file: {e}\n{traceback.format_exc()}")
            raise

    def create_folder(self, folder_name, parent_folder_id):
        try:
            folder = self.service.files().create(
                body={
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_folder_id]
                },
                fields='id'
            ).execute()
            return folder['id']
        except Exception as e:
            self.logger.error(f"Error in create_folder: {e}\n{traceback.format_exc()}")
            raise

    def create_folders_for_upload(self, names, parent_folder_id):
        """
        Create a chain of nested folders and return the ID of the deepest one.

        IMPROVEMENT: The original version did not update the gdrive_tree after
        creating folders, which could cause re-creation of the same folders on
        the next push.  Callers should update the tree externally after this
        returns if they need tree consistency within the same session.
        """
        try:
            last_id = parent_folder_id
            for name in names:
                last_id = self.create_folder(name, last_id)
                _console.print(f"  [cyan]⊕[/] folder [dim]{name}[/]")
            return last_id
        except Exception as e:
            self.logger.error(f"Error in create_folders_for_upload: {e}\n{traceback.format_exc()}")
            raise

    def upload_folder(self, folder_path, parent_folder_id):
        try:
            folder_name = os.path.basename(folder_path)
            folder_id   = self.create_folder(folder_name, parent_folder_id)
            _console.print(f"  [cyan]⊕[/] folder [bold]{folder_name}[/]")

            local_base = ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH
            for item in os.listdir(local_base + folder_path):
                item_path = os.path.join(folder_path, item)
                if os.path.isfile(local_base + item_path):
                    self.upload_file(item_path, folder_id)
                elif os.path.isdir(local_base + item_path):
                    self.upload_folder(item_path, folder_id)

        except Exception as e:
            self.logger.error(f"Error in upload_folder: {e}\n{traceback.format_exc()}")
            raise

    def upload_helper(self, gdrive_tree, folder_path):
        try:
            path_str       = folder_path[0]
            to_upload_path = path_str.split("/")
            nearest_node, folders_created = gdrive_tree.get_node(to_upload_path[1:])
            final_id = nearest_node.id

            if folders_created != len(to_upload_path[1:-1]):
                final_id = self.create_folders_for_upload(
                    to_upload_path[folders_created + 1:], nearest_node.id
                )

            local_full = ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + path_str
            if os.path.isdir(local_full):
                self.upload_folder(path_str, final_id)
            else:
                self.upload_file(path_str, final_id)

        except Exception as e:
            self.logger.error(f"Error in upload_helper: {e}\n{traceback.format_exc()}")
            raise

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def hard_delete_file(self, file_id):
        try:
            self.service.files().delete(fileId=file_id).execute()
            _console.print(f"  [red]✗[/] permanently deleted [dim]{file_id}[/]")
        except Exception as e:
            self.logger.error(f"Error in hard_delete_file: {e}\n{traceback.format_exc()}")
            raise

    def delete_file(self, file_id, gdrive_tree=None):
        try:
            self.service.files().update(fileId=file_id, body={'trashed': True}).execute()

            if gdrive_tree:
                parent = gdrive_tree.find_parent_node_by_id(file_id)
                if parent:
                    for name, child in list(parent.children.items()):
                        if child.id == file_id:
                            del parent.children[name]
                            break

            _console.print(f"  [yellow]🗑[/] moved to trash [dim]{file_id}[/]")
        except Exception as e:
            self.logger.error(f"Error in delete_file: {e}\n{traceback.format_exc()}")
            raise

    # ------------------------------------------------------------------
    # Download
    # ------------------------------------------------------------------

    def download_file(self, output_path, drive_file_id):
        try:
            request  = self.service.files().get_media(fileId=drive_file_id)
            dir_path = os.path.dirname(
                ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + output_path
            )
            os.makedirs(dir_path, exist_ok=True)

            file_name = os.path.basename(output_path)
            local_out = ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + output_path

            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]Downloading[/] [bold]{task.description}[/]"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TransferSpeedColumn(),
                TimeRemainingColumn(),
                console=_console,
            ) as progress:
                task = progress.add_task(file_name, total=100)
                with io.FileIO(local_out, 'wb') as out_file:
                    downloader = MediaIoBaseDownload(out_file, request)
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            progress.update(task, completed=int(status.progress() * 100))
                progress.update(task, completed=100)

            _console.print(f"  [green]↓[/] {output_path}")
        except Exception as e:
            self.logger.error(f"Error in download_file: {e}\n{traceback.format_exc()}")
            raise

    def download_folder(self, output_path, drive_folder_id):
        try:
            os.makedirs(
                ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + output_path, exist_ok=True
            )
            results = self.service.files().list(
                q=f"parents in '{drive_folder_id}'",
                fields="files(id, name, mimeType)"
            ).execute()

            for item in results.get('files', []):
                item_path = os.path.join(output_path, item['name'])
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    self.download_folder(item_path, item['id'])
                else:
                    self.download_file(item_path, item['id'])

        except Exception as e:
            self.logger.error(f"Error in download_folder: {e}\n{traceback.format_exc()}")
            raise

    def download_helper(self, output_path, drive_file_id, isDir):
        try:
            if isDir:
                self.download_folder(output_path, drive_file_id)
            else:
                self.download_file(output_path, drive_file_id)
        except Exception as e:
            self.logger.error(f"Error in download_helper: {e}\n{traceback.format_exc()}")
            raise