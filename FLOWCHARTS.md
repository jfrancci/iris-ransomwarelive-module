# Flowcharts - IRIS Ransomware.live Module

## 📊 System Overview

```mermaid
graph TB
    subgraph "DFIR-IRIS Platform"
        UI[Web Interface]
        APP[App Container]
        WORKER[Worker Container]
        DB[(PostgreSQL DB)]
    end
    
    subgraph "Ransomware.live Module"
        MODULE[RansomwareLiveModule]
        HOOKS[Hook Handlers]
        API_CLIENT[API Client]
    end
    
    subgraph "External Services"
        RLAPI[Ransomware.live API]
        INTEL[Threat Intelligence DB]
    end
    
    UI --> APP
    APP --> MODULE
    MODULE --> WORKER
    WORKER --> HOOKS
    HOOKS --> API_CLIENT
    API_CLIENT --> RLAPI
    RLAPI --> INTEL
    MODULE --> DB
    
    style MODULE fill:#4CAF50
    style RLAPI fill:#FF9800
    style DB fill:#2196F3
```

---

## 🔄 Complete Enrichment Flow

```mermaid
flowchart TD
    START([Start]) --> TRIGGER{Trigger Type}
    
    TRIGGER -->|Manual| MANUAL[User clicks<br/>Processors Button]
    TRIGGER -->|Automatic| AUTO[Case created/updated<br/>with ransomware_group]
    
    MANUAL --> EXTRACT
    AUTO --> CHECK_AUTO{Auto-enrich<br/>enabled?}
    
    CHECK_AUTO -->|No| END1([End - No action])
    CHECK_AUTO -->|Yes| EXTRACT
    
    EXTRACT[Extract ransomware_group<br/>from custom_attribute]
    
    EXTRACT --> HAS_GROUP{Group<br/>found?}
    
    HAS_GROUP -->|No - Manual| ERROR1[Return error:<br/>Field empty]
    HAS_GROUP -->|No - Auto| END2([End - Ignored])
    HAS_GROUP -->|Yes| NORMALIZE
    
    ERROR1 --> END3([End])
    
    NORMALIZE[Normalize group name<br/>Ex: Cl0p → Clop]
    
    NORMALIZE --> INIT_SESSION[Initialize HTTP session<br/>+ API Key if available]
    
    INIT_SESSION --> FETCH_PROFILE
    
    subgraph "Fetch Intelligence"
        FETCH_PROFILE[GET /groups/group]
        FETCH_PROFILE --> PROFILE_OK{Status 200?}
        
        PROFILE_OK -->|Yes| CREATE_NOTE1[Create note:<br/>Group Profile]
        PROFILE_OK -->|404| LOG1[Log: Group not found]
        PROFILE_OK -->|Error| LOG2[Log: API error]
        
        CREATE_NOTE1 --> FETCH_IOCS
        LOG1 --> FETCH_IOCS
        LOG2 --> FETCH_IOCS
        
        FETCH_IOCS[GET /iocs/group]
        FETCH_IOCS --> IOCS_OK{Status 200?}
        
        IOCS_OK -->|Yes| CREATE_NOTE2[Create note: IOCs]
        IOCS_OK -->|404/Error| FETCH_NOTES
        
        CREATE_NOTE2 --> ADD_IOCS[Add IOCs to IOC tab<br/>147+ indicators]
        ADD_IOCS --> FETCH_NOTES
        
        FETCH_NOTES[GET /ransomnotes/group]
        FETCH_NOTES --> NOTES_OK{Status 200?}
        
        NOTES_OK -->|Yes| CREATE_NOTE3[Create note:<br/>Ransom Notes]
        NOTES_OK -->|404/Error| FETCH_YARA
        
        CREATE_NOTE3 --> FETCH_YARA
        
        FETCH_YARA[GET /yara/group]
        FETCH_YARA --> YARA_OK{Status 200?}
        
        YARA_OK -->|Yes| CREATE_NOTE4[Create note:<br/>YARA Rules]
        YARA_OK -->|404/Error| CALCULATE
        
        CREATE_NOTE4 --> CALCULATE
    end
    
    CALCULATE[Calculate success:<br/>X/4 endpoints]
    
    CALCULATE --> SUCCESS{Any<br/>success?}
    
    SUCCESS -->|Yes| RETURN_SUCCESS[Return I2Success<br/>with message]
    SUCCESS -->|No| RETURN_ERROR[Return I2Success<br/>with warnings]
    
    RETURN_SUCCESS --> LOG_FINAL[Log: Enrichment complete]
    RETURN_ERROR --> LOG_FINAL
    
    LOG_FINAL --> END([End])
    
    style START fill:#4CAF50
    style END fill:#4CAF50
    style END1 fill:#9E9E9E
    style END2 fill:#9E9E9E
    style END3 fill:#F44336
    style CREATE_NOTE1 fill:#2196F3
    style CREATE_NOTE2 fill:#2196F3
    style CREATE_NOTE3 fill:#2196F3
    style CREATE_NOTE4 fill:#2196F3
    style ADD_IOCS fill:#FF9800
```

