# DFIR-IRIS Ransomware.live Module

![Version](https://img.shields.io/badge/version-3.3.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)
![IRIS](https://img.shields.io/badge/IRIS-v2.4.22%2B-orange.svg)

A powerful DFIR-IRIS module that automatically enriches ransomware incident cases with comprehensive threat intelligence from [Ransomware.live](https://ransomware.live/).

## 🎯 Features

- ✅ **Automatic Enrichment** - Enriches cases automatically when ransomware groups are detected
- 📊 **Comprehensive Intelligence** - Fetches group profiles, statistics, and MITRE ATT&CK TTPs
- 🎯 **IOC Collection** - Automatically adds indicators of compromise to case IOC tab
- 📝 **Ransom Note Samples** - Access historical ransom note examples
- 🛡️ **YARA Rules** - Detection rules for ransomware identification
- 🔑 **API Key Support** - Enhanced access with optional API key authentication
- 🎨 **Rich Markdown Formatting** - Professional, readable reports in case notes
- ⚡ **Smart Execution** - Both manual and automatic enrichment modes
- 🌐 **Dark Web Intelligence** - Monitors ransomware group infrastructure status

## 📋 Requirements

- **DFIR-IRIS** v2.4.22 or higher
- **Python** 3.8+ (tested on 3.9, 3.12, 3.13)
- **Ubuntu** 22.04 or 24.04 (recommended)
- **Docker** and **Docker Compose**
- Internet connectivity for API access

## 📦 Quick Installation

```bash
# 1. Clone repository
cd /opt/iris-web
git clone https://github.com/jfrancci/iris-ransomwarelive-module.git iris-web_ransomwarelive
cd iris-web_ransomwarelive

# 2. Install module
./buildnpush2iris.sh -ar

# 3. Enable in IRIS UI
# Navigate to: Advanced → Modules → Ransomware.live Enrichment → Enable
```

## ⚙️ Configuration

Add this custom attribute in **Advanced → Custom Attributes → Cases**:

```json
{
    "Ransomware Group": {
        "ransomware_group": {
            "type": "input_string",
            "label": "Ransomware group",
            "description": "Ransomware group name (e.g., Akira, LockBit)",
            "mandatory": false,
            "value": ""
        }
    }
}
```

## 🚀 Usage

1. Create a case in IRIS
2. Fill "Ransomware group" field with group name (e.g., `Akira`)
3. Module automatically enriches the case with intelligence
4. Check **Notes** tab for threat intelligence
5. Check **IOC** tab for added indicators

## 📊 Data Collected

- **Group Profile**: Description, statistics, MITRE ATT&CK TTPs, dark web locations
- **IOCs**: IP addresses, domains, hashes, emails, crypto wallets (auto-added to case)
- **Ransom Notes**: Historical samples and patterns
- **YARA Rules**: Detection signatures

## 🦠 Supported Groups

Akira, LockBit, Black Basta, ALPHV/BlackCat, Cl0p, RansomHub, Play, and many more...

See [Ransomware.live](https://ransomware.live/#/group) for complete list.

## 🔍 Troubleshooting

**Module not appearing?**
```bash
docker compose restart app worker
```

**Installation failed?**
```bash
# Ubuntu 24.04: Install required packages first
apt-get install -y python3-venv python3-build python3.12-venv
./buildnpush2iris.sh -ar
```

**Check logs:**
```bash
docker logs iriswebapp_worker -f | grep '\[RL\]'
```

## 📚 Documentation

- [Installation Guide](INSTALL.md)
- [Usage Examples](EXAMPLES.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) file for details.

## 🙏 Credits

- **DFIR-IRIS Team** - Platform
- **Ransomware.live** - Threat intelligence API
- **Community Contributors** - Testing and improvements

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/iris-ransomwarelive-module/issues)
- **IRIS Discord**: [Join Discord](https://discord.gg/iris)

---

**Made by the DFIR Community**

⭐ Star this repository if you find it useful!