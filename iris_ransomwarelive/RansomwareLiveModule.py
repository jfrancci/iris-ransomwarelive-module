# -*- coding: utf-8 -*-
"""
DFIR-IRIS Ransomware.live Module
Version: 3.3.1
Author: JFN
"""

import json
import os
import re
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

try:
    from iris_interface.IrisModuleInterface import IrisModuleInterface, IrisModuleTypes
    import iris_interface.IrisInterfaceStatus as InterfaceStatus
except ImportError:
    # Fallback para testes
    class IrisModuleInterface:
        def __init__(self):
            self.log = type('obj', (object,), {
                'info': lambda x: print(f"INFO: {x}"),
                'error': lambda x: print(f"ERROR: {x}"),
                'warning': lambda x: print(f"WARNING: {x}")
            })()
            self.module_dict_conf = {}
        
        def register_to_hook(self, *args, **kwargs):
            return True
    
    class InterfaceStatus:
        @staticmethod
        def I2Success(**kwargs):
            return {"status": "success", **kwargs}
        
        @staticmethod
        def I2Error(msg, **kwargs):
            return {"status": "error", "message": msg, **kwargs}
    
    class IrisModuleTypes:
        module_processor = "processor"


class RansomwareLiveModule(IrisModuleInterface):
    """
    Ransomware.live enrichment module for DFIR-IRIS.
    Provides threat intelligence enrichment for ransomware incidents.
    """
    
    _module_name = "IrisRansomwareLive"
    _module_human_name = "Ransomware.live Enrichment"
    _module_description = "Enrich cases with Ransomware.live threat intelligence"
    _interface_version = "1.2.0"
    _module_version = "3.3.1"
    _module_type = IrisModuleTypes.module_processor
    _pipeline_support = False
    _pipeline_info = {}
    
    _module_configuration = [
        {
            "param_name": "api_url",
            "param_human_name": "API URL",
            "param_description": "Ransomware.live API base URL",
            "default": "https://api-pro.ransomware.live",
            "mandatory": True,
            "type": "string"
        },
        {
            "param_name": "api_key",
            "param_human_name": "API Key",
            "param_description": "Your Ransomware.live API key for enhanced access",
            "default": "",
            "mandatory": False,
            "type": "sensitive_string"
        },
        {
            "param_name": "timeout_s",
            "param_human_name": "Request Timeout",
            "param_description": "API request timeout in seconds",
            "default": 30,
            "mandatory": True,
            "type": "int"
        },
        {
            "param_name": "auto_enrich",
            "param_human_name": "Auto Enrichment",
            "param_description": "Automatically enrich cases when ransomware IOCs are detected",
            "default": True,
            "mandatory": True,
            "type": "bool"
        }
    ]
    
    def __init__(self):
        super().__init__()
        self._session = None
        self._api_key = None
        self.log.info(f"[RL] Initializing module v{self._module_version}")
    
    def register_hooks(self, module_id: int):
        """Register module hooks for both manual and automatic execution."""
        try:
            self.register_to_hook(module_id, iris_hook_name="on_manual_trigger_case")
            self.register_to_hook(module_id, iris_hook_name="on_manual_trigger_ioc")
            self.register_to_hook(module_id, iris_hook_name="on_postload_case_create")
            self.register_to_hook(module_id, iris_hook_name="on_postload_case_info_update")
            
            self.log.info("[RL] Hooks registered successfully (manual + automatic)")
            return InterfaceStatus.I2Success()
        except Exception as e:
            self.log.error(f"[RL] Failed to register hooks: {e}")
            return InterfaceStatus.I2Error(str(e))

    def hooks_handler(self, hook_name: str, hook_ui_name: str, data):
        """Handle incoming hooks for both manual and automatic execution."""
        self.log.info(f"[RL] Processing hook: {hook_name}")
        
        try:
            config = self._load_config()
            
            if hook_name in ["on_manual_trigger_case", "on_postload_case_create", "on_postload_case_info_update"]:
                return self._handle_case_trigger(data, config, is_automatic=(hook_name != "on_manual_trigger_case"))
            
            elif hook_name == "on_manual_trigger_ioc":
                return self._handle_ioc_trigger(data, config)
            
            else:
                return InterfaceStatus.I2Success(data=data)
        
        except Exception as e:
            self.log.error(f"[RL] Hook handler error: {e}")
            self.log.error(f"[RL] Traceback: {traceback.format_exc()}")
            return InterfaceStatus.I2Error(str(e), data=data)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load and validate module configuration."""
        config = {
            'api_url': 'https://api-pro.ransomware.live',
            'api_key': '',
            'timeout': 30,
            'auto_enrich': True
        }
        
        if hasattr(self, 'module_dict_conf') and isinstance(self.module_dict_conf, dict):
            config['api_url'] = self.module_dict_conf.get('api_url', config['api_url'])
            config['api_key'] = self.module_dict_conf.get('api_key', config['api_key'])
            config['timeout'] = int(self.module_dict_conf.get('timeout_s', config['timeout']))
            config['auto_enrich'] = self.module_dict_conf.get('auto_enrich', config['auto_enrich'])
        
        self._api_key = config['api_key']
        return config
    
    def _handle_case_trigger(self, data, config, is_automatic=False):
        """Handle case trigger (both manual and automatic)."""
        if isinstance(data, list) and data:
            data = data[0]
        
        case = data.get('case', data) if isinstance(data, dict) else data
        case_id = self._get_case_id(case)
        
        if not case_id:
            return InterfaceStatus.I2Error("No case ID found")
        
        group = self._extract_ransomware_group(case)
        
        if not group:
            if is_automatic:
                self.log.info(f"[RL] Case {case_id} has no ransomware_group - skipping automatic enrichment")
                return InterfaceStatus.I2Success(data=data)
            else:
                return InterfaceStatus.I2Error(
                    "No ransomware group detected. Please fill the 'ransomware_group' field in the case."
                )
        
        execution_type = "automatic" if is_automatic else "manual"
        self.log.info(f"[RL] Enriching case {case_id} ({execution_type}) with group: {group}")
        
        success = self._enrich_case(case_id, group, config)
        
        if success:
            message = f"Successfully enriched case with {group} intelligence"
            if is_automatic:
                message += " (automatic execution)"
            return InterfaceStatus.I2Success(data=data, logs=message)
        else:
            return InterfaceStatus.I2Success(data=data, logs="Enrichment completed with some errors. Check logs for details.")
    
    def _handle_ioc_trigger(self, data, config):
        """Handle IOC-based trigger."""
        if isinstance(data, list) and data:
            data = data[0]
        
        ioc = data.get('ioc', data) if isinstance(data, dict) else data
        case_id = self._get_case_id(ioc)
        
        if not case_id:
            return InterfaceStatus.I2Error("No case ID found in IOC")
        
        group = self._extract_group_from_ioc(ioc)
        if not group:
            return InterfaceStatus.I2Error("IOC is not a ransomware group indicator")
        
        self.log.info(f"[RL] Enriching case {case_id} from IOC with group: {group}")
        
        success = self._enrich_case(case_id, group, config)
        
        if success:
            return InterfaceStatus.I2Success(data=data)
        else:
            return InterfaceStatus.I2Success(data=data, logs="Enrichment completed with warnings")
    
    def _get_case_id(self, obj):
        """Extract case ID from object."""
        if isinstance(obj, dict):
            return obj.get('case_id') or obj.get('id') or obj.get('ioc_case_id')
        else:
            return (getattr(obj, 'case_id', None) or 
                   getattr(obj, 'id', None) or 
                   getattr(obj, 'ioc_case_id', None))
    
    def _extract_ransomware_group(self, case) -> Optional[str]:
        """Extract ransomware group from custom_attributes JSON field."""
        case_id = self._get_case_id(case)
        if not case_id:
            self.log.error("[RL] Cannot extract group: no case_id found")
            return None
        
        self.log.info(f"[RL] Looking for ransomware_group in case {case_id}")
        
        try:
            from app import db
            from sqlalchemy import text
            
            query = text("""
                SELECT custom_attributes 
                FROM cases 
                WHERE case_id = :case_id
            """)
            
            result = db.session.execute(query, {"case_id": case_id}).fetchone()
            
            if not result or not result[0]:
                self.log.warning(f"[RL] No custom_attributes found for case {case_id}")
                return None
            
            custom_attrs = result[0]
            self.log.info(f"[RL] custom_attributes type: {type(custom_attrs)}")
            
            if isinstance(custom_attrs, str):
                try:
                    custom_attrs = json.loads(custom_attrs)
                except Exception as e:
                    self.log.error(f"[RL] Failed to parse JSON: {e}")
                    return None
            
            if not isinstance(custom_attrs, dict):
                self.log.error(f"[RL] custom_attributes is not a dict: {type(custom_attrs)}")
                return None
            
            self.log.info(f"[RL] custom_attributes keys: {list(custom_attrs.keys())}")
            
            for group_name, group_data in custom_attrs.items():
                self.log.info(f"[RL] Checking group: '{group_name}'")
                
                if isinstance(group_data, dict) and 'ransomware_group' in group_data:
                    field_data = group_data['ransomware_group']
                    self.log.info(f"[RL] Found field data: {field_data}")
                    
                    if isinstance(field_data, dict) and 'value' in field_data:
                        group = str(field_data['value']).strip()
                        if group:
                            self.log.info(f"[RL] ✓✓✓ Ransomware group found: {group}")
                            return group
                        else:
                            self.log.info("[RL] Field 'ransomware_group' has empty value - skipping")
                            return None
            
            self.log.warning("[RL] Field 'ransomware_group' not found in custom_attributes")
            return None
            
        except Exception as e:
            self.log.error(f"[RL] Error reading custom_attributes: {e}")
            self.log.error(f"[RL] Traceback: {traceback.format_exc()}")
            return None

    def _extract_group_from_ioc(self, ioc) -> Optional[str]:
        """Extract ransomware group name from IOC."""
        if isinstance(ioc, dict):
            ioc_type = str(ioc.get('ioc_type_name', '')).lower()
            value = ioc.get('ioc_value', '')
        else:
            ioc_type_obj = getattr(ioc, 'ioc_type', None)
            ioc_type = str(getattr(ioc_type_obj, 'type_name', '')).lower() if ioc_type_obj else ''
            value = getattr(ioc, 'ioc_value', '')
        
        if 'ransomware' in ioc_type or 'threat' in ioc_type:
            return str(value).strip() if value else None
        
        return None

    # =========================================================================
    # API & HTTP helpers
    # =========================================================================

    def _ensure_session(self):
        """Create HTTP session with retry logic."""
        if self._session is not None:
            return
        
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry = Retry(
            total=2,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=None
        )
        
        self._session = requests.Session()
        adapter = HTTPAdapter(max_retries=retry)
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def _make_api_request(self, endpoint: str, config: Dict, requires_auth: bool = False) -> Optional[Any]:
        """Make API request to Ransomware.live."""
        self._ensure_session()
        
        base_url = config['api_url'].rstrip('/')
        url = f"{base_url}{endpoint}"
        timeout = config.get('timeout', 30)
        api_key = config.get('api_key', '')
        
        headers = {'Accept': 'application/json'}
        if api_key:
            headers['X-API-KEY'] = api_key
        elif requires_auth:
            self.log.warning(f"[RL] Endpoint {endpoint} requires auth but no API key configured")
            return None
        
        try:
            self.log.info(f"[RL] GET {url}")
            r = self._session.get(url, headers=headers, timeout=timeout)
            
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                self.log.warning(f"[RL] Not found: {url}")
                return None
            else:
                self.log.warning(f"[RL] HTTP {r.status_code} for {url}")
                return None
                
        except requests.RequestException as e:
            self.log.error(f"[RL] Request error: {e}")
            return None

    def _log(self, level: str, message: str):
        """Helper logging method."""
        if level == 'info':
            self.log.info(f"[RL] {message}")
        elif level == 'error':
            self.log.error(f"[RL] {message}")
        elif level == 'warning':
            self.log.warning(f"[RL] {message}")

    # =========================================================================
    # Note helpers
    # =========================================================================

    def _create_note_folder(self, caseid: int, folder_title: str = "Ransomware.live Intelligence") -> Optional[int]:
        """Create or get note folder for ransomware intelligence."""
        try:
            folders = self.case_get_notes_directory(caseid=caseid)
            if folders and hasattr(folders, 'is_success') and folders.is_success():
                for folder in (folders.get_data() or []):
                    if isinstance(folder, dict) and folder.get('name') == folder_title:
                        return folder.get('id')
            
            result = self.case_add_notes_directory(
                caseid=caseid,
                directory_name=folder_title
            )
            
            if result and hasattr(result, 'is_success') and result.is_success():
                data = result.get_data()
                if isinstance(data, dict):
                    return data.get('id')
            
            return None
            
        except Exception as e:
            self.log.error(f"[RL] Failed to create note folder: {e}")
            return None

    def _add_note(self, caseid: int, title: str, content: str, folder_id: Optional[int] = None) -> bool:
        """Add a note to a case."""
        try:
            kwargs = {
                'caseid': caseid,
                'note_title': f"🎯 Ransomware.live - {title}",
                'note_content': content,
            }
            if folder_id is not None:
                kwargs['note_directory_id'] = folder_id
            
            result = self.case_add_note(**kwargs)
            
            if result and hasattr(result, 'is_success') and result.is_success():
                self.log.info(f"[RL] ✓ Note added: {title}")
                return True
            else:
                msg = result.get_message() if result and hasattr(result, 'get_message') else 'Unknown error'
                self.log.error(f"[RL] Failed to add note '{title}': {msg}")
                return False
                
        except Exception as e:
            self.log.error(f"[RL] Error adding note '{title}': {e}")
            return False

    # =========================================================================
    # Main enrichment orchestrator
    # =========================================================================

    def _enrich_case(self, case_id: int, group: str, config: Dict) -> bool:
        """Enrich case with Ransomware.live intelligence."""
        self.log.info(f"[RL] Starting enrichment for group '{group}' on case {case_id}")
        
        all_success = True
        
        # Create note folder
        folder_id = self._create_note_folder(case_id)
        if folder_id:
            self.log.info(f"[RL] Note folder ID: {folder_id}")
        else:
            self.log.warning("[RL] Could not create note folder, notes will go to root")
        
        # 1. Group Profile
        if not self._enrich_group_profile(case_id, group, config, folder_id):
            all_success = False
        
        # 2. Recent Victims
        if not self._enrich_victims(case_id, group, config, folder_id):
            all_success = False
        
        # 3. IOCs (requires auth)
        if not self._enrich_iocs(case_id, group, config, folder_id):
            all_success = False
        
        # 4. Ransom Notes
        if not self._enrich_ransom_notes(case_id, group, config, folder_id):
            all_success = False
        
        # 5. YARA Rules (requires auth)
        if not self._enrich_yara_rules(case_id, group, config, folder_id):
            all_success = False
        
        status = "completed successfully" if all_success else "completed with some errors"
        self.log.info(f"[RL] Enrichment {status} for group '{group}' on case {case_id}")
        
        return all_success

    # =========================================================================
    # Enrichment methods
    # =========================================================================

    def _enrich_group_profile(self, caseid: int, group: str, config: Dict, folder_id: Optional[int]) -> bool:
        """Enrich with group profile information."""
        try:
            self._log('info', "Fetching group profile...")
            
            data = self._make_api_request(f"/group/{group}", config)
            if not data:
                self._log('warning', f"No profile data for group: {group}")
                return False
            
            # Handle list response
            if isinstance(data, list) and data:
                data = data[0]
            
            group_name = data.get('group_name', data.get('group', data.get('name', group)))
            
            content = f"# {group.upper()} - Ransomware Group Profile\n\n"
            content += f"**Data source:** Ransomware.live API  \n"
            content += f"**Retrieved:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  \n\n"
            
            # Description
            description = data.get('description', '')
            if description:
                content += f"## Description\n\n{description}\n\n"
            
            # Metadata
            content += "## Key Information\n\n"
            
            fields = [
                ('first_seen', 'First Seen'), ('firstseen', 'First Seen'),
                ('last_seen', 'Last Active'), ('lastseen', 'Last Active'),
                ('victims_count', 'Total Victims'), ('victims', 'Total Victims'),
                ('url', 'Leak Site URL'),
                ('status', 'Status'),
                ('country', 'Country of Origin'),
            ]
            
            seen_labels = set()
            for key, label in fields:
                if label in seen_labels:
                    continue
                val = data.get(key)
                if val:
                    content += f"- **{label}:** {val}\n"
                    seen_labels.add(label)
            
            # Locations / Sites
            locations = data.get('locations', [])
            if locations:
                content += "\n## Known Sites\n\n"
                for loc in locations:
                    if isinstance(loc, dict):
                        slug = loc.get('slug', loc.get('fqdn', 'N/A'))
                        status = loc.get('available', 'unknown')
                        content += f"- `{slug}` (available: {status})\n"
                    else:
                        content += f"- `{loc}`\n"
            
            # TTPs
            ttps = data.get('ttps', [])
            if ttps:
                content += "\n## MITRE ATT&CK TTPs\n\n"
                for tactic in ttps[:10]:
                    if isinstance(tactic, dict):
                        tactic_name = tactic.get('tactic_name', '')
                        if tactic_name:
                            content += f"\n### {tactic_name}\n\n"
                            techniques = tactic.get('techniques', [])
                            for tech in techniques[:10]:
                                tech_id = tech.get('technique_id', '')
                                tech_name = tech.get('technique_name', '')
                                if tech_id and tech_name:
                                    content += f"- **{tech_id}**: {tech_name}\n"
            
            self._add_note(caseid, f"{group.upper()} - Profile", content, folder_id)
            self._log('info', f"✓ Group profile added for {group}")
            return True
            
        except Exception as e:
            self._log('error', f"Error enriching group profile: {e}")
            return False

    def _enrich_victims(self, caseid: int, group: str, config: Dict, folder_id: Optional[int]) -> bool:
        """Enrich with recent victims data."""
        try:
            self._log('info', "Fetching recent victims...")
            
            data = self._make_api_request(f"/group/{group}", config)
            if not data:
                return False
            
            # Extract posts/victims
            posts = []
            if isinstance(data, list):
                posts = data
            elif isinstance(data, dict):
                posts = data.get('posts', data.get('victims', []))
            
            if not posts:
                self._log('info', "No victim data available")
                return True  # Not an error, just no data
            
            # Limit to 30 most recent
            posts = posts[:30]
            
            content = f"# {group.upper()} - Recent Victims\n\n"
            content += f"**Data source:** Ransomware.live API  \n"
            content += f"**Retrieved:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  \n"
            content += f"**Count:** {len(posts)}  \n\n"
            
            content += "| Date | Victim | Website | Country |\n"
            content += "|------|--------|---------|----------|\n"
            
            for post in posts:
                if isinstance(post, dict):
                    discovered = post.get('discovered', post.get('date', 'Unknown'))
                    title = post.get('post_title', post.get('title', post.get('victim', 'N/A')))
                    website = post.get('website', post.get('url', 'N/A'))
                    country = post.get('country', 'N/A')
                    content += f"| {discovered} | {title} | {website} | {country} |\n"
            
            self._add_note(caseid, f"{group.upper()} - Victims", content, folder_id)
            self._log('info', f"✓ Victims: {len(posts)} entries added")
            return True
            
        except Exception as e:
            self._log('error', f"Error enriching victims: {e}")
            return False

    def _enrich_iocs(self, caseid: int, group: str, config: Dict, folder_id: Optional[int]) -> bool:
        """Enrich with Indicators of Compromise."""
        try:
            self._log('info', "Fetching IOCs...")
            
            data = self._make_api_request(f"/iocs/{group}", config, requires_auth=True)
            if not data:
                self._log('info', "No IOC data available (may require API key)")
                return True
            
            # Parse IOCs by type
            ioc_types = {}
            ioc_list = data if isinstance(data, list) else [data]
            
            for ioc_entry in ioc_list:
                if isinstance(ioc_entry, dict):
                    ioc_type = ioc_entry.get('type', ioc_entry.get('ioc_type', 'unknown'))
                    ioc_value = ioc_entry.get('value', ioc_entry.get('ioc_value', ''))
                    
                    if ioc_type not in ioc_types:
                        ioc_types[ioc_type] = []
                    if ioc_value:
                        ioc_types[ioc_type].append(ioc_value)
            
            if not ioc_types:
                self._log('info', "No IOCs parsed from response")
                return True
            
            content = f"# {group.upper()} - Indicators of Compromise\n\n"
            content += f"**Data source:** Ransomware.live API  \n"
            content += f"**Retrieved:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  \n\n"
            
            for ioc_type, values in sorted(ioc_types.items()):
                unique_values = sorted(set(values))
                content += f"## {ioc_type.upper()} ({len(unique_values)})\n\n"
                content += "```\n"
                for value in unique_values:
                    content += f"{value}\n"
                content += "```\n\n"
            
            self._add_note(caseid, f"{group.upper()} - IOCs", content, folder_id)
            self._log('info', "✓ IOCs added")
            return True
            
        except Exception as e:
            self._log('error', f"Error enriching IOCs: {e}")
            return False

    def _enrich_ransom_notes(self, caseid: int, group: str, config: Dict, folder_id: Optional[int]) -> bool:
        """Enrich with ransom note samples."""
        try:
            self._log('info', "Fetching ransom notes...")
            
            data = self._make_api_request(f"/ransomnotes/{group}", config)
            if not data:
                self._log('info', "No ransom notes available")
                return True
            
            notes = data if isinstance(data, list) else data.get('ransomnotes', [data])
            
            if not notes:
                return True
            
            content = f"# {group.upper()} - Ransom Notes\n\n"
            content += f"**Data source:** Ransomware.live API  \n"
            content += f"**Retrieved:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  \n"
            content += f"**Samples:** {len(notes)}  \n\n"
            
            for i, note in enumerate(notes[:5], 1):
                note_text = note.get('note', note) if isinstance(note, dict) else str(note)
                if note_text:
                    content += f"## Sample {i}\n\n"
                    content += "```\n"
                    content += str(note_text)[:2000]
                    if len(str(note_text)) > 2000:
                        content += "\n... (truncated)"
                    content += "\n```\n\n"
            
            self._add_note(caseid, f"{group.upper()} - Ransom Notes", content, folder_id)
            self._log('info', "✓ Ransom notes added")
            return True
            
        except Exception as e:
            self._log('error', f"Error enriching ransom notes: {e}")
            return False

    def _enrich_yara_rules(self, caseid: int, group: str, config: Dict, folder_id: Optional[int]) -> bool:
        """Enrich with YARA rules."""
        try:
            self._log('info', "Fetching YARA rules...")
            
            data = self._make_api_request(f"/yara/{group}", config, requires_auth=True)
            if not data:
                self._log('info', "No YARA rules available (may require API key)")
                return True
            
            rules = data if isinstance(data, list) else [data]
            
            if not rules:
                return True
            
            content = f"# {group.upper()} - YARA Rules\n\n"
            content += f"**Data source:** Ransomware.live API  \n"
            content += f"**Retrieved:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  \n"
            content += f"**Rules:** {len(rules)}  \n\n"
            
            for rule in rules:
                if isinstance(rule, dict):
                    name = rule.get('name', rule.get('rule_name', 'Unknown'))
                    rule_content = rule.get('rule', rule.get('content', ''))
                else:
                    name = 'Unknown'
                    rule_content = str(rule)
                
                content += f"## {name}\n\n"
                content += "```yara\n"
                content += str(rule_content)
                content += "\n```\n\n"
            
            self._add_note(caseid, f"{group.upper()} - YARA Rules", content, folder_id)
            self._log('info', "✓ YARA rules added")
            return True
            
        except Exception as e:
            self._log('error', f"Error enriching YARA rules: {e}")
            return False