---

## 🎯 Ransomware Group Extraction Detail

```mermaid
flowchart TD
    START([Receive Case Object]) --> GET_ID[Extract case_id]
    
    GET_ID --> HAS_ID{case_id<br/>valid?}
    
    HAS_ID -->|No| ERROR1[Log: No case_id found]
    HAS_ID -->|Yes| QUERY_DB[SQL Query custom_attributes]
    
    ERROR1 --> END1([End])
    
    QUERY_DB --> HAS_ATTRS{Attributes<br/>exist?}
    
    HAS_ATTRS -->|No| LOG1[Log: No attributes]
    HAS_ATTRS -->|Yes| CHECK_TYPE{Is<br/>string?}
    
    LOG1 --> END2([End])
    
    CHECK_TYPE -->|Yes| PARSE_JSON[Parse JSON]
    CHECK_TYPE -->|No| CHECK_DICT{Is<br/>dict?}
    
    PARSE_JSON --> PARSE_OK{Parse<br/>OK?}
    
    PARSE_OK -->|No| ERROR2[Log: Parse failed]
    PARSE_OK -->|Yes| CHECK_DICT
    
    ERROR2 --> END3([End])
    
    CHECK_DICT -->|No| ERROR3[Log: Not a dict]
    CHECK_DICT -->|Yes| ITERATE[Iterate keys]
    
    ERROR3 --> END4([End])
    
    ITERATE --> LOOP{For each<br/>key}
    
    LOOP --> HAS_FIELD{Has<br/>ransomware_group?}
    
    HAS_FIELD -->|No| LOOP
    HAS_FIELD -->|Yes| GET_VALUE[Get field_data]
    
    GET_VALUE --> IS_DICT{Is<br/>dict?}
    
    IS_DICT -->|No| LOOP
    IS_DICT -->|Yes| HAS_VALUE{Has<br/>value?}
    
    HAS_VALUE -->|No| LOOP
    HAS_VALUE -->|Yes| EXTRACT[Extract and strip]
    
    EXTRACT --> IS_EMPTY{Empty?}
    
    IS_EMPTY -->|Yes| LOG2[Log: Empty value]
    IS_EMPTY -->|No| SUCCESS[Return group name]
    
    LOG2 --> END5([End])
    SUCCESS --> END6([Success])
    
    LOOP --> NOT_FOUND[Log: Field not found]
    NOT_FOUND --> END7([End])
    
    style START fill:#4CAF50
    style END6 fill:#4CAF50
    style SUCCESS fill:#4CAF50
    style ERROR1 fill:#F44336
    style ERROR2 fill:#F44336
    style ERROR3 fill:#F44336
```

---

## 📝 Note Creation Detail

```mermaid
flowchart TD
    START([Create Note]) --> GET_DIR{Directory<br/>exists?}
    
    GET_DIR -->|Yes| USE_DIR[Use existing<br/>directory_id]
    GET_DIR -->|No| CREATE_DIR[Create directory:<br/>Ransomware details]
    
    CREATE_DIR --> DIR_OK{Created<br/>OK?}
    
    DIR_OK -->|Yes| GET_NEW_ID[Get new<br/>directory_id]
    DIR_OK -->|No| FALLBACK[Search any<br/>case directory]
    
    GET_NEW_ID --> USE_DIR
    
    FALLBACK --> FOUND{Found?}
    
    FOUND -->|Yes| USE_FALLBACK[Use found<br/>directory_id]
    FOUND -->|No| WARN[Log: WARNING<br/>No directory]
    
    USE_FALLBACK --> USE_DIR
    
    WARN --> CREATE_NOTE
    USE_DIR --> CREATE_NOTE
    
    CREATE_NOTE[Create Note object:<br/>title, content, timestamps]
    
    CREATE_NOTE --> SAVE[db.session.add<br/>db.session.commit]
    
    SAVE --> SAVE_OK{Commit<br/>OK?}
    
    SAVE_OK -->|No| ERROR[Log: Failed to create<br/>db.session.rollback]
    SAVE_OK -->|Yes| REFRESH[db.session.refresh]
    
    ERROR --> END1([End - Error])
    
    REFRESH --> VERIFY[Verify note created<br/>in database]
    
    VERIFY --> EXISTS{Note<br/>exists?}
    
    EXISTS -->|No| ERROR2[Log: Note not found]
    EXISTS -->|Yes| HAS_DIR{Has<br/>directory_id?}
    
    ERROR2 --> END2([End - Error])
    
    HAS_DIR -->|Yes| SUCCESS[Log: Note verified]
    HAS_DIR -->|No| WARN2[Log: No directory_id]
    
    SUCCESS --> END3([End - Success])
    WARN2 --> END4([End - Warning])
    
    style START fill:#4CAF50
    style END3 fill:#4CAF50
    style END4 fill:#FF9800
    style END1 fill:#F44336
    style END2 fill:#F44336
    style CREATE_NOTE fill:#2196F3
```

