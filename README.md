<p align="center">
  <img src="https://raw.githubusercontent.com/emrekybs/hawkopsec/main/hawkopsec/assets/hawkopsec_mark.png" alt="HawkOpsec" width="380">
</p>

<h1 align="center">HawkOpsec</h1>

<p align="center"><b>One-tap Linux OPSEC hardening & anonymity toolkit</b></p>

<p align="center">
  <img alt="pypi" src="https://img.shields.io/pypi/v/hawkopsec?color=0b0d10">
  <img alt="platform" src="https://img.shields.io/badge/platform-Linux-0b0d10">
  <img alt="license" src="https://img.shields.io/badge/license-MIT-blue">
</p>

Pick a profile and HawkOpsec starts Tor, encrypts DNS, spoofs your identity, hardens the kernel
and checks for DNS / IP leaks — **Reset system** rolls everything back.

<p align="center"><img src="https://raw.githubusercontent.com/emrekybs/hawkopsec/main/docs/dashboard.png" alt="HawkOpsec" width="850"></p>

## Architecture

<p align="center"><img src="https://raw.githubusercontent.com/emrekybs/hawkopsec/main/docs/arch.png" alt="Architecture" width="850"></p>

## Install

System packages:

```bash
# Debian / Ubuntu / Kali / Mint
sudo apt install -y pipx tor nftables policykit-1 iproute2 rfkill
# Arch
sudo pacman -S --needed python-pipx tor nftables polkit iproute2 rfkill
```

**With pipx**

```bash
pipx install hawkopsec
sudo "$(command -v hawkopsec-setup)"
hawkopsec
```

**Without pipx**

```bash
python3 -m venv ~/.hawkopsec
~/.hawkopsec/bin/pip install hawkopsec
sudo ~/.hawkopsec/bin/hawkopsec-setup
~/.hawkopsec/bin/hawkopsec
```

`hawkopsec-setup` runs once: it installs the root helper, polkit policy and menu entry.
After that, start HawkOpsec from the application menu.

## License

MIT — see [LICENSE](LICENSE).
