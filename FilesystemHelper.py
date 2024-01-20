import os
import shutil
import traceback
import ConfigurationManager
from datetime import datetime
from Logger import Logger

class FilesystemHelper:
    """
    A utility class for interacting with the filesystem, including generating trees and performing soft deletes.

    Usage:
    filesystem_helper = FilesystemHelper()
    filesystem_helper.generate_tree_from_filesystem(tree)
    filesystem_helper.soft_delete_from_filesystem("/example/file.txt")
    """

    logger = Logger()

    def __init__(self):
        """
        Initialize FilesystemHelper with folder and backup paths from ConfigurationManager.
        """
        self.FOLDER_PATH = ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH
        self.BACKUP_FOLDER_PATH = ConfigurationManager.BACKUP_FOLDER_PATH

    def generate_tree_from_filesystem(self, tree):
        """
        Generate a tree structure based on the current filesystem.

        Parameters:
        - tree: An instance of the Tree class to store the filesystem structure.
        """
        try:
            # Function to add files and subdirectories to the tree
            root_value = os.path.basename(self.FOLDER_PATH)
            tree.add([root_value])

            def add_recursive(current_node, current_path):
                for item in os.listdir(current_path):
                    item_path = os.path.join(current_path, item)
                    if os.path.isdir(item_path):
                        # If it's a directory, add it as a child and recurse
                        child_value = os.path.basename(item_path)
                        tree.add(current_node + [child_value])
                        add_recursive(current_node + [child_value], item_path)
                    else:
                        # If it's a file, add it directly
                        tree.add(current_node + [item])

            # Start the traversal from the root of the tree
            add_recursive([root_value], self.FOLDER_PATH)

        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in generate_tree_from_filesystem: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e

    def soft_delete_from_filesystem(self, path):
        """
        Soft delete a file or directory from the filesystem.

        Parameters:
        - path: The path of the file or directory to be soft deleted.
        """
        try:
            backup_dir_name = datetime.now().strftime('%d-%m-%Y')
            os.makedirs(f"{ConfigurationManager.BACKUP_FOLDER_PATH + '/' + backup_dir_name}", exist_ok=True)

            if os.path.exists(ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + path):
                dir_path = ConfigurationManager.BACKUP_FOLDER_PATH + "/" + datetime.now().strftime('%d-%m-%Y') + "/" + "/".join(path.split("/")[:-1])
                os.makedirs(dir_path, exist_ok=True)
                shutil.move(ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + path, dir_path)
                print("Deleted Successfully!")
                print(f"Path: {ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + path}")
                print(f"Backup path: {dir_path}")
            else:
                print(f"Path does not exist: {ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + path}")

            print("============================================")

        except Exception as e:
            # Log the error using the logger
            self.logger.error(f"Error occurred in soft_delete_from_filesystem: {e}")
            # Optionally, log the full traceback for detailed error information
            self.logger.error(traceback.format_exc())
            # Raise the exception again to notify the caller about the error
            raise e
