import re
from pathlib import Path

from termcolor import cprint
from .interface import Command
from ..config import CONFIG_FILE_PATH
from ..lib import confirm_action


class RemoveUser(Command):
    """Remove all `User` directives from the SSH config file."""

    @property
    def cmd(self):
        return "remove-user"

    @property
    def help(self):
        return "Remove all `User` entries from the ssh config"

    def run(self, *args, **kwargs) -> int:
        path = Path(CONFIG_FILE_PATH)

        if not path.exists():
            cprint(f"Config file not found at {CONFIG_FILE_PATH}", "red")
            return 1

        text = path.read_text()
        lines = text.splitlines()

        pattern = re.compile(r"^\s*User\s+.*$", re.IGNORECASE)
        new_lines = [ln for ln in lines if not pattern.match(ln)]

        if len(new_lines) == len(lines):
            cprint("No `User` entries found in the ssh config.", "yellow")
            return 0

        cprint(f"Found {len(lines) - len(new_lines)} `User` entries in {CONFIG_FILE_PATH}", "yellow")

        if not confirm_action("Remove all `User` entries from the ssh config file?"):
            cprint("Aborted.", "yellow")
            return 1

        # backup original first, then write the cleaned file
        backup_path = f"{CONFIG_FILE_PATH}.bak"
        Path(backup_path).write_text(text)
        path.write_text("\n".join(new_lines) + ("\n" if text.endswith("\n") else ""))

        cprint(f"Removed `User` entries and backed up original to {backup_path}", "green")
        return 0