---

## 🔍 IOC Addition to Case Detail

```mermaid
flowchart TD
    START([Receive API data]) --> PARSE[Parse JSON response]
    
    PARSE --> HAS_IOCS{IOCs<br/>dict exists?}
    
    HAS_IOCS -->|No| LOG1[Log: No IOCs found]
    HAS_IOCS -->|Yes| GET_TYPES[Get IOC types from DB]
    
    LOG1 --> END1([End])
    
    GET_TYPES --> CREATE_MAP[Create type mapping:<br/>ip to ip-dst, etc.]
    
    CREATE_MAP --> COUNTER[added_count = 0]
    
    COUNTER --> ITERATE[Iterate IOCs dict]
    
    ITERATE --> LOOP{For each<br/>type}
    
    LOOP --> IS_LIST{Is valid<br/>list?}
    
    IS_LIST -->|No| LOOP
    IS_LIST -->|Yes| MAP_TYPE[Map api_type<br/>to IRIS type]
    
    MAP_TYPE --> TYPE_OK{Type<br/>found?}
    
    TYPE_OK -->|No| LOG2[Log: No suitable type]
    TYPE_OK -->|Yes| GET_TYPE_ID[Get ioc_type_id]
    
    LOG2 --> LOOP
    
    GET_TYPE_ID --> PROCESS_VALUES[Limit to 100 IOCs<br/>per type]
    
    PROCESS_VALUES --> VALUE_LOOP{For each<br/>value}
    
    VALUE_LOOP --> CLEAN[Strip whitespace<br/>validate not empty]
    
    CLEAN --> VALID{Valid?}
    
    VALID -->|No| VALUE_LOOP
    VALID -->|Yes| CHECK_DUP[Check if IOC<br/>already exists]
    
    CHECK_DUP --> EXISTS{Already<br/>exists?}
    
    EXISTS -->|Yes| VALUE_LOOP
    EXISTS -->|No| INSERT_IOC[INSERT INTO ioc]
    
    INSERT_IOC --> GET_ID[Get new ioc_id]
    
    GET_ID --> LINK[INSERT INTO ioc_link]
    
    LINK --> INCREMENT[added_count++]
    
    INCREMENT --> BATCH{Count mod 10<br/>equals 0?}
    
    BATCH -->|Yes| COMMIT1[Commit and<br/>log progress]
    BATCH -->|No| VALUE_LOOP
    
    COMMIT1 --> VALUE_LOOP
    
    VALUE_LOOP --> NEXT_TYPE[Next type]
    NEXT_TYPE --> LOOP
    
    LOOP --> FINAL_COMMIT[Final commit]
    
    FINAL_COMMIT --> HAS_ADDED{Added<br/>any?}
    
    HAS_ADDED -->|Yes| SUCCESS[Log: Added X IOCs]
    HAS_ADDED -->|No| WARN[Log: No new IOCs]
    
    SUCCESS --> END2([End - Success])
    WARN --> END3([End - Warning])
    
    style START fill:#4CAF50
    style END2 fill:#4CAF50
    style END3 fill:#FF9800
    style INSERT_IOC fill:#2196F3
    style LINK fill:#2196F3
```

---

## 🌐 Ransomware.live API Interaction

