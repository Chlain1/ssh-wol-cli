from types import SimpleNamespace

from ssh_cli.cmds.connect import Connect


class _HostConfig:
    def __init__(self, data):
        self._data = data

    def get(self, key):
        return self._data.get(key)


class _Config:
    def __init__(self, host_config):
        self._host_config = host_config

    def host(self, host):
        return self._host_config


def test_connect_uses_direct_ssh_after_wol(monkeypatch):
    from ssh_cli.cmds import connect as connect_module

    calls = []

    monkeypatch.setattr(connect_module, "select_host", lambda: "test-host")
    monkeypatch.setattr(connect_module, "read_ssh_config", lambda path: _Config(_HostConfig({"hostname": "134.60.18.17", "user": "default-user"})))
    monkeypatch.setattr(connect_module, "get_host_macs", lambda host: ["aa:bb:cc:dd:ee:ff"])
    monkeypatch.setattr(connect_module, "get_host_wol_target_ip", lambda host: "192.168.1.255")
    monkeypatch.setattr(connect_module, "_send_wol_packets", lambda ip, macs: True)
    monkeypatch.setattr(connect_module, "_wait_until_pingable", lambda hostname: True)
    monkeypatch.setattr(connect_module.inquirer, "prompt", lambda questions: {"username": "chl"})

    def fake_run(args):
        calls.append(args)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(connect_module.subprocess, "run", fake_run)

    code = Connect().run()

    assert code == 0
    assert calls == [["ssh", "-o", "PreferredAuthentications=password", "-o", "PubkeyAuthentication=no", "-l", "chl", "test-host"]]
