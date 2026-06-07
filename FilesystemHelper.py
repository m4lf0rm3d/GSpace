import fnmatch
import os
import shutil
import traceback
import ConfigurationManager
from datetime import datetime
from Logger import Logger
from rich.console import Console

_console = Console()

# Default patterns that are never synced regardless of .gspaceignore.
# Covers build artefacts and dependency folders for all common stacks.
_DEFAULT_IGNORE = {
    # Python
    "venv", ".venv", "__pycache__", "*.pyc", "*.pyo", ".pytest_cache",
    # Node / JS / TS / Angular / React
    "node_modules", "dist", ".next", ".nuxt", ".angular", "build", ".cache",
    # .NET / C#
    "bin", "obj", ".vs",
    # C / C++
    "*.o", "*.out", "*.a", "*.so", "*.dll", "*.exe",
    # General VCS / IDE
    ".git", ".idea", ".vscode",
    # GSpace own files
    "token.json", "token.pickle",
}

IGNORE_FILE = ".gspaceignore"


def _load_ignore_patterns(root: str) -> set:
    """
    Read <root>/.gspaceignore and merge with built-in defaults.
    Each non-blank, non-comment line is treated as a fnmatch pattern.
    """
    patterns = set(_DEFAULT_IGNORE)
    ignore_path = os.path.join(root, IGNORE_FILE)
    if os.path.exists(ignore_path):
        with open(ignore_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    patterns.add(line)
    return patterns


def _is_ignored(name: str, patterns: set) -> bool:
    """Return True if *name* matches any ignore pattern."""
    return any(fnmatch.fnmatch(name, p) for p in patterns)


class FilesystemHelper:
    """
    Utility for local filesystem operations: tree generation, soft delete, hard delete.
    Respects .gspaceignore (plus built-in defaults) so ignored paths are invisible
    to the diff engine — they are never pushed, pulled, or deleted.
    """

    logger = Logger()

    def __init__(self):
        self.FOLDER_PATH        = ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH
        self.BACKUP_FOLDER_PATH = ConfigurationManager.BACKUP_FOLDER_PATH

    def generate_tree_from_filesystem(self, tree):
        try:
            root_value = os.path.basename(self.FOLDER_PATH)
            tree.add([root_value])

            ignore_patterns = _load_ignore_patterns(self.FOLDER_PATH)

            def add_recursive(current_node, current_path):
                for item in os.listdir(current_path):
                    if _is_ignored(item, ignore_patterns):
                        continue          # skip silently — not in tree, not in diff
                    item_path = os.path.join(current_path, item)
                    if os.path.isdir(item_path):
                        tree.add(current_node + [item], isDir=True)
                        add_recursive(current_node + [item], item_path)
                    else:
                        tree.add(current_node + [item], fileSize=os.path.getsize(item_path), isDir=False)

            add_recursive([root_value], self.FOLDER_PATH)

        except Exception as e:
            self.logger.error(f"Error in generate_tree_from_filesystem: {e}\n{traceback.format_exc()}")
            raise

    def soft_delete_from_filesystem(self, path):
        try:
            backup_dir = os.path.join(
                ConfigurationManager.BACKUP_FOLDER_PATH,
                datetime.now().strftime('%d-%m-%Y'),
                os.path.dirname(path).lstrip('/')
            )
            os.makedirs(backup_dir, exist_ok=True)

            src = ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + path
            if os.path.exists(src):
                shutil.move(src, backup_dir)
                _console.print(f"  [yellow]↪[/] [dim]{path}[/] → backup")
            else:
                _console.print(f"  [dim]skip (not found):[/] {path}")

        except Exception as e:
            self.logger.error(f"Error in soft_delete_from_filesystem: {e}\n{traceback.format_exc()}")
            raise

    def hard_delete_from_filesystem(self, path):
        try:
            file_path = ConfigurationManager.LOCAL_FILESYSTEM_FOLDER_PATH + path
            if os.path.exists(file_path):
                os.remove(file_path)
                _console.print(f"  [red]✗[/] deleted [dim]{path}[/]")
            else:
                _console.print(f"  [dim]skip (not found):[/] {path}")

        except Exception as e:
            self.logger.error(f"Error in hard_delete_from_filesystem: {e}\n{traceback.format_exc()}")
            raise