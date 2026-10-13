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

**With pipx**

```bash
# Debian / Ubuntu / Kali / Mint
sudo apt install -y pipx tor nftables policykit-1 iproute2 rfkill
# Arch
sudo pacman -S --needed python-pipx tor nftables polkit iproute2 rfkill

pipx install hawkopsec
sudo "$(command -v hawkopsec-setup)"
hawkopsec
```

**From Source

```bash
# Debian / Ubuntu / Kali / Mint
sudo apt install -y git python3-pyqt6 tor nftables policykit-1 iproute2 rfkill && git clone https://github.com/emrekybs/hawkopsec.git && cd hawkopsec && sudo ./packaging/install.sh && hawkopsec
# Arch
sudo pacman -S --needed git python-pyqt6 tor nftables polkit iproute2 rfkill && git clone https://github.com/emrekybs/hawkopsec.git && cd hawkopsec && sudo ./packaging/install.sh && hawkopsec
```

After installing, start HawkOpsec from the application menu or run `hawkopsec`.

## License

MIT — see [LICENSE](LICENSE).
