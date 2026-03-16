# IrisRansomwareLive

> DFIR-IRIS module for automatic case enrichment with [Ransomware.live](https://ransomware.live) threat intelligence.

[![Version](https://img.shields.io/badge/version-3.3.1-blue)](https://github.com/SEU-USUARIO/iris-ransomwarelive)
[![IRIS Interface](https://img.shields.io/badge/IRIS%20interface-1.2.0-orange)](https://docs.dfir-iris.org)
[![Python](https://img.shields.io/badge/python-3.10%2B-green)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)

---

## Overview

**IrisRansomwareLive** enriches DFIR-IRIS cases with real-time ransomware threat intelligence sourced from [Ransomware.live](https://ransomware.live). When triggered — automatically on case creation or manually on demand — the module fetches and registers in the case:

- 📋 **Group profile** — description, TTPs, statistics (victims, first/last seen)
- 🔑 **IOCs** — MD5/SHA256 hashes tagged `ransomware-live`
- 📝 **Ransom notes** — sample ransom note content
- 🛡️ **YARA rules** — detection rules for the ransomware family
- 📊 **Custom attributes** — `ransomware_group` field populated in the Case Summary

---

## Requirements

| Requirement | Version |
|---|---|
| DFIR-IRIS | 2.4.x |
| Python (inside `iriswebapp_worker`) | 3.10+ |
| Ransomware.live API | Public (free) or Pro |

---

## Installation

### 1. Install the pip package inside the IRIS worker container

```bash
docker exec iriswebapp_worker \
  /opt/venv/bin/pip install iris_ransomwarelive
```

### 2. Register the module in IRIS

Navigate to **Advanced → Modules → Add Module** and enter:

```
iris_ransomwarelive
```

Click **Validate module**.

![Add module dialog in IRIS showing iris_ransomwarelive typed in the module name field](docs/images/01-add-module.png)

After validation, **IrisRansomwareLive v3.3.1** will appear in the modules list with a green active indicator:

![Modules management table showing IrisRansomwareLive v3.3.1 as the only active module (green checkmark)](docs/images/02-modules-list.png)

### 3. Configure the module (optional)

Click the module name → **Module Information**. Available settings:

| Parameter | Default | Description |
|---|---|---|
| `API URL` | `https://api.ransomware.live` | Ransomware.live API endpoint |
| `API Key` | *(empty)* | Pro API key for enhanced rate limits |
| `Request Timeout` | `30` | HTTP timeout in seconds |
| `Auto Enrichment` | `True` | Enrich automatically on case creation |

To set a Pro API key, click the **API Key** field:

![Update API Key dialog for IrisRansomwareLive showing a sensitive_string input field](docs/images/03-configure-api-key.png)

> **Note:** The API key is optional. The public API works without authentication, but has lower rate limits.

---

## Usage

### Setting up a case for enrichment

The module reads the `ransomware_group` custom attribute to identify the ransomware family to query. Set it via **Summary → Manage → Ransomware Group**:

![Case #17 manage dialog with the Ransomware Group tab showing "Akira" filled in the ransomware_group field](docs/images/04-case-ransomware-group.png)

### Manual trigger

With the group name set, click **Processors → `iris_ransomwarelive::on_manual_trigger_case`**:

![Case summary page showing the Processors dropdown with iris_ransomwarelive::on_manual_trigger_case option highlighted](docs/images/05-manual-trigger.png)

### Results: IOCs enriched

After enrichment, the case IOC tab is populated with hashes from Ransomware.live, all tagged with `ransomware`, the group name, and `ransomware-live`:

![IOC list showing multiple MD5 hashes from Ransomware.live for Akira, each tagged with ransomware, Akira, and ransomware-live](docs/images/06-iocs-enriched.png)

### Results: Group profile note

A note titled **Ransomware.live: \<GROUP\> Profile** is created under the **Ransomware details** directory, containing the group description, statistics, and MITRE ATT&CK TTPs:

![Notes panel showing Ransomware.live: AKIRA Profile note with group description, victim statistics (1370 victims), first/last seen dates, and MITRE ATT&CK TTPs section](docs/images/07-akira-profile-note.png)

The **Ransomware details** note directory also contains:
- `Ransomware.live: <GROUP> IOCs`
- `Ransomware.live: <GROUP> Ransom Notes`
- `Ransomware.live: <GROUP> YARA Rules`

---

## Automatic enrichment

When `Auto Enrichment` is enabled (default), the module is triggered automatically whenever a new case is created — no manual intervention required. The `ransomware_group` field must be populated at case creation time (e.g. by the `custom-iris.py` Wazuh integration script).

---

## Troubleshooting

**Module doesn't appear after validation:**
```bash
# Restart the worker container
cd /opt/dfir-mesi/iris-web && docker compose restart worker
```

**Enrichment returns no data:**
```bash
# Check worker logs (filter for RansomwareLive output)
docker logs iriswebapp_worker --tail 50 | grep '\[RL\]'
```

**Verify the installed package version:**
```bash
docker exec iriswebapp_worker \
  /opt/venv/bin/pip show iris_ransomwarelive
```

**API rate limit errors:**
- Obtain a Pro API key from [Ransomware.live](https://ransomware.live) and configure it in the module settings (see [Configuration](#3-configure-the-module-optional)).

---

## Post-installation checklist

After completing the steps above, verify:

```
═══════════════════════════════════════════════════════
              Installation Completed!                   
═══════════════════════════════════════════════════════

Next steps:

1. Open IRIS web interface
   https://your-iris-server

2. Navigate to modules
   Advanced → Modules → Add Module → and type: iris_ransomwarelive

3. Configure the module (optional)
   • API URL: https://api-pro.ransomware.live
   • Timeout: 30 seconds

To test the module:

1. Create a new case with ransomware_group custom field
   (Summary → Manage → Ransomware Group)

2. Add an IOC of type 'ransomware-group' with value:
   lockbit

3. Click: Processors → iris_ransomwarelive::on_manual_trigger_case

Troubleshooting:

• Check module logs:
  docker logs iriswebapp_worker --tail 50 | grep '[RL]'

• Verify module status:
  docker exec iriswebapp_worker /opt/venv/bin/pip show iris_ransomwarelive

• If module doesn't appear, restart worker:
  cd /opt/dfir-mesi/iris-web && docker compose restart worker
```

---

## License

MIT — see [LICENSE](LICENSE) for details.