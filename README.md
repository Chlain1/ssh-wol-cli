# SSH-CLI

![PyPI](https://img.shields.io/pypi/v/ssh-cli)
![GitHub Actions Workflow Status](https://img.shields.io/github/actions/workflow/status/ValentinKolb/ssh-cli/poetry.yml)

This is a Fork of [ssh-cli](https://github.com/ValentinKolb/ssh-cli) with extended wake-on-lan Features

This CLI tool allows you to create and manage your SSH config file, streamlining the process of handling SSH
connections.

## Installation

To install SSH-Tool, simply run the following command:

```bash
pip install ssh-cli
```

## Usage

After installation, you can start using SSH-Tool by executing:

```bash
ssh-cli
```

## Features

SSH-Tool comes with a variety of features to manage your SSH configurations efficiently:

- **Add a New Host:** Easily add new hosts to your SSH config, with or without specifying a key.
- **Remove a Host:** Remove hosts from your SSH config.
- **List All Hosts:** Get a comprehensive list of all the hosts in your SSH config.
- **Connect to a Host:** Initiate a connection to a specified host directly.
- **Edit a Host:** Update hostname, user, port, Wake-on-LAN MAC addresses, and Wake-on-LAN target IP for an existing host.
- **Manage MAC Addresses:** Add or update Wake-on-LAN MAC addresses and target IP for an existing host directly.
- **Wake-on-LAN Before Connect:** Send directed magic packets (like `wakeonlan -i <target_ip> <mac>`, up to two MAC addresses per host), wait for ping response, then start SSH password login.
- **Edit SSH Config File:** Open and edit your SSH config file with your preferred editor.
- **Cleanup SSH Keys:** Remove unused SSH keys from your directory.

## Configuration

This tool can be configured with Environment Variables:

- `SSH_CLI_CONFIG_FILE`: Path to the SSH config file (created if it does not exist). Default: `~/.ssh/config`
- `SSH_CLI_KEY_DIR`: Path to the directory where keys are stored (created if it does not exist). Default: `~/.ssh/keys`
- `SSH_CLI_METADATA_PATH`: Path to the metadata file for host-specific Wake-on-LAN settings (MAC addresses and target IP). Default: `~/.ssh/ssh-cli-metadata.json`
- `SSH_CLI_KEY_TYPE`: Type of generated SSH keys. Default: `ed25519`
- `SSH_CLI_DEFAULT_USER`: Default user for creating new SSH hosts. Default: `$USER`
- `SSH_CLI_DEFAULT_PORT`: Default port for creating new SSH hosts. Default: `22`
- `SSH_CLI_EDITOR`: Editor used for editing the SSH config file. Default: `$EDITOR` else `nano`

## Contributing

Contributions are what make the open-source community such an amazing place to learn, inspire, and create. Any
contributions you make are greatly appreciated.

1. Fork the Project
1. Create your Feature Branch (git checkout -b feature/AmazingFeature)
1. Commit your Changes (git commit -m 'Add some AmazingFeature')
1. Push to the Branch (git push origin feature/AmazingFeature)
1. Open a Pull Request

## License

Distributed under the MIT License. See LICENSE for more information.
