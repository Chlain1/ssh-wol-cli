import os
import subprocess

import inquirer
import validators
from sshconf import read_ssh_config
from termcolor import cprint

from .interface import Command
from ..config import DEFAULT_USER, SSH_DEFAULT_PORT, CONFIG_FILE_PATH, KEY_DIR_PATH, KEY_TYPE
from ..lib import show_host_config
from ..metadata import set_host_wol_config
from ..validation import (
    is_valid_hostname,
    is_not_empty,
    host_exists,
    is_number,
    is_valid_mac_addresses,
    is_valid_wol_target_ip,
    parse_mac_addresses,
    parse_wol_target_ip,
)


def _create_key_file(host) -> str | None:
    if not inquirer.confirm("Do you want to use a passkey?", default=True):
        return None
    password = inquirer.password("Enter a password for the key file (optional)") or ""
    key_file = f'{KEY_DIR_PATH}/{host}'
    res = subprocess.run(
        ["ssh-keygen",
         "-t", KEY_TYPE,
         "-C", f"'key_for_{host}'",
         "-f", key_file,
         "-N", password,
         "-q"
         ])
    if res.returncode != 0:
        cprint(f"Error creating key file: {res.stderr}", "red")
        return None
    return key_file


class CreateHostConfig(Command):
    """
    This class prompts the user to enter the details for a new host and then creates it in the ssh config file.
    """

    @property
    def help(self):
        return "Create a new host"

    @property
    def cmd(self):
        return "create"

    def run(self, *args, **kwargs) -> int:
        """
        This function prompts the user to enter the details for a new host and then creates it in the ssh config file.
        It also prompts the user to create a key file for the host.
        """
        c = read_ssh_config(CONFIG_FILE_PATH)

        host_config_questions = [
            inquirer.Text(
                "hostname",
                message="Hostname (e.g. example.com)",
                validate=is_valid_hostname
            ),
            inquirer.Text(
                "host",
                message="Enter a name for this host (e.g. example)",
                validate=lambda _, x: is_not_empty(_, x) and host_exists(_, x),
                default=lambda ans: ans["hostname"].split(".")[0] if validators.domain(ans["hostname"]) else None
            ),
            inquirer.Text(
                "user",
                message="Enter the username for this host",
                default=DEFAULT_USER
            ),
            inquirer.Text(
                "port",
                message="Enter the port for this host",
                default=SSH_DEFAULT_PORT,
                validate=is_number
            ),
            inquirer.Text(
                "wol_macs",
                message="Wake-on-LAN MAC addresses (optional, max 2, comma-separated)",
                validate=is_valid_mac_addresses,
                default=""
            ),
            inquirer.Text(
                "wol_target_ip",
                message="Wake-on-LAN target IP (wakeonlan -i target)",
                validate=is_valid_wol_target_ip,
                default=lambda ans: ans["hostname"] if validators.ipv4(ans["hostname"]) else ""
            ),
        ]

        if (answers := inquirer.prompt(host_config_questions)) is None:
            return 1

        wol_macs = parse_mac_addresses(answers["wol_macs"])
        wol_target_ip = parse_wol_target_ip(answers["wol_target_ip"])

        if wol_macs and not wol_target_ip:
            cprint("Wake-on-LAN target IP is required when MAC addresses are configured.", "red")
            return 1

        # Do not write the `User` to the ssh config so the username is always
        # prompted at connection time. Store only hostname and port (and
        # identityfile if created).
        c.add(answers["host"], Hostname=answers["hostname"], Port=answers["port"])

        if key_file := _create_key_file(answers["host"]):
            c.set(answers["host"], IdentityFile=key_file)

        print("Host configured with the following configuration:")
        show_host_config(
            answers["host"],
            c,
            mac_addresses=wol_macs,
            wol_target_ip=wol_target_ip,
        )

        if not inquirer.confirm("Do you want to save this host?", default=True):
            if key_file:
                os.remove(key_file)
                os.remove(f'{key_file}.pub')
            cprint(f'Host {answers["host"]} not saved', "yellow")
            return 1

        c.write(CONFIG_FILE_PATH)
        set_host_wol_config(answers["host"], wol_macs, wol_target_ip)
        cprint(f'Host {answers["host"]} saved', "green")

        return 0
