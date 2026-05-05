import platform
import subprocess
import time

import inquirer
from sshconf import read_ssh_config
from termcolor import cprint
from wakeonlan import send_magic_packet

from .interface import Command
from ..config import CONFIG_FILE_PATH
from ..lib import select_host
from ..metadata import get_host_macs, get_host_wol_target_ip
from ..validation import is_not_empty

PING_TIMEOUT_SECONDS = 60


def _is_pingable(hostname: str) -> bool:
    """Return True when the host answers a single ping."""
    ping_command = ["ping", "-n", "1", "-w", "1000", hostname]

    if platform.system().lower() != "windows":
        ping_command = ["ping", "-c", "1", "-W", "1", hostname]

    result = subprocess.run(ping_command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return result.returncode == 0


def _wait_until_pingable(hostname: str, timeout_seconds: int = PING_TIMEOUT_SECONDS) -> bool:
    """Wait until a host is pingable or timeout is reached."""
    deadline = time.monotonic() + timeout_seconds

    while time.monotonic() < deadline:
        if _is_pingable(hostname):
            return True
        time.sleep(2)

    return False


def _send_wol_packets(wol_target_ip: str, mac_addresses: list[str]) -> bool:
    """Send one Wake-on-LAN magic packet per configured MAC address to a target IP."""
    for mac_address in mac_addresses:
        try:
            # Match `wakeonlan -i <ip> <mac>` behavior.
            send_magic_packet(mac_address, ip_address=wol_target_ip)
        except OSError as exc:
            cprint(f"Could not send Wake-on-LAN packet for {mac_address}: {exc}", "red")
            return False

    return True


def _prompt_credentials(default_user: str | None) -> str | None:
    """Ask for the SSH username used by password authentication."""
    questions = [
        inquirer.Text(
            "username",
            message="Enter SSH username",
            default=default_user or "",
            validate=is_not_empty,
        ),
    ]

    answers = inquirer.prompt(questions)
    if answers is None:
        return None

    return answers["username"]


def _connect_with_ssh(host: str, username: str) -> int:
    """Start an interactive SSH session and let ssh handle the password prompt."""
    ssh_args = [
        "-o",
        "PreferredAuthentications=password",
        "-o",
        "PubkeyAuthentication=no",
        "-l",
        username,
        host,
    ]

    code = subprocess.run(["ssh", *ssh_args])
    return code.returncode


class Connect(Command):
    """
    This class implements the "connect" command that connects to a host.
    """

    @property
    def help(self):
        return "Connect to a host via ssh"

    @property
    def cmd(self):
        return "connect"

    def run(self, *args, **kwargs) -> int:
        """
        This function prompts the user to select a host from the ssh config file and then connects to it.
        """
        if not (host := select_host()):
            return 1

        c = read_ssh_config(CONFIG_FILE_PATH)
        host_config = c.host(host)

        if not host_config:
            cprint(f"No SSH config found for host '{host}'.", "red")
            return 1

        hostname = host_config.get("hostname") or host
        mac_addresses = get_host_macs(host)
        wol_target_ip = get_host_wol_target_ip(host)

        if not mac_addresses:
            cprint(f"No Wake-on-LAN MAC addresses configured for host '{host}', trying direct SSH.", "yellow")
            code = subprocess.run(["ssh", host])
            return code.returncode

        if not wol_target_ip:
            cprint(
                f"No Wake-on-LAN target IP configured for host '{host}'. Configure it via edit/macs command.",
                "red",
            )
            return 1

        cprint(f"Sending Wake-on-LAN packets to {wol_target_ip} ...", "green")
        if not _send_wol_packets(wol_target_ip, mac_addresses):
            return 1

        cprint(f"Waiting up to {PING_TIMEOUT_SECONDS}s for {hostname} to become pingable ...", "yellow")
        if not _wait_until_pingable(hostname):
            cprint(f"Host '{host}' is still not reachable after {PING_TIMEOUT_SECONDS}s.", "red")
            return 1

        cprint(f"Host '{host}' is reachable. Starting SSH login ...", "green")
        # Always prompt for username without pre-filling it from the config.
        credentials = _prompt_credentials(None)

        if credentials is None:
            cprint("SSH login cancelled.", "yellow")
            return 1

        username = credentials
        return _connect_with_ssh(host, username)
