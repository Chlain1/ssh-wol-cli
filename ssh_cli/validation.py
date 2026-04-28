import re

import validators
from inquirer.errors import ValidationError
from sshconf import read_ssh_config

from .config import CONFIG_FILE_PATH

MAC_REGEX = re.compile(r"^[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){5}$")


def normalize_mac_address(value: str) -> str:
    """Normalize a MAC address to lower-case colon notation."""
    mac_address = value.strip().replace("-", ":").lower()

    if not MAC_REGEX.match(mac_address):
        raise ValueError(f"Invalid MAC address: {value}")

    return mac_address


def parse_mac_addresses(value: str | None, max_count: int = 2) -> list[str]:
    """Parse and validate a comma-separated MAC address list."""
    if not value:
        return []

    addresses = [entry.strip() for entry in value.split(",") if entry.strip()]

    if len(addresses) > max_count:
        raise ValueError(f"At most {max_count} MAC addresses are allowed")

    parsed_addresses: list[str] = []
    for address in addresses:
        normalized = normalize_mac_address(address)
        if normalized in parsed_addresses:
            raise ValueError("Duplicate MAC addresses are not allowed")
        parsed_addresses.append(normalized)

    return parsed_addresses


def parse_wol_target_ip(value: str | None) -> str:
    """Parse and validate a Wake-on-LAN target IPv4 address."""
    target_ip = (value or "").strip()

    if not target_ip:
        return ""

    if not validators.ipv4(target_ip):
        raise ValueError("Wake-on-LAN target IP must be a valid IPv4 address")

    return target_ip


def is_valid_mac_addresses(_, x):
    """Validate optional comma-separated MAC addresses for Wake-on-LAN."""
    try:
        parse_mac_addresses(x)
    except ValueError as exc:
        raise ValidationError(x, reason=str(exc))

    return True


def is_valid_wol_target_ip(_, x):
    """Validate optional Wake-on-LAN target IPv4 address."""
    try:
        parse_wol_target_ip(x)
    except ValueError as exc:
        raise ValidationError(x, reason=str(exc))

    return True


def is_number(_, x):
    """
    This function checks if a given input is a number.
    :param x: what to check
    :return: True if x is a number, raises a ValidationError otherwise
    """
    if not x.isdigit():
        raise ValidationError(x, reason='Must be a number')
    else:
        return True


def is_not_empty(_, x):
    """
    This function checks if a given input is not empty.
    :param x: what to check
    :return: True if x is not empty, raises a ValidationError otherwise
    """
    if not x:
        raise ValidationError(x, reason='Cannot be empty')
    else:
        return True


def is_valid_hostname(_, x):
    """
    This function checks if a given input is a valid hostname.
    :param x: what to check
    :return: True if x is a valid hostname, raises a ValidationError otherwise
    """
    if not (validators.domain(x) or validators.ipv4(x) or validators.ipv6(x)):
        raise ValidationError(x, reason='Not a valid hostname, must be a domain or an IP address.')
    else:
        return True


def host_exists(_, x):
    """
    This function checks if a given host already exists in the ssh config file.
    :param x: what to check
    :return: True if x is not empty, raises a ValidationError otherwise
    """
    c = read_ssh_config(CONFIG_FILE_PATH)
    if x in c.hosts():
        raise ValidationError(x, reason='Host already exists, delete it first.')
    else:
        return True
