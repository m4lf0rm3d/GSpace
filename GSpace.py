import sys
import traceback
import ConfigurationManager
from FilesystemHelper import FilesystemHelper
from GoogleDriveHelper import GoogleDriveHelper
from Logger import Logger
from Tree import Tree

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from rich.columns import Columns
from rich.rule import Rule
from rich.prompt import Confirm

_console = Console()


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def _changes_table(changes: dict, title: str) -> Table:
    """Build a rich Table summarising a changes dictionary."""
    table = Table(
        title=title,
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
        border_style="dim",
        expand=True,
    )
    table.add_column("Op", width=4, justify="center")
    table.add_column("Path")
    table.add_column("Type", width=9, justify="center")

    for path, fid, is_dir in changes["Additions"]:
        table.add_row(
            "[green]+[/]",
            f"[green]{path}[/]",
            "[cyan]folder[/]" if is_dir else "[dim]file[/]",
        )
    for path, fid, is_dir in changes["Modifications"]:
        table.add_row(
            "[yellow]~[/]",
            f"[yellow]{path}[/]",
            "[cyan]folder[/]" if is_dir else "[dim]file[/]",
        )
    for path, fid, is_dir in changes["Deletions"]:
        table.add_row(
            "[red]−[/]",
            f"[red]{path}[/]",
            "[cyan]folder[/]" if is_dir else "[dim]file[/]",
        )

    return table


def _summary_panel(changes: dict, label: str) -> Panel:
    adds  = len(changes["Additions"])
    mods  = len(changes["Modifications"])
    dels  = len(changes["Deletions"])
    total = adds + mods + dels

    if total == 0:
        text = Text("No changes", style="dim")
    else:
        text = Text()
        if adds: text.append(f"  +{adds} add{'s' if adds != 1 else ''}  ", style="green")
        if mods: text.append(f"  ~{mods} mod{'s' if mods != 1 else ''}  ", style="yellow")
        if dels: text.append(f"  −{dels} del{'s' if dels != 1 else ''}  ", style="red")

    return Panel(text, title=f"[bold]{label}[/]", border_style="dim", expand=True)


def _header():
    _console.print()
    _console.print(
        Panel(
            f"[bold cyan]GSpace[/]  [dim]v{ConfigurationManager.APP_VERSION}[/]",
            subtitle="[dim]Google Drive ↔ Local Filesystem[/]",
            border_style="cyan",
            expand=False,
        )
    )
    _console.print()


# ──────────────────────────────────────────────────────────────────────────────
# GSpace
# ──────────────────────────────────────────────────────────────────────────────

