import inquirer
from sshconf import read_ssh_config
from termcolor import cprint

from .interface import Command
from ..config import CONFIG_FILE_PATH, DEFAULT_USER, SSH_DEFAULT_PORT
from ..lib import select_host, show_host_config
from ..metadata import get_host_macs, set_host_macs
from ..validation import (
    is_valid_hostname,
    is_not_empty,
    is_number,
    is_valid_mac_addresses,
    parse_mac_addresses,
)


class EditHostConfig(Command):
    """Edit an existing host and its Wake-on-LAN MAC addresses."""

    @property
    def help(self):
        return "Edit an existing host"

    @property
    def cmd(self):
        return "edit"

    def run(self, *args, **kwargs) -> int:
        c = read_ssh_config(CONFIG_FILE_PATH)

        if not (host := select_host()):
            return 1

        if not (host_config := c.host(host)):
            cprint(f"No SSH config found for host '{host}'.", "red")
            return 1

        host_questions = [
            inquirer.Text(
                "hostname",
                message="Hostname (e.g. example.com)",
                default=host_config.get("hostname") or host,
                validate=is_valid_hostname,
            ),
            inquirer.Text(
                "user",
                message="Username",
                default=host_config.get("user") or DEFAULT_USER or "",
                validate=is_not_empty,
            ),
            inquirer.Text(
                "port",
                message="Port",
                default=str(host_config.get("port") or SSH_DEFAULT_PORT),
                validate=is_number,
            ),
            inquirer.Text(
                "wol_macs",
                message="Wake-on-LAN MAC addresses (optional, max 2, comma-separated)",
                default=", ".join(get_host_macs(host)),
                validate=is_valid_mac_addresses,
            ),
        ]

        if (answers := inquirer.prompt(host_questions)) is None:
            return 1

        wol_macs = parse_mac_addresses(answers["wol_macs"])

        c.set(host, Hostname=answers["hostname"])
        c.set(host, User=answers["user"])
        c.set(host, Port=answers["port"])

        print("Updated host configuration:")
        show_host_config(host, c, mac_addresses=wol_macs)

        if not inquirer.confirm("Do you want to save these changes?", default=True):
            cprint(f"Changes for host {host} not saved", "yellow")
            return 1

        c.write(CONFIG_FILE_PATH)
        set_host_macs(host, wol_macs)
        cprint(f"Host {host} updated", "green")

        return 0
