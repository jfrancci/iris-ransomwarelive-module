# DFIR-IRIS Ransomware.live Module (Beta Version)

![Version](https://img.shields.io/badge/version-3.3.1-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)
![IRIS](https://img.shields.io/badge/IRIS-v2.4.22%2B-orange.svg)

[![EN](https://img.shields.io/badge/lang-EN-blue.svg)](README.md)
[![PT-BR](https://img.shields.io/badge/lang-PT--BR-green.svg)](docs/pt-BR/README.pt-BR.md)

A powerful DFIR-IRIS module that automatically enriches ransomware incident cases with comprehensive threat intelligence from [Ransomware.live](https://ransomware.live/).

## 🌐 Documentation Languages

- 🇺🇸 **English** (you are here)
- 🇧🇷 **[Português Brasileiro](docs/pt-BR/README.pt-BR.md)**

## 🎯 Features

- ✅ **Automatic Enrichment** - Enriches cases automatically when ransomware groups are detected
- 📊 **Comprehensive Intelligence** - Fetches group profiles, statistics, and MITRE ATT&CK TTPs
- 🎯 **IOC Collection** - Automatically adds 147+ indicators of compromise to case IOC tab
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
# 1. Clone repository in DFIR-IRIS install folder
cd /opt/iris-web
git clone https://github.com/jfrancci/iris-ransomwarelive-module.git iris-web_ransomwarelive
cd iris-web_ransomwarelive

# 2. Install module
chmod +x buildnpush2iris.sh 
./buildnpush2iris.sh -ar

or 

./buildnpush2iris.sh -ar -i /opt/dfir-mesi/iris-web

# 3. Enable in IRIS UI
# Navigate to: Advanced → Modules → Add Module → iris_ransomwarelive
```

## ⚙️ Configuration

Add this custom attribute in **Advanced → Custom Attributes → Cases**:

```json
{
    "Ransomware Group": {
        "ransomware_group": {
            "type": "input_string",
            "label": "Ransomware group",
            "description": "Ransomware group name (e.g., Akira, LockBit, BlackBasta)",
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
5. Check **IOC** tab for 147+ added indicators

## 📊 Data Collected

- **Group Profile**: Description, statistics, MITRE ATT&CK TTPs, dark web locations
- **IOCs**: IP addresses, domains, hashes, emails, crypto wallets (auto-added to case)
- **Ransom Notes**: Historical samples and patterns
- **YARA Rules**: Detection signatures

## 🦠 Supported Groups

Akira, LockBit, Black Basta, ALPHV/BlackCat, Cl0p, RansomHub, Play, and 100+ more...

See [Ransomware.live Groups](https://ransomware.live/#/group) for complete list.

## 📚 Complete Documentation

- 📘 **[User Manual](USER_MANUAL.md)** - Complete installation and usage guide
- 📊 **[Flowcharts](FLOWCHARTS.md)** - 10 visual diagrams of module operation
- 🚀 **[Installation Guide](INSTALL.md)** - Quick start guide
- 💡 **[Usage Examples](EXAMPLES.md)** - Practical examples and code samples
- 🤝 **[Contributing](CONTRIBUTING.md)** - Contribution guidelines
- 📝 **[Changelog](CHANGELOG.md)** - Version history

### Portuguese Documentation

- 📘 **[Manual do Usuário](docs/pt-BR/USER_MANUAL.pt-BR.md)** - Guia completo em português
- 📊 **[Fluxogramas](docs/pt-BR/FLOWCHARTS.pt-BR.md)** - Diagramas visuais
- 🚀 **[Guia de Instalação](docs/pt-BR/INSTALL.pt-BR.md)** - Instalação rápida
- 💡 **[Exemplos](docs/pt-BR/EXAMPLES.pt-BR.md)** - Exemplos práticos

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

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

Apache License 2.0 - See [LICENSE](LICENSE) file for details.

## 🙏 Credits

- **DFIR-IRIS Team** - For the amazing incident response platform
- **Ransomware.live** - For providing the threat intelligence API
- **Community Contributors** - For testing, feedback, and improvements

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jfrancci/iris-ransomwarelive-module/issues)
- **IRIS Discord**: [Join Discord](https://discord.gg/iris)
- **Documentation**: [IRIS Docs](https://docs.dfir-iris.org/)

---

**Made with ❤️ by the DFIR Community**

⭐ **Star this repository if you find it useful!**

[![GitHub stars](https://img.shields.io/github/stars/jfrancci/iris-ransomwarelive-module?style=social)](https://github.com/jfrancci/iris-ransomwarelive-module)
