import inquirer
from sshconf import read_ssh_config
from termcolor import cprint

from .interface import Command
from ..config import CONFIG_FILE_PATH
from ..lib import select_host, show_host_config
from ..metadata import get_host_macs, get_host_wol_target_ip, set_host_wol_config
from ..validation import (
    is_valid_mac_addresses,
    is_valid_wol_target_ip,
    parse_mac_addresses,
    parse_wol_target_ip,
)


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
            inquirer.Text(
                "wol_target_ip",
                message="Wake-on-LAN target IP (wakeonlan -i target)",
                default=get_host_wol_target_ip(host),
                validate=is_valid_wol_target_ip,
            ),
        ]

        if (answers := inquirer.prompt(questions)) is None:
            return 1

        wol_macs = parse_mac_addresses(answers["wol_macs"])
        wol_target_ip = parse_wol_target_ip(answers["wol_target_ip"])

        if wol_macs and not wol_target_ip:
            cprint("Wake-on-LAN target IP is required when MAC addresses are configured.", "red")
            return 1

        print("Updated MAC address configuration:")
        show_host_config(host, c, mac_addresses=wol_macs, wol_target_ip=wol_target_ip)

        if not inquirer.confirm("Do you want to save these MAC addresses?", default=True):
            cprint(f"MAC address changes for host {host} not saved", "yellow")
            return 1

        set_host_wol_config(host, wol_macs, wol_target_ip)
        cprint(f"MAC addresses for host {host} updated", "green")
        return 0