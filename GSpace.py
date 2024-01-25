import sys
import ConfigurationManager
import traceback
from FilesystemHelper import FilesystemHelper
from GoogleDriveHelper import GoogleDriveHelper
from Logger import Logger
from Tree import Tree

class GSpace:
    """
    GSpace is a utility for synchronizing files between the local filesystem and Google Drive.

    Usage:
    gspace_instance = GSpace()
    gspace_instance.pull()
    gspace_instance.push()
    gspace_instance.sync()
    """

    logger = Logger()

    def __init__(self):
        """
        Initialize GSpace by creating instances of GoogleDriveHelper, FilesystemHelper, and initializing Google Drive service.
        """
        try:
            self.logger.info("Program Started")
            self.gdrive = GoogleDriveHelper()
            self.filesystem = FilesystemHelper()
            self.gdrive.initialize_service()
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in GSpace initialization: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def fetch(self, updateType="Local Filesystem"):
        """
        Fetch changes from Google Drive and local filesystem, and print the differences.

        Parameters:
        - updateType: Type of update, either "Local Filesystem" or "Google Drive".
        """
        try:
            gdrive_tree, local_fs_tree = Tree(), Tree()
            gdrive_tree.add([ConfigurationManager.ROOT_FOLDER_NAME], ConfigurationManager.ROOT_FOLDER_ID)
            self.gdrive.generate_tree_from_google_drive(gdrive_tree)
            self.filesystem.generate_tree_from_filesystem(local_fs_tree)

            changes_in_local = local_fs_tree.find_difference_path(gdrive_tree)
            changes_in_server = gdrive_tree.find_difference_path(local_fs_tree)
            print("============================================")

            print("Following changes will take place in " + updateType)

            if updateType == "Local Filesystem":
                print(f"Additions ({len(changes_in_server['Additions'])}):")
                for change in changes_in_server["Additions"]: print("+", change[0])
                print(f"Modifications ({len(changes_in_server['Modifications'])}):")
                for change in changes_in_server["Modifications"]: print("*", change[0])
                print(f"Deletions ({len(changes_in_server['Deletions'])}):")
                for change in changes_in_server["Deletions"]: print("-", change[0])
            else:
                print(f"Additions ({len(changes_in_local['Additions'])}):")
                for change in changes_in_local["Additions"]: print("+", change[0])
                print(f"Modifications ({len(changes_in_local['Modifications'])}):")
                for change in changes_in_server["Modifications"]: print("*", change[0])
                print(f"Deletions ({len(changes_in_local['Deletions'])}):")
                for change in changes_in_local["Deletions"]: print("-", change[0])

                

            print("============================================")

            return changes_in_local, changes_in_server, gdrive_tree, local_fs_tree
        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in fetch: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def pull(self):
        """
        Pull changes from Google Drive to the local filesystem.
        """
        try:
            changes_in_local, changes_in_server, gdrive_tree, local_fs_tree = self.fetch()

            if not changes_in_server["Additions"] and not changes_in_server["Deletions"] and not changes_in_server["Modifications"]:
                print("============================================")
                print("No changes to pull!\nExiting ...")
                return print("============================================")

            confirmation = ""

            while confirmation not in ["yes", "no"]:
                confirmation = input("Are you sure you want to continue? [yes, no]\n >>> ")
                if confirmation not in ["yes", "no"]: print("Usage: 'yes' or 'no'")

            if confirmation == "no":
                print("============================================")
                print("Canceled by user!\nExiting ...")
                return print("============================================")

            if len(changes_in_server["Additions"]):
                print("============================================")
                print("Starting pulling changes from Google Drive:")
                for to_download in changes_in_server["Additions"]:
                    self.gdrive.download_helper(to_download[0], to_download[1], to_download[2])

            if len(changes_in_server["Modifications"]):
                print("============================================")
                print("Starting modifications in local Filesystem:")
                print("============================================")

                for to_modify in changes_in_server["Modifications"]:
                    self.filesystem.hard_delete_from_filesystem(to_modify[0])
                    self.gdrive.download_helper(to_modify[0], to_modify[1], to_modify[2])

                print("Finished modification changes from Google Drive!")
                print("============================================")

            if len(changes_in_server["Deletions"]):
                print("============================================")
                print("Starting removing files in local Filesystem:")
                for to_delete in changes_in_server["Deletions"]:
                    self.filesystem.soft_delete_from_filesystem(to_delete[0])

                print("Finished removing files from local Filesystem!")
                print("============================================")

            print("SUCCESS: Pulled Google Drive!")
            self.logger.info("Pulled from google drive")

        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in pull: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def push(self):
        """
        Push changes from the local filesystem to Google Drive.
        """
        try:
            changes_in_local, changes_in_server, gdrive_tree, local_fs_tree = self.fetch(updateType="Google Drive")

            if not changes_in_local["Additions"] and not changes_in_local["Deletions"] and not changes_in_local["Modifications"]:
                print("============================================")
                print("No changes to push!\nExiting ...")
                return print("============================================")

            confirmation = ""

            while confirmation not in ["yes", "no"]:
                confirmation = input("Are you sure you want to continue? [yes, no]\n >>> ")
                if confirmation not in ["yes", "no"]: print("Usage: 'yes' or 'no'")

            if confirmation == "no":
                print("============================================")
                print("Canceled by user!\nExiting ...")
                return print("============================================")

            if len(changes_in_local["Additions"]):
                print("============================================")
                print("Starting pushing changes to Google Drive:")
                for to_upload in changes_in_local["Additions"]:
                    self.gdrive.upload_helper(gdrive_tree, to_upload)

                print("Finished pushing changes to Google Drive!")
                print("============================================")

            if len(changes_in_server["Modifications"]):
                print("============================================")
                print("Starting modifications in Google Drive:")
                print("============================================")

                for to_modify in changes_in_server["Modifications"]:
                    self.gdrive.delete_file(to_modify[1], gdrive_tree=gdrive_tree)
                    self.gdrive.upload_helper(gdrive_tree, to_modify)

                print("Finished modifications in Google Drive!")
                print("============================================")

            if len(changes_in_local["Deletions"]):
                print("============================================")
                print("Starting removing files from Google Drive:")
                for to_delete in changes_in_local["Deletions"]:
                    self.gdrive.delete_file(to_delete[1], gdrive_tree=gdrive_tree)

                print("Finished removing files from Google Drive!")
                print("============================================")

            print("SUCCESS: Pushing to Google Drive!")
            self.logger.info("Pushed to Google Drive")


        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in push: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def sync(self):
        """
        Synchronize changes between the local filesystem and Google Drive.
        """
        try:
            self.pull()
            self.push()

            self.logger.info("Sync from Google Drive and Local System Completed")

        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in sync: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

def main():
    try:
        options = {
            "fetch": "",
            "pull": "",
            "push": "",
            "sync": ""
        }

        if len(sys.argv) != 2:
            return print("Usage: python3 GSpace.py <command>")

        if sys.argv[1] not in options.keys():
            return print("Usage: python3 GSpace.py <command>\nCommands: fetch, pull, push, sync")

        gspace_instance = GSpace()

        options = {
            "fetch": gspace_instance.fetch,
            "pull": gspace_instance.pull,
            "push": gspace_instance.push,
            "sync": gspace_instance.sync
        }

        options[sys.argv[1]]()

        gspace_instance.logger.info(f"SUCCESS: '{sys.argv[1]}'")

    except Exception as e:
        # Log the error using the logger
        Logger().error(f"Error occurred in main: {e}")
        # Optionally, log the full traceback for detailed error information
        Logger().error(traceback.format_exc())
        # Raise the exception again to notify the caller about the error
        raise e

if __name__ == "__main__":
    main()
