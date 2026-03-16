# Usage Examples

## Basic Example

```bash
# 1. Create case in IRIS
# 2. Fill "Ransomware group": Akira
# 3. Module auto-enriches with:
#    - Group profile
#    - 147 IOCs (IPs, domains, hashes, wallets)
#    - Ransom notes
#    - YARA rules
```

## Manual Enrichment

1. Open case
2. Click **Processors**
3. Select `iris_ransomwarelive::on_manual_trigger_case`
4. Click **Run**

## API Integration Example

```python
import requests

def enrich_case(case_id, group, api_token):
    url = f"https://your-iris.com/api/case/{case_id}/update"
    headers = {"Authorization": f"Bearer {api_token}"}
    
    payload = {
        "custom_attributes": {
            "Ransomware Group": {
                "ransomware_group": {"value": group}
            }
        }
    }
    
    response = requests.post(url, headers=headers, json=payload)
    return response.status_code == 200

# Usage
enrich_case(42, "Akira", "your-token")
```

## Supported Groups

- Akira
- LockBit (aliases: lockbit3, lockbit30)
- Black Basta
- ALPHV / BlackCat
- Cl0p (alias: clop)
- RansomHub
- Play

And many more...

See full examples in repository.
