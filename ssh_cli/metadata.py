import json
from pathlib import Path

from .config import METADATA_FILE_PATH


def _read_metadata() -> dict[str, list[str]]:
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

    metadata: dict[str, list[str]] = {}
    for host, values in data.items():
        if not isinstance(host, str) or not isinstance(values, list):
            continue
        mac_addresses = [value for value in values if isinstance(value, str)]
        metadata[host] = mac_addresses[:2]

    return metadata


def _write_metadata(metadata: dict[str, list[str]]) -> None:
    """Persist host metadata to disk."""
    path = Path(METADATA_FILE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, indent=2, sort_keys=True)
        file.write("\n")


def get_host_macs(host: str) -> list[str]:
    """Return up to two MAC addresses configured for a host."""
    return _read_metadata().get(host, [])[:2]


def set_host_macs(host: str, mac_addresses: list[str]) -> None:
    """Set MAC addresses for a host."""
    metadata = _read_metadata()

    if mac_addresses:
        metadata[host] = mac_addresses[:2]
    elif host in metadata:
        del metadata[host]

    _write_metadata(metadata)


def remove_host_macs(host: str) -> None:
    """Delete MAC address metadata for a host."""
    metadata = _read_metadata()

    if host in metadata:
        del metadata[host]
        _write_metadata(metadata)
