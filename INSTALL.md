# Quick Installation Guide

## ⚡ Quick Start (3 steps)

```bash
# 1. Clone
cd /opt/iris-web
git clone https://github.com/jfrancci/iris-ransomwarelive-module.git iris-web_ransomwarelive
cd iris-web_ransomwarelive

# 2. Install
./buildnpush2iris.sh -ar

# 3. Enable
# Navigate to: Advanced → Modules → Ransomware.live → Enable
```

## Configuration

Add custom attribute in IRIS:

```json
{
    "Ransomware Group": {
        "ransomware_group": {
            "type": "input_string",
            "label": "Ransomware group",
            "description": "Group name (e.g., Akira, LockBit)",
            "mandatory": false,
            "value": ""
        }
    }
}
```

## Test

1. Create case
2. Fill "Ransomware group": `Akira`
3. Check Notes and IOC tabs

✅ Done!
