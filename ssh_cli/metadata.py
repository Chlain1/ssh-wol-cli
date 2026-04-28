import json
from pathlib import Path
from typing import Any

from .config import METADATA_FILE_PATH


def _normalize_host_entry(values: Any) -> dict[str, Any] | None:
    """Normalize old and new metadata formats for a single host."""
    if isinstance(values, list):
        # Backward compatibility: old format was host -> [mac1, mac2]
        mac_addresses = [value for value in values if isinstance(value, str)][:2]
        return {"mac_addresses": mac_addresses, "wol_target_ip": ""}

    if isinstance(values, dict):
        mac_values = values.get("mac_addresses", [])
        if not isinstance(mac_values, list):
            mac_values = []

        mac_addresses = [value for value in mac_values if isinstance(value, str)][:2]
        wol_target_ip = values.get("wol_target_ip", "")

        if not isinstance(wol_target_ip, str):
            wol_target_ip = ""

        return {
            "mac_addresses": mac_addresses,
            "wol_target_ip": wol_target_ip.strip(),
        }

    return None


def _read_metadata() -> dict[str, dict[str, Any]]:
    """Load host metadata from disk."""
    path = Path(METADATA_FILE_PATH)

    if not path.exists():
        return {}

    try:
        with path.open(encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return {}

    if not isinstance(data, dict):
        return {}

    metadata: dict[str, dict[str, Any]] = {}
    for host, values in data.items():
        if not isinstance(host, str):
            continue

        if normalized := _normalize_host_entry(values):
            metadata[host] = normalized

    return metadata


def _write_metadata(metadata: dict[str, dict[str, Any]]) -> None:
    """Persist host metadata to disk."""
    path = Path(METADATA_FILE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, sort_keys=True)
        file.write("\n")


def get_host_macs(host: str) -> list[str]:
    """Return up to two MAC addresses configured for a host."""
    return _read_metadata().get(host, {}).get("mac_addresses", [])[:2]


def get_host_wol_target_ip(host: str) -> str:
    """Return the configured Wake-on-LAN target IP for a host."""
    return _read_metadata().get(host, {}).get("wol_target_ip", "")


def set_host_wol_config(host: str, mac_addresses: list[str], wol_target_ip: str) -> None:
    """Set MAC addresses and WOL target IP for a host."""
    metadata = _read_metadata()

    if mac_addresses or wol_target_ip.strip():
        metadata[host] = {
            "mac_addresses": mac_addresses[:2],
            "wol_target_ip": wol_target_ip.strip(),
        }
    elif host in metadata:
        del metadata[host]

    _write_metadata(metadata)


def set_host_macs(host: str, mac_addresses: list[str]) -> None:
    """Set MAC addresses for a host while preserving WOL target IP."""
    set_host_wol_config(host, mac_addresses, get_host_wol_target_ip(host))


def remove_host_macs(host: str) -> None:
    """Delete MAC address metadata for a host."""
    metadata = _read_metadata()

    if host in metadata:
        del metadata[host]
        _write_metadata(metadata)