```mermaid
sequenceDiagram
    participant User as 👤 IRIS User
    participant UI as 🖥️ IRIS Web UI
    participant Module as 🔧 RansomwareLive Module
    participant API as 🌐 Ransomware.live API
    participant DB as 💾 IRIS Database
    
    User->>UI: 1. Create case with<br/>ransomware_group: "Akira"
    UI->>DB: 2. Save case with<br/>custom_attributes
    DB-->>UI: 3. Case saved
    
    UI->>Module: 4. Trigger hook:<br/>on_postload_case_create
    
    Module->>DB: 5. Query: SELECT custom_attributes
    DB-->>Module: 6. Return JSON:<br/>{ransomware_group: "Akira"}
    
    Module->>Module: 7. Normalize:<br/>"Akira" → "Akira"
    
    Note over Module,API: Start parallel requests
    
    par Fetch Group Profile
        Module->>API: 8a. GET /groups/Akira
        API-->>Module: 8b. 200 OK<br/>{group_name, description, TTPs}
        Module->>DB: 8c. INSERT INTO notes
    and Fetch IOCs
        Module->>API: 9a. GET /iocs/Akira
        API-->>Module: 9b. 200 OK<br/>{iocs: {ip: [...], domain: [...]}}
        Module->>DB: 9c. INSERT INTO notes
        loop For each IOC
            Module->>DB: 9d. INSERT INTO ioc<br/>INSERT INTO ioc_link
        end
    and Fetch Ransom Notes
        Module->>API: 10a. GET /ransomnotes/Akira
        API-->>Module: 10b. 200 OK<br/>{ransomnotes: [...]}
        Module->>DB: 10c. INSERT INTO notes
    and Fetch YARA Rules
        Module->>API: 11a. GET /yara/Akira
        API-->>Module: 11b. 200 OK<br/>{yara rules}
        Module->>DB: 11c. INSERT INTO notes
    end
    
    Note over Module: Calculate results
    
    Module-->>UI: 12. Return I2Success
    
    UI-->>User: 13. 🎉 Success message
    
    User->>UI: 14. Navigate to Notes tab
    UI->>DB: 15. SELECT notes
    DB-->>UI: 16. Return 4 notes
    UI-->>User: 17. Display notes
    
    User->>UI: 18. Navigate to IOC tab
    UI->>DB: 19. SELECT iocs
    DB-->>UI: 20. Return 147 IOCs
    UI-->>User: 21. Display IOCs table
```

---

## ⚙️ System Hooks and Triggers

```mermaid
stateDiagram-v2
    [*] --> Waiting: Module Loaded
    
    Waiting --> ManualTrigger: User clicks Processors
    Waiting --> AutoTrigger: Case created/updated
    
    ManualTrigger --> ValidateManual: on_manual_trigger_case
    AutoTrigger --> CheckAutoEnrich: on_postload_case_create<br/>on_postload_case_info_update
    
    CheckAutoEnrich --> ValidateAuto: auto_enrich = true
    CheckAutoEnrich --> Waiting: auto_enrich = false
    
    ValidateManual --> ExtractGroup: Always proceed
    ValidateAuto --> ExtractGroup: Always proceed
    
    ExtractGroup --> GroupFound: ransomware_group exists
    ExtractGroup --> ErrorManual: No group (manual)
    ExtractGroup --> IgnoreAuto: No group (auto)
    
    ErrorManual --> [*]: Return error
    IgnoreAuto --> Waiting: Silent skip
    
    GroupFound --> NormalizeGroup
    NormalizeGroup --> InitSession
    InitSession --> FetchIntelligence
    
    state FetchIntelligence {
        [*] --> ProfileAPI
        ProfileAPI --> IOCsAPI
        IOCsAPI --> NotesAPI
        NotesAPI --> YARAapi
        YARAapi --> [*]
    }
    
    FetchIntelligence --> CreateNotes
    
    state CreateNotes {
        [*] --> CheckDirectory
        CheckDirectory --> CreateNote1: Profile
        CreateNote1 --> CreateNote2: IOCs
        CreateNote2 --> AddIOCs: Add to IOC tab
        AddIOCs --> CreateNote3: Ransom Notes
        CreateNote3 --> CreateNote4: YARA
        CreateNote4 --> [*]
    }
    
    CreateNotes --> CalculateSuccess
    CalculateSuccess --> ReturnSuccess: X/4 successful
    ReturnSuccess --> Waiting: Complete
```

---

## 📊 Data Structure

```mermaid
erDiagram
    CASES ||--o{ NOTES : has
    CASES ||--o{ IOC_LINK : has
    IOC_LINK }o--|| IOC : references
    IOC }o--|| IOC_TYPE : has_type
    NOTES }o--|| NOTE_DIRECTORY : in_directory
    
    CASES {
        int case_id PK
        string case_name
        json custom_attributes
        timestamp created_at
    }
    
    NOTE_DIRECTORY {
        int id PK
        string name
        int case_id FK
        int parent_id
    }
    
    NOTES {
        int note_id PK
        string note_title
        text note_content
        int note_case_id FK
        int directory_id FK
        timestamp note_creationdate
    }
    
    IOC {
        int ioc_id PK
        string ioc_value
        int ioc_type_id FK
        string ioc_description
        string ioc_tags
    }
    
    IOC_LINK {
        int ioc_id FK
        int case_id FK
    }
    
    IOC_TYPE {
        int type_id PK
        string type_name
    }
```

