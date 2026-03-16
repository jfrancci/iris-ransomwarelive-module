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

import requests # type: ignore

try:
    from iris_interface.IrisModuleInterface import IrisModuleInterface, IrisModuleTypes # type: ignore
    import iris_interface.IrisInterfaceStatus as InterfaceStatus # type: ignore
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
            # Hook para execução MANUAL
            self.register_to_hook(module_id, iris_hook_name="on_manual_trigger_case")
            self.register_to_hook(module_id, iris_hook_name="on_manual_trigger_ioc")
            
            # Hook CORRETO para execução AUTOMÁTICA ao criar caso
            self.register_to_hook(module_id, iris_hook_name="on_postload_case_create")
            
            # Hook CORRETO para execução AUTOMÁTICA ao atualizar caso
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
            # Load configuration
            config = self._load_config()
            
            # Process based on hook type
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
        # Extract case data
        if isinstance(data, list) and data:
            data = data[0]
        
        case = data.get('case', data) if isinstance(data, dict) else data
        case_id = self._get_case_id(case)
        
        if not case_id:
            return InterfaceStatus.I2Error("No case ID found")
        
        # Extract ransomware group
        group = self._extract_ransomware_group(case)
        
        if not group:
            if is_automatic:
                # Se automático e não tem grupo, apenas ignora silenciosamente
                self.log.info(f"[RL] Case {case_id} has no ransomware_group - skipping automatic enrichment")
                return InterfaceStatus.I2Success(data=data)
            else:
                # Se manual, informa o erro ao usuário
                return InterfaceStatus.I2Error(
                    "No ransomware group detected. Please fill the 'ransomware_group' field in the case."
                )
        
        execution_type = "automatic" if is_automatic else "manual"
        self.log.info(f"[RL] Enriching case {case_id} ({execution_type}) with group: {group}")
        
        # Perform enrichment
        success = self._enrich_case(case_id, group, config)
        
        if success:
            message = f"Successfully enriched case with {group} intelligence"
            if is_automatic:
                message += " (automatic execution)"
            
            return InterfaceStatus.I2Success(
                data=data,
                logs=message
            )
        else:
            return InterfaceStatus.I2Success(
                data=data,
                logs="Enrichment completed with some errors. Check logs for details."
            )
    
    def _handle_ioc_trigger(self, data, config):
        """Handle IOC-based trigger."""
        if isinstance(data, list) and data:
            data = data[0]
        
        ioc = data.get('ioc', data) if isinstance(data, dict) else data
        case_id = self._get_case_id(ioc)
        
        if not case_id:
            return InterfaceStatus.I2Error("No case ID found in IOC")
        
        # Extract group from IOC
        group = self._extract_group_from_ioc(ioc)
        if not group:
            return InterfaceStatus.I2Error("IOC is not a ransomware group indicator")
        
        self.log.info(f"[RL] Enriching case {case_id} from IOC with group: {group}")
        
        # Perform enrichment
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
            from app import db # type: ignore
            from sqlalchemy import text # type: ignore
            import json
            
            # Busca diretamente na tabela cases usando SQL
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
            
            # Se for string, parseia como JSON
            if isinstance(custom_attrs, str):
                try:
                    custom_attrs = json.loads(custom_attrs)
                except Exception as e:
                    self.log.error(f"[RL] Failed to parse JSON: {e}")
                    return None
            
            # custom_attrs já deve ser dict (PostgreSQL JSON field)
            if not isinstance(custom_attrs, dict):
                self.log.error(f"[RL] custom_attributes is not a dict: {type(custom_attrs)}")
                return None
            
            self.log.info(f"[RL] custom_attributes keys: {list(custom_attrs.keys())}")
            
            # Navega pela estrutura: {"Ransomware Group": {"ransomware_group": {"value": "Akira"}}}
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
            import traceback
            self.log.error(f"[RL] Traceback: {traceback.format_exc()}")
            return None
        
    def _extract_group_from_ioc(self, ioc) -> Optional[str]:
        """Extract ransomware group from IOC."""
        if isinstance(ioc, dict):
            ioc_type = str(ioc.get('ioc_type_name', '')).lower()
            value = ioc.get('ioc_value', '')
        else:
            ioc_type_obj = getattr(ioc, 'ioc_type', None)
            ioc_type = str(getattr(ioc_type_obj, 'type_name', '')).lower() if ioc_type_obj else ''
            value = getattr(ioc, 'ioc_value', '')
        
        if 'ransomware' in ioc_type or 'threat' in ioc_type:
            return str(value).strip()
        
        return None
    
    def _get_custom_fields(self, case) -> List:
        """Get custom fields from case."""
        if isinstance(case, dict):
            return case.get('custom_fields', []) or []
        else:
            cf = getattr(case, 'custom_fields', None)
            return list(cf) if cf and hasattr(cf, '__iter__') else []
    
    def _add_iocs_to_case(self, case_id: int, group: str, iocs_data: Dict) -> int:
        """Add IOCs from API to the case IOC tab."""
        self.log.info(f"[RL] ===== ADDING IOCs TO CASE {case_id} =====")
        
        added_count = 0
        
        try:
            from app import db # type: ignore
            from sqlalchemy import text # type: ignore
            
            # A estrutura da API é: {"client": "...", "group": "...", "iocs": {"sha256": [...], "btc": [...], ...}}
            if 'iocs' not in iocs_data or not isinstance(iocs_data['iocs'], dict):
                self.log.warning("[RL] No 'iocs' dictionary found in API response")
                return 0
            
            iocs_dict = iocs_data['iocs']
            self.log.info(f"[RL] IOC types found: {list(iocs_dict.keys())}")
            
            # Map IOC types from API to IRIS IOC types
            ioc_type_mapping = {
                'ip': 'ip-dst',
                'ipv4': 'ip-dst',
                'domain': 'domain',
                'url': 'url',
                'hash': 'md5',
                'md5': 'md5',
                'sha1': 'sha1',
                'sha256': 'sha256',
                'email': 'email',
                'cryptocurrency': 'btc',
                'bitcoin': 'btc',
                'wallet': 'btc',
                'btc': 'btc',
                'eth': 'other',
                'xmr': 'xmr'
            }
            
            # Get available IOC types from database
            result = db.session.execute(text("SELECT type_id, type_name FROM ioc_type")).fetchall()
            ioc_type_cache = {row[1]: row[0] for row in result}
            
            self.log.info(f"[RL] Available IRIS IOC types: {len(ioc_type_cache)}")
            
            # Process each IOC category from API
            for api_type, values in iocs_dict.items():
                if not isinstance(values, list) or not values:
                    continue
                
                self.log.info(f"[RL] Processing '{api_type}' with {len(values)} values")
                
                # Map to IRIS IOC type
                api_type_lower = api_type.lower().replace(' ', '_').replace('-', '_')
                iris_type_name = ioc_type_mapping.get(api_type_lower, 'other')
                
                # Get IOC type ID
                if iris_type_name not in ioc_type_cache:
                    if 'other' in ioc_type_cache:
                        ioc_type_id = ioc_type_cache['other']
                    else:
                        self.log.error(f"[RL] No suitable IOC type found for {api_type}")
                        continue
                else:
                    ioc_type_id = ioc_type_cache[iris_type_name]
                
                # Add each IOC value
                for value in values[:100]:  # Limit to 100 per type
                    try:
                        value_str = str(value).strip()
                        if not value_str:
                            continue
                        
                        # Check if IOC already exists for this case
                        check_query = text("""
                            SELECT i.ioc_id 
                            FROM ioc i
                            JOIN ioc_link il ON i.ioc_id = il.ioc_id
                            WHERE i.ioc_value = :value AND il.case_id = :case_id
                        """)
                        existing = db.session.execute(
                            check_query, 
                            {"value": value_str, "case_id": case_id}
                        ).fetchone()
                        
                        if existing:
                            continue
                        
                        # Step 1: Insert IOC
                        insert_ioc_query = text("""
                            INSERT INTO ioc (
                                ioc_value, 
                                ioc_type_id, 
                                ioc_description, 
                                ioc_tags, 
                                ioc_tlp_id, 
                                user_id
                            ) VALUES (
                                :ioc_value,
                                :ioc_type_id,
                                :ioc_description,
                                :ioc_tags,
                                2,
                                1
                            ) RETURNING ioc_id
                        """)
                        
                        result = db.session.execute(insert_ioc_query, {
                            "ioc_value": value_str,
                            "ioc_type_id": ioc_type_id,
                            "ioc_description": f"From Ransomware.live: {group}",
                            "ioc_tags": f"ransomware,{group},ransomware-live"
                        })
                        
                        ioc_id = result.fetchone()[0]
                        
                        # Step 2: Create link to case
                        insert_link_query = text("""
                            INSERT INTO ioc_link (ioc_id, case_id)
                            VALUES (:ioc_id, :case_id)
                        """)
                        
                        db.session.execute(insert_link_query, {
                            "ioc_id": ioc_id,
                            "case_id": case_id
                        })
                        
                        added_count += 1
                        
                        if added_count % 10 == 0:
                            db.session.commit()
                            self.log.info(f"[RL] Added {added_count} IOCs so far...")
                    
                    except Exception as e:
                        self.log.warning(f"[RL] Failed to add IOC '{value}': {e}")
                        db.session.rollback()
                        continue
            
            # Final commit
            db.session.commit()
            
            if added_count > 0:
                self.log.info(f"[RL] ✓✓✓ Successfully added {added_count} IOCs to case")
            else:
                self.log.warning("[RL] ⚠️  No new IOCs were added")
            
            return added_count
        
        except Exception as e:
            self.log.error(f"[RL] Error adding IOCs: {e}")
            import traceback
            self.log.error(f"[RL] Traceback: {traceback.format_exc()}")
            try:
                db.session.rollback()
            except:
                pass
            return 0
        
    def _enrich_case(self, case_id: int, group: str, config: Dict) -> bool:
        """Enrich case with Ransomware.live intelligence."""
        # Normalize group name
        group_normalized = self._normalize_group_name(group)
        self.log.info(f"[RL] Normalized group name: {group_normalized}")
        
        # Initialize session with API key if available
        if not self._session:
            self._session = requests.Session()
            if config.get('api_key'):
                self._session.headers.update({'X-API-KEY': config['api_key']})
                self.log.info("[RL] API-KEY configured for requests")
            else:
                self.log.warning("[RL] No API-KEY configured - some endpoints may fail")
        
        success_count = 0
        total_attempts = 0
        
        # Fetch group profile
        total_attempts += 1
        if self._fetch_group_profile(case_id, group_normalized, config):
            success_count += 1
        
        # Fetch IOCs
        total_attempts += 1
        if self._fetch_iocs(case_id, group_normalized, config):
            success_count += 1
        
        # Fetch ransom notes
        total_attempts += 1
        if self._fetch_ransom_notes(case_id, group_normalized, config):
            success_count += 1
        
        # Fetch YARA rules
        total_attempts += 1
        if self._fetch_yara_rules(case_id, group_normalized, config):
            success_count += 1
        
        self.log.info(f"[RL] Enrichment complete: {success_count}/{total_attempts} successful")
        return success_count > 0
    
    def _normalize_group_name(self, group: str) -> str:
        """Normalize ransomware group name - capitalize first letter."""
        group = group.strip()
        
        # Remove caracteres especiais mas mantém letras e números
        group = re.sub(r'[^a-zA-Z0-9]', '', group)
        
        # Capitalize primeira letra (Akira, Lockbit, etc.)
        group = group.capitalize()
        
        # Common aliases (se necessário mapear nomes diferentes)
        aliases = {
            'Lockbit3': 'Lockbit',
            'Lockbit30': 'Lockbit',
            'Alphv': 'Blackcat',
            'Cl0p': 'Clop'
        }
        
        return aliases.get(group, group)
    
    def _fetch_group_profile(self, case_id: int, group: str, config: Dict) -> bool:
        """Fetch and add group profile information."""
        try:
            url = f"{config['api_url']}/groups/{group}"
            self.log.info(f"[RL] Fetching group profile: {url}")
            
            response = self._session.get(url, timeout=config['timeout'])
            self.log.info(f"[RL] Response status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                self.log.info(f"[RL] API returned data for group: {data.get('group_name', group)}")
                
                html_content = self._format_group_profile_html(data, group)
                self.log.info(f"[RL] HTML content generated, length: {len(html_content)} chars")
                
                # Log first 500 chars of HTML for debugging
                self.log.info(f"[RL] HTML preview: {html_content[:500]}...")
                
                if self._add_note(case_id, f"Ransomware.live: {group.upper()} Profile", html_content):
                    self.log.info("[RL] ✓ Group profile note created successfully")
                    return True
                else:
                    self.log.error("[RL] ✗ Failed to create group profile note")
                    return False
            elif response.status_code == 404:
                self.log.warning(f"[RL] Group not found: {group}")
            else:
                self.log.error(f"[RL] API error {response.status_code}: {response.text[:200]}")
        
        except Exception as e:
            self.log.error(f"[RL] Error fetching group profile: {e}")
            import traceback
            self.log.error(f"[RL] Traceback: {traceback.format_exc()}")
        
        return False
    
    def _fetch_iocs(self, case_id: int, group: str, config: Dict) -> bool:
        """Fetch IOCs and add them both as note AND as IOCs in the case."""
        try:
            url = f"{config['api_url']}/iocs/{group}"
            self.log.info(f"[RL] Fetching IOCs: {url}")
            
            response = self._session.get(url, timeout=config['timeout'])
            
            if response.status_code == 200:
                data = response.json()
                
                if data and isinstance(data, dict):
                    # Create note with IOCs
                    html_content = self._format_iocs_html(data, group)
                    note_created = self._add_note(case_id, f"Ransomware.live: {group.upper()} IOCs", html_content)
                    
                    # ADD IOCs to the case
                    iocs_added = self._add_iocs_to_case(case_id, group, data)
                    
                    if note_created or iocs_added > 0:
                        self.log.info(f"[RL] IOCs processed: Note={note_created}, IOCs added={iocs_added}")
                        return True
            elif response.status_code == 404:
                self.log.info(f"[RL] No IOCs found for {group}")
        
        except Exception as e:
            self.log.error(f"[RL] Error fetching IOCs: {e}")
        
        return False
    
    def _fetch_ransom_notes(self, case_id: int, group: str, config: Dict) -> bool:
        """Fetch and add ransom notes."""
        try:
            url = f"{config['api_url']}/ransomnotes/{group}"
            self.log.info(f"[RL] Fetching ransom notes: {url}")
            
            response = self._session.get(url, timeout=config['timeout'])
            
            if response.status_code == 200:
                data = response.json()
                notes = data.get('ransomnotes', [])
                
                if notes:
                    html_content = self._format_ransom_notes_html(notes, group)
                    
                    if self._add_note(case_id, f"Ransomware.live: {group.upper()} Ransom Notes", html_content):
                        self.log.info(f"[RL] Ransom notes created ({len(notes)} samples)")
                        return True
            elif response.status_code == 404:
                self.log.info(f"[RL] No ransom notes found for {group}")
        
        except Exception as e:
            self.log.error(f"[RL] Error fetching ransom notes: {e}")
        
        return False
    
    def _fetch_yara_rules(self, case_id: int, group: str, config: Dict) -> bool:
        """Fetch and add YARA rules."""
        try:
            url = f"{config['api_url']}/yara/{group}"
            self.log.info(f"[RL] Fetching YARA rules: {url}")
            
            response = self._session.get(url, timeout=config['timeout'])
            
            if response.status_code == 200:
                data = response.json()
                
                if data and isinstance(data, dict):
                    html_content = self._format_yara_rules_html(data, group)
                    
                    if self._add_note(case_id, f"Ransomware.live: {group.upper()} YARA Rules", html_content):
                        self.log.info("[RL] YARA rules note created")
                        return True
            elif response.status_code == 404:
                self.log.info(f"[RL] No YARA rules found for {group}")
        
        except Exception as e:
            self.log.error(f"[RL] Error fetching YARA rules: {e}")
        
        return False
    
    def _format_group_profile_html(self, data: Dict, group: str) -> str:
        """Format group profile data as Markdown."""
        group_name = data.get('group_name', data.get('group', group.upper()))
        
        # Use Markdown formatting instead of HTML
        content = f"# 🔒 {group_name}\n\n"
        content += "*Ransomware Group Intelligence Report*\n\n"
        content += "---\n\n"
        
        # Description
        if data.get('description'):
            content += f"## 📋 Description\n\n{data['description']}\n\n"
        
        # Statistics
        content += "## 📊 Statistics\n\n"
        
        if data.get('victims') or data.get('victims_count'):
            victims = data.get('victims') or data.get('victims_count')
            content += f"**Victims:** {victims}\n\n"
        
        if data.get('firstseen') or data.get('first_seen'):
            first = data.get('firstseen') or data.get('first_seen')
            content += f"**First Seen:** {first}\n\n"
        
        if data.get('lastseen') or data.get('last_seen'):
            last = data.get('lastseen') or data.get('last_seen')
            content += f"**Last Seen:** {last}\n\n"
        
        # TTPs
        ttps = data.get('ttps', [])
        if ttps:
            content += "## 🎯 MITRE ATT&CK TTPs\n\n"
            for ttp in ttps:
                content += f"- `{ttp}`\n"
            content += "\n"
        
        # Locations
        locations = data.get('locations', [])
        if locations:
            content += "## 🌐 Dark Web Locations\n\n"
            for loc in locations:
                status = "🟢 Online" if loc.get('available') else "🔴 Offline"
                title = loc.get('title', 'Unknown')
                fqdn = loc.get('fqdn', 'N/A')
                loc_type = loc.get('type', 'Unknown')
                updated = loc.get('updated', 'N/A')
                
                content += f"### {title}\n\n"
                content += f"- **Status:** {status}\n"
                content += f"- **Address:** `{fqdn}`\n"
                content += f"- **Type:** {loc_type}\n"
                content += f"- **Last Updated:** {updated}\n\n"
        
        # Footer
        content += "---\n\n"
        content += f"**Source:** [Ransomware.live]({data.get('url', 'https://www.ransomware.live')})\n\n"
        content += f"**Report Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        
        return content
    
    def _format_iocs_html(self, data: Dict, group: str) -> str:
        """Format IOCs as Markdown."""
        content = f"# 🔍 {group.upper()} - Indicators of Compromise\n\n"
        
        # Process different IOC types
        ioc_count = 0
        for key, values in data.items():
            if isinstance(values, list) and values:
                content += f"## {key.replace('_', ' ').title()}\n\n"
                for ioc in values[:50]:  # Limit to 50 per type
                    content += f"- `{ioc}`\n"
                    ioc_count += 1
                content += "\n"
        
        if ioc_count == 0:
            content += "*No IOCs available for this group.*\n\n"
        
        content += "---\n\n"
        content += f"**Total IOCs:** {ioc_count}\n\n"
        content += f"**Report Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        
        return content
    
    def _format_ransom_notes_html(self, notes: List, group: str) -> str:
        """Format ransom notes as Markdown."""
        content = f"# 📝 {group.upper()} - Ransom Notes\n\n"
        content += f"*{len(notes)} sample(s) available*\n\n"
        content += "---\n\n"
        
        for i, note in enumerate(notes[:5], 1):  # Show first 5 notes
            note_content = str(note)[:1000]  # Limit content
            if len(str(note)) > 1000:
                note_content += "\n... (truncated)"
            
            content += f"## Sample {i}\n\n"
            content += "```\n"
            content += note_content
            content += "\n```\n\n"
        
        content += "---\n\n"
        content += "**Note:** Use these samples to identify ransomware infections and understand attacker communication methods.\n\n"
        content += f"**Report Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        
        return content
    
    def _format_yara_rules_html(self, data: Dict, group: str) -> str:
        """Format YARA rules as Markdown."""
        content = f"# 🛡️ {group.upper()} - YARA Detection Rules\n\n"
        
        content += "## YARA Rules\n\n"
        content += "```yara\n"
        content += json.dumps(data, indent=2)
        content += "\n```\n\n"
        
        content += "---\n\n"
        content += "**Usage:** Deploy these YARA rules in your security infrastructure for ransomware detection.\n\n"
        content += f"**Report Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
        
        return content
    
    def _add_note(self, case_id: int, title: str, content: str) -> bool:
        """Add note to case with proper directory structure."""
        self.log.info(f"[RL] Adding note: {title}")
        
        try:
            from app import db # type: ignore
            from app.models.models import Notes # type: ignore
            from datetime import datetime
            from sqlalchemy import text # type: ignore
            
            # Try to get or create a directory for Ransomware.live notes
            directory_id = None
            try:
                # Use SQLAlchemy text() to avoid the warning
                result = db.session.execute(
                    text("SELECT id, name FROM note_directory WHERE case_id = :case_id AND name = :name"),
                    {"case_id": case_id, "name": "Ransomware details"}
                ).fetchone()
                
                if result:
                    directory_id = result[0]
                    self.log.info(f"[RL] Using existing 'Ransomware details' directory ID: {directory_id}")
                else:
                    # Create new directory
                    self.log.info("[RL] Creating 'Ransomware details' directory...")
                    result = db.session.execute(
                        text("INSERT INTO note_directory (name, case_id, parent_id) VALUES (:name, :case_id, NULL) RETURNING id"),
                        {"name": "Ransomware details", "case_id": case_id}
                    )
                    db.session.commit()
                    directory_id = result.fetchone()[0]
                    self.log.info(f"[RL] Created directory ID: {directory_id}")
                
            except Exception as dir_error:
                self.log.warning(f"[RL] Directory creation failed: {dir_error}")
                # If no directory exists and we can't create one, try to find ANY directory for this case
                try:
                    result = db.session.execute(
                        text("SELECT id FROM note_directory WHERE case_id = :case_id LIMIT 1"),
                        {"case_id": case_id}
                    ).fetchone()
                    if result:
                        directory_id = result[0]
                        self.log.info(f"[RL] Using fallback directory ID: {directory_id}")
                except:
                    pass
            
            # Create the note
            note = Notes()
            note.note_title = title
            note.note_content = content
            note.note_creationdate = datetime.utcnow()
            note.note_lastupdate = datetime.utcnow()
            note.note_case_id = case_id
            note.note_user = 1
            
            # CRITICAL: Set directory_id
            if directory_id:
                note.directory_id = directory_id
                self.log.info(f"[RL] Assigning note to directory: {directory_id}")
            else:
                self.log.error("[RL] ⚠️  WARNING: Creating note WITHOUT directory_id - it may not appear in UI!")
            
            db.session.add(note)
            db.session.commit()
            db.session.refresh(note)
            
            self.log.info(f"[RL] ✓ Note created (ID: {note.note_id}, Dir: {note.directory_id})")
            
            # Verify the note
            verify = db.session.query(Notes).filter(Notes.note_id == note.note_id).first()
            if verify:
                if verify.directory_id:
                    self.log.info(f"[RL] ✓✓ Note verified with directory_id: {verify.directory_id}")
                    return True
                else:
                    self.log.warning(f"[RL] ⚠️  Note created but has no directory_id!")
                    return True  # Still return True as note was created
            else:
                self.log.error(f"[RL] ✗ Note not found after creation!")
                return False
            
        except Exception as e:
            self.log.error(f"[RL] Failed to create note: {e}")
            import traceback
            self.log.error(f"[RL] Traceback: {traceback.format_exc()}")
            try:
                db.session.rollback()
            except:
                pass
            return False