class GSpace:
    """
    GSpace — sync files between local filesystem and Google Drive.

    Usage:
        gspace = GSpace()
        gspace.pull()
        gspace.push()
        gspace.sync()
    """

    logger = Logger()

    def __init__(self):
        try:
            self.logger.info("Program started")
            self.gdrive     = GoogleDriveHelper()
            self.filesystem = FilesystemHelper()
            self.gdrive.initialize_service()
        except Exception as e:
            self.logger.error(f"Init error: {e}\n{traceback.format_exc()}")
            raise

    # ------------------------------------------------------------------
    # fetch
    # ------------------------------------------------------------------

    def fetch(self, update_type="Local Filesystem"):
        """
        Build both trees, diff them, and print a summary.
        Returns (changes_in_local, changes_in_server, gdrive_tree, local_fs_tree).
        """
        try:
            with _console.status("[bold cyan]Reading Google Drive…[/]", spinner="dots"):
                gdrive_tree = Tree()
                gdrive_tree.add(
                    [ConfigurationManager.ROOT_FOLDER_NAME],
                    ConfigurationManager.ROOT_FOLDER_ID
                )
                self.gdrive.generate_tree_from_google_drive(gdrive_tree)

            with _console.status("[bold cyan]Reading local filesystem…[/]", spinner="dots"):
                local_fs_tree = Tree()
                self.filesystem.generate_tree_from_filesystem(local_fs_tree)

            changes_in_local  = local_fs_tree.find_difference_path(gdrive_tree)
            changes_in_server = gdrive_tree.find_difference_path(local_fs_tree)

            _console.print(Rule("[bold]Pending changes[/]", style="dim"))
            _console.print()

            if update_type == "Local Filesystem":
                _console.print(
                    Columns([
                        _summary_panel(changes_in_server, "→ Local filesystem"),
                    ], expand=True)
                )
                if any(changes_in_server.values()):
                    _console.print(_changes_table(changes_in_server, "Changes coming from Google Drive"))
            else:
                _console.print(
                    Columns([
                        _summary_panel(changes_in_local, "→ Google Drive"),
                    ], expand=True)
                )
                if any(changes_in_local.values()):
                    _console.print(_changes_table(changes_in_local, "Changes going to Google Drive"))

            _console.print()

            return changes_in_local, changes_in_server, gdrive_tree, local_fs_tree

        except Exception as e:
            self.logger.error(f"fetch error: {e}\n{traceback.format_exc()}")
            raise

    # ------------------------------------------------------------------
    # pull
    # ------------------------------------------------------------------

    def pull(self):
        """Download changes from Google Drive to the local filesystem."""
        try:
            changes_local, changes_server, gdrive_tree, local_tree = self.fetch()

            if not any(changes_server.values()):
                _console.print("[dim]Nothing to pull.[/]")
                return

            if not Confirm.ask("[bold]Apply these changes to local filesystem?[/]"):
                _console.print("[dim]Canceled.[/]")
                return

            _console.print()

            if changes_server["Additions"]:
                _console.print(Rule("[green]Downloading additions[/]", style="dim"))
                for path, fid, is_dir in changes_server["Additions"]:
                    self.gdrive.download_helper(path, fid, is_dir)

            if changes_server["Modifications"]:
                _console.print(Rule("[yellow]Applying modifications[/]", style="dim"))
                for path, fid, is_dir in changes_server["Modifications"]:
                    self.filesystem.hard_delete_from_filesystem(path)
                    self.gdrive.download_helper(path, fid, is_dir)

            if changes_server["Deletions"]:
                _console.print(Rule("[red]Removing deleted files[/]", style="dim"))
                for path, fid, is_dir in changes_server["Deletions"]:
                    self.filesystem.soft_delete_from_filesystem(path)

            _console.print()
            _console.print(Panel("[bold green]✓ Pull complete[/]", border_style="green", expand=False))
            self.logger.info("Pull from Google Drive complete")

        except Exception as e:
            self.logger.error(f"pull error: {e}\n{traceback.format_exc()}")
            raise

    # ------------------------------------------------------------------
    # push
    # ------------------------------------------------------------------

    def push(self):
        """Upload local changes to Google Drive."""
        try:
            changes_local, changes_server, gdrive_tree, local_tree = self.fetch(update_type="Google Drive")

            if not any(changes_local.values()):
                _console.print("[dim]Nothing to push.[/]")
                return

            if not Confirm.ask("[bold]Apply these changes to Google Drive?[/]"):
                _console.print("[dim]Canceled.[/]")
                return

            _console.print()

            if changes_local["Additions"]:
                _console.print(Rule("[green]Uploading additions[/]", style="dim"))
                for item in changes_local["Additions"]:
                    self.gdrive.upload_helper(gdrive_tree, item)

            if changes_server["Modifications"]:
                _console.print(Rule("[yellow]Applying modifications[/]", style="dim"))
                for path, fid, is_dir in changes_server["Modifications"]:
                    self.gdrive.delete_file(fid, gdrive_tree=gdrive_tree)
                    self.gdrive.upload_helper(gdrive_tree, (path, fid, is_dir))

            if changes_local["Deletions"]:
                _console.print(Rule("[red]Removing deleted files[/]", style="dim"))
                for path, fid, is_dir in changes_local["Deletions"]:
                    self.gdrive.delete_file(fid, gdrive_tree=gdrive_tree)

            _console.print()
            _console.print(Panel("[bold green]✓ Push complete[/]", border_style="green", expand=False))
            self.logger.info("Push to Google Drive complete")

        except Exception as e:
            self.logger.error(f"push error: {e}\n{traceback.format_exc()}")
            raise

    # ------------------------------------------------------------------
    # sync
    # ------------------------------------------------------------------

    def sync(self):
        """Pull then push — full two-way sync."""
        try:
            _console.print(Rule("[bold cyan]Pull phase[/]", style="cyan"))
            self.pull()
            _console.print()
            _console.print(Rule("[bold cyan]Push phase[/]", style="cyan"))
            self.push()
            _console.print()
            _console.print(Panel("[bold green]✓ Sync complete[/]", border_style="green", expand=False))
            self.logger.info("Sync complete")
        except Exception as e:
            self.logger.error(f"sync error: {e}\n{traceback.format_exc()}")
            raise


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────

COMMANDS = ("fetch", "pull", "push", "sync")


def main():
    _header()

    if len(sys.argv) != 2 or sys.argv[1] not in COMMANDS:
        _console.print(
            Panel(
                f"[bold]Usage:[/]  python3 GSpace.py [cyan]<command>[/]\n\n"
                f"[bold]Commands:[/]  {', '.join(f'[cyan]{c}[/]' for c in COMMANDS)}",
                title="[bold red]Invalid usage[/]",
                border_style="red",
                expand=False,
            )
        )
        sys.exit(1)

    cmd = sys.argv[1]

    try:
        gspace = GSpace()
        getattr(gspace, cmd)()
        gspace.logger.info(f"SUCCESS: '{cmd}'")
    except KeyboardInterrupt:
        _console.print("\n[dim]Interrupted.[/]")
        sys.exit(0)
    except Exception as e:
        Logger().error(f"Fatal error in '{cmd}': {e}\n{traceback.format_exc()}")
        _console.print_exception(show_locals=False)
        sys.exit(1)


if __name__ == "__main__":
    main()