---

## 🎨 Component Architecture

```mermaid
C4Context
    title Architecture - IRIS Ransomware.live Module
    
    Person(analyst, "DFIR Analyst", "Investigates ransomware<br/>incidents")
    
    System_Boundary(iris, "DFIR-IRIS Platform") {
        Container(webapp, "Web Application", "Flask/Python", "User interface")
        Container(worker, "Worker", "Python/Celery", "Process tasks")
        ContainerDb(db, "Database", "PostgreSQL", "Store cases, IOCs, notes")
    }
    
    System_Boundary(module, "Ransomware.live Module") {
        Component(hooks, "Hook Handlers", "Python", "on_manual_trigger_case<br/>on_postload_case_create")
        Component(extractor, "Group Extractor", "Python", "Extract ransomware_group<br/>from custom_attributes")
        Component(enricher, "Intelligence Enricher", "Python", "Coordinate intelligence<br/>gathering")
        Component(api_client, "API Client", "Requests", "HTTP client for<br/>Ransomware.live")
        Component(note_creator, "Note Creator", "Python", "Create formatted<br/>Markdown notes")
        Component(ioc_manager, "IOC Manager", "Python", "Add IOCs to case")
    }
    
    System_Ext(rl_api, "Ransomware.live API", "Threat intelligence REST API")
    
    Rel(analyst, webapp, "Create cases, view intelligence")
    Rel(webapp, worker, "Send tasks")
    Rel(worker, hooks, "Trigger module")
    Rel(hooks, extractor, "Extract group")
    Rel(extractor, db, "Query custom_attributes")
    Rel(hooks, enricher, "Enrich case")
    Rel(enricher, api_client, "Fetch intelligence")
    Rel(api_client, rl_api, "HTTP GET requests")
    Rel(enricher, note_creator, "Create notes")
    Rel(enricher, ioc_manager, "Add IOCs")
    Rel(note_creator, db, "INSERT notes")
    Rel(ioc_manager, db, "INSERT iocs, ioc_links")
```

---

## 📈 Complete Data Flow

```mermaid
graph LR
    subgraph "Input"
        A[Case created<br/>ransomware_group: Akira]
    end
    
    subgraph "Processing"
        B[Extract Group]
        C[Normalize]
        D[API Requests]
        E[Parse Responses]
    end
    
    subgraph "Enrichment"
        F[Group Profile<br/>Description, TTPs]
        G[IOCs<br/>IPs, Domains, Hashes]
        H[Ransom Notes<br/>Samples]
        I[YARA Rules<br/>Detection]
    end
    
    subgraph "Storage"
        J[(Notes Table<br/>4 notes created)]
        K[(IOC Table<br/>147 IOCs added)]
    end
    
    subgraph "Output"
        L[IRIS UI<br/>Notes Tab]
        M[IRIS UI<br/>IOC Tab]
    end
    
    A --> B
    B --> C
    C --> D
    
    D --> F
    D --> G
    D --> H
    D --> I
    
    F --> E
    G --> E
    H --> E
    I --> E
    
    E --> J
    E --> K
    
    J --> L
    K --> M
    
    style A fill:#4CAF50
    style F fill:#2196F3
    style G fill:#2196F3
    style H fill:#2196F3
    style I fill:#2196F3
    style L fill:#FF9800
    style M fill:#FF9800
```

---

## 🔐 API Key Authentication Flow

```mermaid
sequenceDiagram
    participant Module as RansomwareLive Module
    participant Config as Module Config
    participant Session as HTTP Session
    participant API as Ransomware.live API
    
    Module->>Config: 1. Load configuration
    Config-->>Module: 2. Return config dict
    
    alt API Key configured
        Module->>Session: 3a. Create session with<br/>X-API-KEY header
        Module->>API: 4a. GET /groups/Akira<br/>Header: X-API-KEY
        API-->>API: Validate API key
        API-->>Module: 5a. 200 OK (enhanced)<br/>+ Priority rate limits
    else Without API Key
        Module->>Session: 3b. Create session<br/>(no auth header)
        Module->>API: 4b. GET /groups/Akira<br/>(anonymous)
        API-->>Module: 5b. 200 OK (basic)<br/>+ Standard rate limits
    end
    
    Module->>Module: 6. Process response<br/>Create notes and IOCs
```
