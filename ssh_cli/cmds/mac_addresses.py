import inquirer
from sshconf import read_ssh_config
from termcolor import cprint

from .interface import Command
from ..config import CONFIG_FILE_PATH
from ..lib import select_host, show_host_config
from ..metadata import get_host_macs, set_host_macs
from ..validation import is_valid_mac_addresses, parse_mac_addresses


class MacAddresses(Command):
    """Manage Wake-on-LAN MAC addresses for an existing host."""

    @property
    def help(self):
        return "Manage Wake-on-LAN MAC addresses"

    @property
    def cmd(self):
        return "macs"

    def run(self, *args, **kwargs) -> int:
        c = read_ssh_config(CONFIG_FILE_PATH)

        if not (host := select_host()):
            return 1

        if c.host(host) is None:
            cprint(f"No SSH config found for host '{host}'.", "red")
            return 1

        questions = [
            inquirer.Text(
                "wol_macs",
                message="Wake-on-LAN MAC addresses (optional, max 2, comma-separated)",
                default=", ".join(get_host_macs(host)),
                validate=is_valid_mac_addresses,
            ),
        ]

        if (answers := inquirer.prompt(questions)) is None:
            return 1

        wol_macs = parse_mac_addresses(answers["wol_macs"])

        print("Updated MAC address configuration:")
        show_host_config(host, c, mac_addresses=wol_macs)

        if not inquirer.confirm("Do you want to save these MAC addresses?", default=True):
            cprint(f"MAC address changes for host {host} not saved", "yellow")
            return 1

        set_host_macs(host, wol_macs)
        cprint(f"MAC addresses for host {host} updated", "green")
        return 0