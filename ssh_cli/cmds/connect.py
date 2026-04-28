import platform
import subprocess
import time

import inquirer
import pexpect
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


def _prompt_credentials(default_user: str | None) -> tuple[str, str] | None:
    """Ask for SSH username/password used by password authentication."""
    questions = [
        inquirer.Text(
            "username",
            message="Enter SSH username",
            default=default_user or "",
            validate=is_not_empty,
        ),
        inquirer.Password(
            "password",
            message="Enter SSH password",
            validate=is_not_empty,
        ),
    ]

    answers = inquirer.prompt(questions)
    if answers is None:
        return None

    return answers["username"], answers["password"]


def _connect_with_password(host: str, username: str, password: str) -> int:
    """Open an interactive SSH session and answer initial auth prompts."""
    ssh_args = [
        "-o",
        "PreferredAuthentications=password",
        "-o",
        "PubkeyAuthentication=no",
        "-l",
        username,
        host,
    ]

    child = pexpect.spawn("ssh", ssh_args, encoding="utf-8")

    while True:
        prompt_index = child.expect(
            [
                r"Are you sure you want to continue connecting \(yes/no(?:/\[fingerprint\])?\)\?",
                r"[Pp]assword:",
                r"Permission denied",
                pexpect.EOF,
                pexpect.TIMEOUT,
            ],
            timeout=30,
        )

        if prompt_index == 0:
            child.sendline("yes")
            continue

        if prompt_index == 1:
            child.sendline(password)
            break

        if prompt_index == 2:
            cprint("SSH login failed: Permission denied", "red")
            child.close()
            return 1

        if prompt_index == 3:
            child.close()
            return child.exitstatus if child.exitstatus is not None else 1

        cprint("Timed out waiting for SSH authentication prompt.", "red")
        child.close()
        return 1

    try:
        child.interact()
    finally:
        child.close()

    return child.exitstatus if child.exitstatus is not None else 0


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
        credentials = _prompt_credentials(host_config.get("user"))

        if credentials is None:
            cprint("SSH login cancelled.", "yellow")
            return 1

        username, password = credentials
        return _connect_with_password(host, username, password)
