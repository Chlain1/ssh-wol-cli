import inquirer
from sshconf import read_ssh_config
from termcolor import cprint

from .interface import Command
from ..config import CONFIG_FILE_PATH, DEFAULT_USER, SSH_DEFAULT_PORT
from ..lib import select_host, show_host_config
from ..metadata import get_host_macs, get_host_wol_target_ip, set_host_wol_config
from ..validation import (
    is_valid_hostname,
    is_not_empty,
    is_number,
    is_valid_mac_addresses,
    is_valid_wol_target_ip,
    parse_mac_addresses,
    parse_wol_target_ip,
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
                # Do not keep username in the config; always ask at connect time.
                # We therefore don't prompt to edit a stored `User` value here.
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
            inquirer.Text(
                "wol_target_ip",
                message="Wake-on-LAN target IP (wakeonlan -i target)",
                default=get_host_wol_target_ip(host),
                validate=is_valid_wol_target_ip,
            ),
        ]

        if (answers := inquirer.prompt(host_questions)) is None:
            return 1

        wol_macs = parse_mac_addresses(answers["wol_macs"])
        wol_target_ip = parse_wol_target_ip(answers["wol_target_ip"])

        if wol_macs and not wol_target_ip:
            cprint("Wake-on-LAN target IP is required when MAC addresses are configured.", "red")
            return 1

        c.set(host, Hostname=answers["hostname"])
        # Intentionally do not set `User` on the host configuration so the
        # username is not stored in the ssh config file.
        c.set(host, Port=answers["port"])

        print("Updated host configuration:")
        show_host_config(host, c, mac_addresses=wol_macs, wol_target_ip=wol_target_ip)

        if not inquirer.confirm("Do you want to save these changes?", default=True):
            cprint(f"Changes for host {host} not saved", "yellow")
            return 1

        c.write(CONFIG_FILE_PATH)
        set_host_wol_config(host, wol_macs, wol_target_ip)
        cprint(f"Host {host} updated", "green")

        return 0
