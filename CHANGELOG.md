# Changelog

All notable changes to the DFIR-IRIS Ransomware.live Module.

## [3.3.1] - 2024-11-03

### Added
- Full compatibility with Ubuntu 24.04 LTS
- Support for Python 3.13
- Automatic Python version detection
- Enhanced installation script with better error handling
- Support for `app` and `worker` containers via `-a` flag
- Automatic service restart option via `-r` flag

### Changed
- Updated installation script to version 3.3.2
- Improved dependency installation order
- Used `--no-deps` flag when installing wheel
- Enhanced logging throughout installation

### Fixed
- **CRITICAL**: Fixed hook name from `on_postload_case_update` to `on_postload_case_info_update`
- Fixed installation failure on Ubuntu 24.04 due to missing `python3-venv`
- Fixed dependency resolution order
- Corrected container detection

## [3.2.0] - 2024-10-06

### Added
- ✨ API key support for authenticated access
- ✨ Enhanced Markdown formatting
- ✨ IOCs endpoint integration
- ✨ Automatic IOC addition to case IOC tab
- ✨ IOC type mapping
- ✨ IOC deduplication

### Changed
- Switched from HTML to Markdown formatting
- Improved note organization
- Enhanced logging with `[RL]` prefix

### Fixed
- 🐛 Fixed database model imports
- 🐛 Fixed regex pattern for group extraction
- 🐛 Fixed note directory creation

## [2.5.0] - 2024-09-29

### Added
- 🎉 Initial public release
- Basic ransomware group enrichment
- YARA rule integration
- Ransom note samples
- MITRE ATT&CK TTP mapping

[3.3.1]: https://github.com/yourusername/iris-ransomwarelive-module/compare/v3.2.0...v3.3.1
[3.2.0]: https://github.com/yourusername/iris-ransomwarelive-module/compare/v2.5.0...v3.2.0
[2.5.0]: https://github.com/yourusername/iris-ransomwarelive-module/releases/tag/v2.5.0
