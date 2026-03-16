# 📘 User Manual - IRIS Ransomware.live Module

**Version:** 3.3.1  
**Date:** March 2026 
**Author:** DFIR Team  

---

## 📑 Table of Contents

1. [Introduction](#introduction)
2. [Prerequisites](#prerequisites)
3. [Step-by-Step Installation](#step-by-step-installation)
4. [Initial Configuration](#initial-configuration)
5. [First Use](#first-use)
6. [Advanced Usage](#advanced-usage)
7. [Troubleshooting](#troubleshooting)
8. [FAQ - Frequently Asked Questions](#faq---frequently-asked-questions)
9. [Glossary](#glossary)

---

## 🎯 Introduction

### What is the IRIS Ransomware.live Module?

The **IRIS Ransomware.live Module** is an extension for the DFIR-IRIS platform that automates ransomware case enrichment with updated threat intelligence.

### What does the module do?

When you investigate a ransomware incident:

1. ✅ **Automatically identifies** the responsible group
2. 📊 **Fetches updated intelligence** from Ransomware.live API
3. 📝 **Creates notes** with detailed group information
4. 🔍 **Adds IOCs** (IPs, domains, hashes) to the case
5. 🛡️ **Provides YARA rules** for detection
6. 📄 **Delivers ransom note samples**

### Why use it?

- ⏱️ **Saves time** - Complete automation
- 📈 **Updated information** - Real-time API
- 🎯 **More accurate** - 147+ IOCs per group
- 🤝 **Integrated with IRIS** - No external tools

---

## 🔧 Prerequisites

### System Requirements

| Item | Requirement | How to Check |
|------|-------------|--------------|
| **DFIR-IRIS** | v2.4.22 or higher | `docker exec iriswebapp_app cat /iriswebapp/version.txt` |
| **Operating System** | Ubuntu 22.04 or 24.04 LTS | `lsb_release -a` |
| **Python** | 3.8+ (on host) | `python3 --version` |
| **Docker** | 20.10+ | `docker --version` |
| **Docker Compose** | 2.0+ | `docker compose version` |
| **Internet** | Access to Ransomware.live API | `curl -I https://api-pro.ransomware.live` |

### Quick Verification

Run this script to check all requirements:

```bash
#!/bin/bash
echo "=== Prerequisites Check ==="
echo ""

# IRIS
if docker ps | grep -q iriswebapp; then
    echo "✅ IRIS is running"
    VERSION=$(docker exec iriswebapp_app cat /iriswebapp/version.txt 2>/dev/null || echo "Not detected")
    echo "   Version: $VERSION"
else
    echo "❌ IRIS is not running"
fi

# Ubuntu
echo ""
echo "Operating System:"
lsb_release -d

# Python
echo ""
PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION"

# Docker
echo ""
DOCKER_VERSION=$(docker --version)
echo "✅ $DOCKER_VERSION"

# Internet
echo ""
if curl -s -o /dev/null -w "%{http_code}" https://api-pro.ransomware.live | grep -q "200\|301\|302"; then
    echo "✅ Access to Ransomware.live API OK"
else
    echo "❌ No access to Ransomware.live API"
fi

echo ""
echo "=== Check Complete ==="
```

---

## 📦 Step-by-Step Installation

### Method 1: Automatic Installation (Recommended)

This is the easiest and fastest method.

#### Step 1: Download Module

```bash
# Navigate to IRIS directory
cd /opt/iris-web

# Clone module repository
git clone https://github.com/jfrancci/iris-ransomwarelive-module.git iris-web_ransomwarelive

# Enter directory
cd iris-web_ransomwarelive
```

**💡 Tip:** If you don't have `git`, install it:
```bash
sudo apt-get update
sudo apt-get install -y git
```

#### Step 2: Run Installation Script

```bash
# Give execution permission
chmod +x buildnpush2iris.sh

# Run complete installation
./buildnpush2iris.sh -ar
```

**What do the flags mean?**
- `-a` = Install in **app** AND **worker** containers (required!)
- `-r` = **Restart** services automatically after installation

**⏱️ Estimated time:** 2-5 minutes

#### Step 3: Verify Installation

```bash
# Check in worker
docker exec iriswebapp_worker /opt/venv/bin/pip show iris_ransomwarelive

# Check in app
docker exec iriswebapp_app /opt/venv/bin/pip show iris_ransomwarelive

# Should show:
# Name: iris_ransomwarelive
# Version: 3.3.1
# ...
```

✅ **If you see the information above, installation was successful!**

---

### Method 2: Manual Installation

Use this method if the automatic script fails.

#### Step 1: Prepare Environment

```bash
# Install system dependencies (Ubuntu 24.04)
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-build python3.12-venv

# Ubuntu 22.04
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-build
```

#### Step 2: Download Module

```bash
cd /opt/iris-web
git clone https://github.com/jfrancci/iris-ransomwarelive-module.git iris-web_ransomwarelive
cd iris-web_ransomwarelive
```

#### Step 3: Build Package

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info

# Build wheel
python3 -m build --wheel --outdir dist

# Verify creation
ls -lh dist/*.whl
```

#### Step 4: Install in Worker

```bash
# Copy to container
docker cp dist/*.whl iriswebapp_worker:/tmp/

# Install
docker exec iriswebapp_worker /opt/venv/bin/pip install /tmp/*.whl

# Clean up
docker exec iriswebapp_worker rm /tmp/*.whl
```

#### Step 5: Install in App

```bash
# Copy to container
docker cp dist/*.whl iriswebapp_app:/tmp/

# Install
docker exec iriswebapp_app /opt/venv/bin/pip install /tmp/*.whl

# Clean up
docker exec iriswebapp_app rm /tmp/*.whl
```

#### Step 6: Restart Services

```bash
cd /opt/iris-web
docker compose restart app worker

# Wait for services to start
sleep 30
```

---

## ⚙️ Initial Configuration

### Step 1: Enable Module in Interface

1. **Login to IRIS**
   - URL: `https://your-iris-server:8443`
   - User: `administrator`
   - Password: your password

2. **Navigate to Modules**
   ```
   Top menu → Advanced → Modules
   ```

3. **Locate the module**
   - Search for: **"Ransomware.live Enrichment"**
   - Status should be: **Not enabled**

4. **Enable the module**
   - Click **"Enable"** button
   - Wait for confirmation
   - Status changes to: **Enabled**

---

### Step 2: Configure Module Parameters

1. **Open configuration**
   - In the module row "Ransomware.live Enrichment"
   - Click the **gear** icon ⚙️
   - Or click **"Configure"**

2. **Configure parameters:**

| Parameter | Recommended Value | Description |
|-----------|-------------------|-------------|
| **API URL** | `https://api-pro.ransomware.live` | API URL (do not change) |
| **API Key** | *(empty initially)* | API key (optional) |
| **Request Timeout** | `30` | Timeout in seconds |
| **Auto Enrichment** | `✓ Enabled` | Automatic enrichment |

3. **Save configuration**
   - Click **"Save"** or **"Update"**

**🔑 About API Key:**
- **Not required** for basic functionality
- **Recommended** for heavy use
- Request at: https://ransomware.live

---

### Step 3: Create Custom Attribute

This is the field the module uses to identify the ransomware group.

1. **Navigate to Custom Attributes**
   ```
   Top menu → Advanced → Custom Attributes
   ```

2. **Select "Cases" tab**
   - Click the **"Cases"** tab

3. **Add the attribute**
   - In the JSON text field, paste:

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

4. **Save**
   - Click **"Save"** or **"Update"**

**⚠️ Important:**
- Field name **MUST** be exactly: `ransomware_group`
- Case sensitive!
- If incorrect, module won't work

---

### Step 4: Verify Complete Installation

Run this checklist:

```bash
# ✅ Module installed in worker
docker exec iriswebapp_worker /opt/venv/bin/pip show iris_ransomwarelive

# ✅ Module installed in app  
docker exec iriswebapp_app /opt/venv/bin/pip show iris_ransomwarelive

# ✅ Module appears in UI
# Access: Advanced → Modules → Look for "Ransomware.live"

# ✅ Module is enabled
# Status should be: "Enabled"

# ✅ Custom attribute created
# Access: Advanced → Custom Attributes → Cases tab

# ✅ No errors in logs
docker logs iriswebapp_worker --tail 50 | grep '\[RL\]'
```

✅ **If all items above are OK, you're ready to use!**

---

## 🚀 First Use

### Scenario: Investigating Akira Ransomware Incident

Let's create a test case to see the module in action.

#### Step 1: Create a New Case

1. **Access IRIS**
   - Login at: `https://your-iris-server:8443`

2. **Create new case**
   ```
   Left menu → Case → "+ New Case" button
   ```

3. **Fill basic data:**
   - **Case Name:** `#001 - Akira Ransomware Test`
   - **Description:** `Automatic enrichment test`
   - **Customer:** `Your customer`
   - **Classification:** `malicious-code:ransomware`
   - **Severity:** `High`
   - **Status:** `Open`

4. **Save case**
   - Click **"Add case"**

---

#### Step 2: Fill Ransomware Group Field

Now let's activate the module by filling the special field.

1. **Open created case**
   - Click on case #001 in list

2. **Go to Summary tab**
   - Should already be selected by default

3. **Edit case**
   - Click **"Edit"** button (upper right)

4. **Scroll to find "Ransomware Group"**
   - It's in Custom Attributes section
   - Field: **"Ransomware group"**

5. **Fill with:** `Akira`
   - Type exactly: `Akira`
   - Or try: `LockBit`, `BlackBasta`, `ALPHV`

6. **Save**
   - Click **"Update"**

**🎉 Magic moment:**
- Module automatically detects filled field
- Starts background enrichment
- In 5-10 seconds, intelligence will be available

---

#### Step 3: View Intelligence - Notes

1. **Click "Notes" tab**
   - Top menu of case: `Notes`

2. **Expand "Ransomware details" directory**
   - Click 📁 "Ransomware details" folder

3. **See the 4 created notes:**

   **📄 Ransomware.live: AKIRA Profile**
   - Group description
   - Victim statistics
   - First/last activity dates
   - MITRE ATT&CK TTPs
   - Dark web sites (online/offline status)

   **🔍 Ransomware.live: AKIRA IOCs**
   - List of indicators of compromise
   - IPs, domains, hashes, emails, crypto wallets

   **📝 Ransomware.live: AKIRA Ransom Notes**
   - Ransom note samples
   - Common patterns
   - Contact methods

   **🛡️ Ransomware.live: AKIRA YARA Rules**
   - YARA detection rules
   - Ransomware signatures

---

#### Step 4: View Added IOCs

1. **Click "IOC" tab**
   - Top menu of case: `IOC`

2. **See automatically added IOCs:**
   - **147+ indicators** added!
   - Types: `ip-dst`, `domain`, `sha256`, `btc`, `email`, etc.
   - Tags: `ransomware`, `akira`, `ransomware-live`

3. **Explore IOCs:**
   - Click any IOC to see details
   - Use filters to search specific types
   - Export to use in firewalls, SIEM, etc.

**💡 Tip:** You can use these IOCs immediately to:
- Block IPs/domains in firewall
- Create SIEM alerts
- Perform threat hunting on network
- Share with ISACs/CERTs

---

#### Step 5: Check Logs (Optional)

To see what happened behind the scenes:

```bash
# View module logs
docker logs iriswebapp_worker --tail 100 | grep '\[RL\]'

# You'll see something like:
# [RL] Enriching case 1 (automatic) with group: Akira
# [RL] Normalized group name: Akira
# [RL] Fetching group profile: https://api-pro.ransomware.live/groups/Akira
# [RL] ✓ Group profile note created successfully
# [RL] ✓✓✓ Successfully added 147 IOCs to case
# [RL] Enrichment complete: 4/4 successful
```

**✅ Congratulations! You completed your first automatic enrichment!**

---

## 🎓 Advanced Usage

### Manual Enrichment

Sometimes you want to re-enrich a case (e.g., new intelligence available).

#### How to:

1. **Open case**
   - Navigate to desired case

2. **Click "Processors"**
   - Button located in case top bar
   - Next to "Manage", "Pipelines"

3. **Select module**
   - Look for: `iris_ransomwarelive::on_manual_trigger_case`
   - Click to select

4. **Execute**
   - Click **"Run"** button
   - Wait for processing (5-10 seconds)

5. **See result**
   - Success/error message will appear
   - New information will be added

**💡 When to use manual enrichment?**
- Update old intelligence
- Force re-enrichment after error
- Test module
- When auto-enrich is disabled

---

### Using API Key for Premium Access

If you have an API key from Ransomware.live:

#### Step 1: Get API Key

1. Visit: https://ransomware.live
2. Contact administrators
3. Request an API key

#### Step 2: Configure in IRIS

1. **Navigate to modules**
   ```
   Advanced → Modules → Ransomware.live Enrichment
   ```

2. **Click Configure** ⚙️

3. **Fill API Key**
   - Field: **API Key**
   - Paste your key: `rl_1234567890abcdef...`

4. **Save**

#### Step 3: Verify

```bash
# Logs should show:
docker logs iriswebapp_worker --tail 50 | grep '\[RL\]'

# Look for:
# [RL] API-KEY configured for requests
```

**🎁 API Key Benefits:**
- ⚡ Higher rate limits
- 🚀 Request priority
- 📊 Access to premium endpoints (future)
- 🎯 More complete data

---

### Working with Multiple Cases

#### Scenario: Ransomware Campaign

Imagine you have 5 cases from the same campaign:

1. **Create 5 cases**
   - #001, #002, #003, #004, #005

2. **In each case, fill:**
   - "Ransomware group" field: `LockBit`

3. **Result:**
   - All 5 cases automatically enriched
   - Same intelligence in all
   - Easy correlation between cases

**💡 Workflow Tip:**
```
1. Create case → 2. Fill group → 3. Automatic enrichment →
4. Analyze notes → 5. Use IOCs → 6. Containment
```

---

### Supported Ransomware Groups

Module supports 100+ groups. Here are the main ones:

| Group | Accepted Aliases | Example Usage |
|-------|-----------------|---------------|
| Akira | akira | `Akira` |
| LockBit | lockbit, lockbit3, lockbit30 | `LockBit` |
| Black Basta | blackbasta, black_basta | `BlackBasta` |
| ALPHV | alphv, blackcat | `ALPHV` |
| Cl0p | clop, cl0p | `Clop` |
| RansomHub | ransomhub | `RansomHub` |
| Play | play | `Play` |
| 8Base | 8base | `8Base` |
| Medusa | medusa | `Medusa` |
| NoEscape | noescape | `NoEscape` |

**Complete list:** https://ransomware.live/#/group

**💡 Automatic Normalization:**
- `lockbit3` → `Lockbit`
- `Cl0p` → `Clop`
- `ALPHV` → `Alphv`

---

## 🔧 Troubleshooting

### Problem 1: Module Doesn't Appear in List

**Symptoms:**
- Don't see "Ransomware.live" in Advanced → Modules

**Solutions:**

```bash
# 1. Check if installed
docker exec iriswebapp_app /opt/venv/bin/pip show iris_ransomwarelive

# If nothing appears:
# 2. Reinstall in app
./buildnpush2iris.sh -a

# 3. Restart services
cd /opt/iris-web
docker compose restart app worker

# 4. Wait 30 seconds
sleep 30

# 5. Check logs
docker logs iriswebapp_app --tail 50 | grep -i module
```

---

### Problem 2: Enrichment Doesn't Work

**Symptoms:**
- Fill field but nothing happens
- No notes created
- No IOCs added

**Diagnosis:**

```bash
# 1. Check worker logs
docker logs iriswebapp_worker --tail 100 | grep '\[RL\]'

# Look for errors like:
# [RL] Error fetching group profile: 404
# [RL] No ransomware_group found
# [RL] Failed to create note
```

**Solutions by error:**

**Error: "No ransomware_group found"**
- ✅ Check if you filled field correctly
- ✅ Field name must be exactly: `ransomware_group`
- ✅ Check custom attribute JSON

**Error: "404" or "Group not found"**
- ✅ Group doesn't exist in Ransomware.live database
- ✅ Try another name or alias
- ✅ Check: https://ransomware.live/#/group

**Error: "Connection timeout"**
- ✅ Check internet connection: `curl https://api-pro.ransomware.live`
- ✅ Check firewall/proxy

**Error: "Failed to create note"**
- ✅ Database permission issue
- ✅ Restart containers: `docker compose restart app worker db`

---

### Problem 3: IOCs Not Being Added

**Symptoms:**
- Notes created OK
- But IOC tab is empty

**Solution:**

```bash
# 1. Check IOC-specific logs
docker logs iriswebapp_worker --tail 200 | grep -A 20 "ADDING IOCs"

# 2. Check if API returned IOCs
# Manual test:
curl "https://api-pro.ransomware.live/iocs/akira"

# 3. Check database
docker exec iriswebapp_db psql -U postgres -d iris_db -c \
  "SELECT COUNT(*) FROM ioc WHERE ioc_description LIKE '%Ransomware.live%';"

# If returns 0, there's an insertion problem

# 4. Check permissions
docker exec iriswebapp_db psql -U postgres -d iris_db -c \
  "SELECT * FROM ioc_type LIMIT 5;"
```

---

## ❓ FAQ - Frequently Asked Questions

### About Functionality

**Q: Does the module work offline?**  
A: No. Module needs connection to Ransomware.live API.

**Q: How long does enrichment take?**  
A: Typically 5-10 seconds per case.

**Q: Can I enrich old cases?**  
A: Yes! Use manual enrichment ("Processors" button).

**Q: How many IOCs are added on average?**  
A: Between 100-200 IOCs per group, depending on API availability.

**Q: Are IOCs automatically updated?**  
A: No. To update, use manual enrichment again.

---

### About Installation

**Q: Does it work on Windows?**  
A: Not directly. IRIS runs on Linux (Ubuntu recommended). You can use WSL2.

**Q: Do I need an API Key?**  
A: Not mandatory, but recommended for heavy use.

**Q: Does it work with production IRIS?**  
A: Yes! Tested in production with IRIS v2.4.22.

**Q: Can I install on an IRIS already in use?**  
A: Yes, it's safe. Doesn't affect existing cases or data.

---

### About Ransomware Groups

**Q: How do I know if a group is supported?**  
A: Check: https://ransomware.live/#/group

**Q: What if my group isn't in the list?**  
A: 
1. Check aliases (e.g., Cl0p → Clop)
2. Wait - new groups are added frequently
3. Request addition at: https://ransomware.live

**Q: Can I add custom groups?**  
A: Not directly. Module uses Ransomware.live API.

---

### About Data and Privacy

**Q: Is my case data sent to Ransomware.live?**  
A: No! Only the group NAME is used in API request. No sensitive data sent.

**Q: Can I use without internet?**  
A: No. API must be accessible.

**Q: Are IOCs reliable?**  
A: Yes, but always do complementary analysis. Don't trust 100% in single source.

---

## 📚 Glossary

| Term | Meaning |
|------|---------|
| **IRIS** | Incident Response Investigation System - DFIR platform |
| **DFIR** | Digital Forensics & Incident Response |
| **IOC** | Indicator of Compromise |
| **TTP** | Tactics, Techniques, and Procedures (MITRE ATT&CK) |
| **YARA** | Malware detection tool based on rules |
| **Hook** | Extension point in IRIS for modules |
| **Enrichment** | Adding intelligence to case |
| **Custom Attribute** | Custom field in IRIS |
| **Worker** | Container that processes background tasks |
| **App** | Container for IRIS web interface |
| **API Key** | Authentication key for API |

---

## 📞 Support

### Need Help?

**🐛 Bugs and Issues:**
- GitHub Issues: https://github.com/jfrancci/iris-ransomwarelive-module/issues

**💬 General Questions:**
- IRIS Discord: https://discord.gg/iris
- GitHub Discussions: https://github.com/jfrancci/iris-ransomwarelive-module/discussions

**📖 Documentation:**
- README: https://github.com/jfrancci/iris-ransomwarelive-module
- IRIS Docs: https://docs.dfir-iris.org/

---

## 📝 Complete Installation Checklist

Use this list to ensure everything is configured:

- [ ] IRIS v2.4.22+ installed and working
- [ ] Ubuntu 22.04 or 24.04
- [ ] Python 3.8+ on host
- [ ] Docker and Docker Compose working
- [ ] Internet access (Ransomware.live API)
- [ ] Module cloned from GitHub
- [ ] `buildnpush2iris.sh` script executed with `-ar`
- [ ] Module installed in worker (verified)
- [ ] Module installed in app (verified)
- [ ] Module enabled in IRIS UI
- [ ] Custom attribute "ransomware_group" created
- [ ] Test case created
- [ ] "Ransomware group" field filled
- [ ] Enrichment worked (notes created)
- [ ] IOCs added to IOC tab
- [ ] Logs without errors

**✅ If all items above are checked, congratulations! You're ready to use the module in production!**

---

## 🎉 Conclusion

You completed the user manual! Now you know:

- ✅ How to install the module
- ✅ How to configure correctly
- ✅ How to use in real cases
- ✅ How to solve common problems
- ✅ How to integrate with other tools

**Next Steps:**
1. Test with real ransomware cases
2. Integrate IOCs with your security tools
3. Share intelligence with your team
4. Contribute improvements on GitHub

**Remember:** This module is a tool. Human knowledge and analysis remain essential!

---

**Manual Version:** 3.3.1  
**Last Updated:** January 2025  
**License:** Apache 2.0  

**Made by the DFIR Community**
