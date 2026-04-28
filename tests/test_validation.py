# basic test from the module with pytest

import pytest

from ssh_cli.validation import (
    is_number,
    is_not_empty,
    is_valid_hostname,
    normalize_mac_address,
    parse_mac_addresses,
    parse_wol_target_ip,
)


def test_is_number():
    assert is_number(None, "1") == True
    with pytest.raises(Exception):
        is_number(None, "a")


def test_is_not_empty():
    assert is_not_empty(None, "a") == True
    with pytest.raises(Exception):
        is_not_empty(None, "")


def test_is_valid_hostname():
    assert is_valid_hostname(None, "example.com") == True
    with pytest.raises(Exception):
        is_valid_hostname(None, "example")


def test_normalize_mac_address():
    assert normalize_mac_address("AA-BB-CC-DD-EE-FF") == "aa:bb:cc:dd:ee:ff"

    with pytest.raises(ValueError):
        normalize_mac_address("invalid")


def test_parse_mac_addresses():
    assert parse_mac_addresses("") == []
    assert parse_mac_addresses("AA-BB-CC-DD-EE-FF") == ["aa:bb:cc:dd:ee:ff"]
    assert parse_mac_addresses("AA:BB:CC:DD:EE:FF, 11:22:33:44:55:66") == [
        "aa:bb:cc:dd:ee:ff",
        "11:22:33:44:55:66",
    ]

    with pytest.raises(ValueError):
        parse_mac_addresses("AA:BB:CC:DD:EE:FF,11:22:33:44:55:66,77:88:99:AA:BB:CC")

    with pytest.raises(ValueError):
        parse_mac_addresses("AA:BB:CC:DD:EE:FF,AA-BB-CC-DD-EE-FF")


def test_parse_wol_target_ip():
    assert parse_wol_target_ip("") == ""
    assert parse_wol_target_ip("192.168.1.255") == "192.168.1.255"

    with pytest.raises(ValueError):
        parse_wol_target_ip("example.com")
