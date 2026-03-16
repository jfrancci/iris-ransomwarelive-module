# Fluxogramas - IRIS Ransomware.live Module

## 📊 Visão Geral do Sistema

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

## 🔄 Fluxo Completo de Enriquecimento

```mermaid
flowchart TD
    START([Início]) --> TRIGGER{Tipo de Trigger}
    
    TRIGGER -->|Manual| MANUAL[Usuário clica em<br/>Processors Button]
    TRIGGER -->|Automático| AUTO[Case criado/atualizado<br/>com ransomware_group]
    
    MANUAL --> EXTRACT
    AUTO --> CHECK_AUTO{Auto-enrich<br/>habilitado?}
    
    CHECK_AUTO -->|Não| END1([Fim - Sem ação])
    CHECK_AUTO -->|Sim| EXTRACT
    
    EXTRACT[Extrair ransomware_group<br/>do custom_attribute]
    
    EXTRACT --> HAS_GROUP{Grupo<br/>encontrado?}
    
    HAS_GROUP -->|Não - Manual| ERROR1[Retorna erro:<br/>Campo vazio]
    HAS_GROUP -->|Não - Auto| END2([Fim - Ignorado])
    HAS_GROUP -->|Sim| NORMALIZE
    
    ERROR1 --> END3([Fim])
    
    NORMALIZE[Normalizar nome do grupo<br/>Ex: Cl0p → Clop]
    
    NORMALIZE --> INIT_SESSION[Inicializar sessão HTTP<br/>+ API Key se disponível]
    
    INIT_SESSION --> FETCH_PROFILE
    
    subgraph "Buscar Inteligência"
        FETCH_PROFILE[GET /groups/grupo]
        FETCH_PROFILE --> PROFILE_OK{Status 200?}
        
        PROFILE_OK -->|Sim| CREATE_NOTE1[Criar nota:<br/>Group Profile]
        PROFILE_OK -->|404| LOG1[Log: Grupo não encontrado]
        PROFILE_OK -->|Erro| LOG2[Log: Erro API]
        
        CREATE_NOTE1 --> FETCH_IOCS
        LOG1 --> FETCH_IOCS
        LOG2 --> FETCH_IOCS
        
        FETCH_IOCS[GET /iocs/grupo]
        FETCH_IOCS --> IOCS_OK{Status 200?}
        
        IOCS_OK -->|Sim| CREATE_NOTE2[Criar nota: IOCs]
        IOCS_OK -->|404/Erro| FETCH_NOTES
        
        CREATE_NOTE2 --> ADD_IOCS[Adicionar IOCs à aba IOC<br/>147+ indicadores]
        ADD_IOCS --> FETCH_NOTES
        
        FETCH_NOTES[GET /ransomnotes/grupo]
        FETCH_NOTES --> NOTES_OK{Status 200?}
        
        NOTES_OK -->|Sim| CREATE_NOTE3[Criar nota:<br/>Ransom Notes]
        NOTES_OK -->|404/Erro| FETCH_YARA
        
        CREATE_NOTE3 --> FETCH_YARA
        
        FETCH_YARA[GET /yara/grupo]
        FETCH_YARA --> YARA_OK{Status 200?}
        
        YARA_OK -->|Sim| CREATE_NOTE4[Criar nota:<br/>YARA Rules]
        YARA_OK -->|404/Erro| CALCULATE
        
        CREATE_NOTE4 --> CALCULATE
    end
    
    CALCULATE[Calcular sucesso:<br/>X/4 endpoints]
    
    CALCULATE --> SUCCESS{Algum<br/>sucesso?}
    
    SUCCESS -->|Sim| RETURN_SUCCESS[Retornar I2Success<br/>com mensagem]
    SUCCESS -->|Não| RETURN_ERROR[Retornar I2Success<br/>com avisos]
    
    RETURN_SUCCESS --> LOG_FINAL[Log: Enrichment complete]
    RETURN_ERROR --> LOG_FINAL
    
    LOG_FINAL --> END([Fim])
    
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

## 🎯 Detalhamento: Extração do Grupo Ransomware

```mermaid
flowchart TD
    START([Receber Case Object]) --> GET_ID[Extrair case_id]
    
    GET_ID --> HAS_ID{case_id<br/>válido?}
    
    HAS_ID -->|Não| ERROR1[Log: No case_id found<br/>Return None]
    HAS_ID -->|Sim| QUERY_DB
    
    ERROR1 --> END1([Fim])
    
    QUERY_DB[SQL Query:<br/>SELECT custom_attributes<br/>FROM cases<br/>WHERE case_id = X]
    
    QUERY_DB --> HAS_ATTRS{custom_attributes<br/>existe?}
    
    HAS_ATTRS -->|Não| LOG1[Log: No custom_attributes<br/>Return None]
    HAS_ATTRS -->|Sim| CHECK_TYPE
    
    LOG1 --> END2([Fim])
    
    CHECK_TYPE{Tipo é<br/>string?}
    
    CHECK_TYPE -->|Sim| PARSE_JSON[json.loads<br/>custom_attributes]
    CHECK_TYPE -->|Não| CHECK_DICT
    
    PARSE_JSON --> PARSE_OK{Parse<br/>OK?}
    
    PARSE_OK -->|Não| ERROR2[Log: Failed to parse JSON<br/>Return None]
    PARSE_OK -->|Sim| CHECK_DICT
    
    ERROR2 --> END3([Fim])
    
    CHECK_DICT{É um<br/>dict?}
    
    CHECK_DICT -->|Não| ERROR3[Log: Not a dict<br/>Return None]
    CHECK_DICT -->|Sim| ITERATE
    
    ERROR3 --> END4([Fim])
    
    ITERATE[Iterar sobre keys<br/>do dict]
    
    ITERATE --> LOOP{Para cada<br/>group_name,<br/>group_data}
    
    LOOP --> HAS_FIELD{Existe<br/>ransomware_group<br/>em group_data?}
    
    HAS_FIELD -->|Não| LOOP
    HAS_FIELD -->|Sim| GET_VALUE
    
    GET_VALUE[field_data =<br/>group_data['ransomware_group']]
    
    GET_VALUE --> IS_DICT{field_data<br/>é dict?}
    
    IS_DICT -->|Não| LOOP
    IS_DICT -->|Sim| HAS_VALUE
    
    HAS_VALUE{Existe<br/>'value'?}
    
    HAS_VALUE -->|Não| LOOP
    HAS_VALUE -->|Sim| EXTRACT
    
    EXTRACT[group = field_data['value']<br/>strip whitespace]
    
    EXTRACT --> IS_EMPTY{group<br/>vazio?}
    
    IS_EMPTY -->|Sim| LOG2[Log: Empty value<br/>Return None]
    IS_EMPTY -->|Não| SUCCESS
    
    LOG2 --> END5([Fim])
    
    SUCCESS[Log: Group found: Akira<br/>Return group]
    
    SUCCESS --> END6([Fim - Sucesso])
    
    LOOP --> NOT_FOUND[Log: Field not found<br/>Return None]
    NOT_FOUND --> END7([Fim])
    
    style START fill:#4CAF50
    style END6 fill:#4CAF50
    style SUCCESS fill:#4CAF50
    style ERROR1 fill:#F44336
    style ERROR2 fill:#F44336
    style ERROR3 fill:#F44336
```

---

## 📝 Detalhamento: Criação de Notas

```mermaid
flowchart TD
    START([Criar Nota]) --> GET_DIR{Diretório<br/>Ransomware details<br/>existe?}
    
    GET_DIR -->|Sim| USE_DIR[Usar directory_id<br/>existente]
    GET_DIR -->|Não| CREATE_DIR
    
    CREATE_DIR[SQL INSERT:<br/>INSERT INTO note_directory<br/>name='Ransomware details']
    
    CREATE_DIR --> DIR_OK{Criação<br/>OK?}
    
    DIR_OK -->|Sim| GET_NEW_ID[Obter novo<br/>directory_id]
    DIR_OK -->|Não| FALLBACK
    
    GET_NEW_ID --> USE_DIR
    
    FALLBACK[Buscar qualquer<br/>diretório do case]
    
    FALLBACK --> FOUND{Encontrou?}
    
    FOUND -->|Sim| USE_FALLBACK[Usar directory_id<br/>encontrado]
    FOUND -->|Não| WARN
    
    USE_FALLBACK --> USE_DIR
    
    WARN[Log: WARNING<br/>Nota sem diretório]
    
    WARN --> CREATE_NOTE
    USE_DIR --> CREATE_NOTE
    
    CREATE_NOTE[Criar objeto Note:<br/>- title<br/>- content Markdown<br/>- case_id<br/>- directory_id<br/>- timestamps]
    
    CREATE_NOTE --> SAVE[db.session.add<br/>db.session.commit]
    
    SAVE --> SAVE_OK{Commit<br/>OK?}
    
    SAVE_OK -->|Não| ERROR[Log: Failed to create<br/>db.session.rollback<br/>Return False]
    SAVE_OK -->|Sim| REFRESH
    
    ERROR --> END1([Fim - Erro])
    
    REFRESH[db.session.refresh<br/>para obter note_id]
    
    REFRESH --> VERIFY[Verificar nota criada:<br/>SELECT * FROM notes<br/>WHERE note_id = X]
    
    VERIFY --> EXISTS{Nota<br/>existe?}
    
    EXISTS -->|Não| ERROR2[Log: Note not found<br/>Return False]
    EXISTS -->|Sim| HAS_DIR
    
    ERROR2 --> END2([Fim - Erro])
    
    HAS_DIR{Tem<br/>directory_id?}
    
    HAS_DIR -->|Sim| SUCCESS[Log: Note verified<br/>Return True]
    HAS_DIR -->|Não| WARN2[Log: No directory_id<br/>Return True]
    
    SUCCESS --> END3([Fim - Sucesso])
    WARN2 --> END4([Fim - Aviso])
    
    style START fill:#4CAF50
    style END3 fill:#4CAF50
    style END4 fill:#FF9800
    style END1 fill:#F44336
    style END2 fill:#F44336
    style CREATE_NOTE fill:#2196F3
```

---

## 🔍 Detalhamento: Adição de IOCs ao Case

```mermaid
flowchart TD
    START([Receber dados da API]) --> PARSE[Parse JSON response<br/>iocs_data]
    
    PARSE --> HAS_IOCS{Existe<br/>iocs dict?}
    
    HAS_IOCS -->|Não| LOG1[Log: No iocs found<br/>Return 0]
    HAS_IOCS -->|Sim| GET_TYPES
    
    LOG1 --> END1([Fim])
    
    GET_TYPES[Obter tipos IOC do DB:<br/>SELECT type_id, type_name<br/>FROM ioc_type]
    
    GET_TYPES --> CREATE_MAP[Criar mapeamento:<br/>ip → ip-dst<br/>domain → domain<br/>sha256 → sha256<br/>etc.]
    
    CREATE_MAP --> COUNTER[added_count = 0]
    
    COUNTER --> ITERATE[Iterar sobre<br/>iocs_dict items]
    
    ITERATE --> LOOP{Para cada<br/>api_type,<br/>values}
    
    LOOP --> IS_LIST{values é<br/>lista válida?}
    
    IS_LIST -->|Não| LOOP
    IS_LIST -->|Sim| MAP_TYPE
    
    MAP_TYPE[Mapear api_type<br/>para IRIS type]
    
    MAP_TYPE --> TYPE_OK{Tipo<br/>encontrado?}
    
    TYPE_OK -->|Não| LOG2[Log: No suitable type<br/>Continue]
    TYPE_OK -->|Sim| GET_TYPE_ID
    
    LOG2 --> LOOP
    
    GET_TYPE_ID[Obter ioc_type_id<br/>do cache]
    
    GET_TYPE_ID --> PROCESS_VALUES[Limitar a 100 IOCs<br/>por tipo]
    
    PROCESS_VALUES --> VALUE_LOOP{Para cada<br/>value}
    
    VALUE_LOOP --> CLEAN[strip whitespace<br/>validar não vazio]
    
    CLEAN --> VALID{Válido?}
    
    VALID -->|Não| VALUE_LOOP
    VALID -->|Sim| CHECK_DUP
    
    CHECK_DUP[SQL Query:<br/>SELECT ioc_id<br/>FROM ioc i<br/>JOIN ioc_link il<br/>WHERE value = X<br/>AND case_id = Y]
    
    CHECK_DUP --> EXISTS{IOC já<br/>existe?}
    
    EXISTS -->|Sim| VALUE_LOOP
    EXISTS -->|Não| INSERT_IOC
    
    INSERT_IOC[SQL INSERT:<br/>INSERT INTO ioc<br/>values, type_id,<br/>description, tags]
    
    INSERT_IOC --> GET_ID[RETURNING ioc_id]
    
    GET_ID --> LINK[SQL INSERT:<br/>INSERT INTO ioc_link<br/>ioc_id, case_id]
    
    LINK --> INCREMENT[added_count++]
    
    INCREMENT --> BATCH{Count % 10<br/>== 0?}
    
    BATCH -->|Sim| COMMIT1[db.session.commit<br/>Log progress]
    BATCH -->|Não| VALUE_LOOP
    
    COMMIT1 --> VALUE_LOOP
    
    VALUE_LOOP --> NEXT_TYPE[Próximo tipo]
    NEXT_TYPE --> LOOP
    
    LOOP --> FINAL_COMMIT[db.session.commit<br/>final]
    
    FINAL_COMMIT --> HAS_ADDED{added_count<br/>> 0?}
    
    HAS_ADDED -->|Sim| SUCCESS[Log: Added X IOCs<br/>Return count]
    HAS_ADDED -->|Não| WARN[Log: No new IOCs<br/>Return 0]
    
    SUCCESS --> END2([Fim - Sucesso])
    WARN --> END3([Fim - Aviso])
    
    style START fill:#4CAF50
    style END2 fill:#4CAF50
    style END3 fill:#FF9800
    style INSERT_IOC fill:#2196F3
    style LINK fill:#2196F3
```

---

## 🌐 Interação com Ransomware.live API

```mermaid
sequenceDiagram
    participant User as 👤 Usuário IRIS
    participant UI as 🖥️ IRIS Web UI
    participant Module as 🔧 RansomwareLive Module
    participant API as 🌐 Ransomware.live API
    participant DB as 💾 IRIS Database
    
    User->>UI: 1. Cria caso com<br/>ransomware_group: "Akira"
    UI->>DB: 2. Salva caso com<br/>custom_attributes
    DB-->>UI: 3. Case saved
    
    UI->>Module: 4. Trigger hook:<br/>on_postload_case_create
    
    Module->>DB: 5. Query: SELECT custom_attributes<br/>FROM cases WHERE case_id = X
    DB-->>Module: 6. Return JSON:<br/>{ransomware_group: "Akira"}
    
    Module->>Module: 7. Normalizar:<br/>"Akira" → "Akira"
    
    Note over Module,API: Iniciar requests paralelos
    
    par Buscar Group Profile
        Module->>API: 8a. GET /groups/Akira<br/>Header: X-API-KEY (se disponível)
        API-->>Module: 8b. 200 OK<br/>{group_name, description,<br/>victims, TTPs, locations}
        Module->>DB: 8c. INSERT INTO notes<br/>(title, content, directory_id)
    and Buscar IOCs
        Module->>API: 9a. GET /iocs/Akira
        API-->>Module: 9b. 200 OK<br/>{iocs: {ip: [...], domain: [...]}}
        Module->>DB: 9c. INSERT INTO notes (IOCs list)
        loop Para cada IOC
            Module->>DB: 9d. INSERT INTO ioc<br/>INSERT INTO ioc_link
        end
    and Buscar Ransom Notes
        Module->>API: 10a. GET /ransomnotes/Akira
        API-->>Module: 10b. 200 OK<br/>{ransomnotes: [...]}
        Module->>DB: 10c. INSERT INTO notes<br/>(ransom samples)
    and Buscar YARA Rules
        Module->>API: 11a. GET /yara/Akira
        API-->>Module: 11b. 200 OK<br/>{yara rules}
        Module->>DB: 11c. INSERT INTO notes<br/>(YARA detection rules)
    end
    
    Note over Module: Calcular resultados
    
    Module-->>UI: 12. Return I2Success:<br/>"Enriched with Akira intelligence"
    
    UI-->>User: 13. 🎉 Show success message
    
    User->>UI: 14. Navigate to Notes tab
    UI->>DB: 15. SELECT * FROM notes<br/>WHERE case_id = X
    DB-->>UI: 16. Return 4 notes
    UI-->>User: 17. Display:<br/>📄 Group Profile<br/>🔍 IOCs<br/>📝 Ransom Notes<br/>🛡️ YARA Rules
    
    User->>UI: 18. Navigate to IOC tab
    UI->>DB: 19. SELECT * FROM ioc<br/>JOIN ioc_link
    DB-->>UI: 20. Return 147 IOCs
    UI-->>User: 21. Display IOCs table
```

---

## ⚙️ Hooks e Triggers do Sistema

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
    
    note right of FetchIntelligence
        Parallel API calls:
        - GET /groups/{group}
        - GET /iocs/{group}
        - GET /ransomnotes/{group}
        - GET /yara/{group}
    end note
    
    note right of CreateNotes
        All notes created in:
        "Ransomware details" directory
        
        IOCs also added to:
        IOC tab of the case
    end note
```

---

## 📊 Estrutura de Dados

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

## 🎨 Arquitetura de Componentes

```mermaid
C4Context
    title Arquitetura - IRIS Ransomware.live Module
    
    Person(analyst, "Analista DFIR", "Investiga incidentes<br/>de ransomware")
    
    System_Boundary(iris, "DFIR-IRIS Platform") {
        Container(webapp, "Web Application", "Flask/Python", "Interface do usuário")
        Container(worker, "Worker", "Python/Celery", "Processa tarefas")
        ContainerDb(db, "Database", "PostgreSQL", "Armazena casos, IOCs, notas")
    }
    
    System_Boundary(module, "Ransomware.live Module") {
        Component(hooks, "Hook Handlers", "Python", "on_manual_trigger_case<br/>on_postload_case_create<br/>on_postload_case_info_update")
        Component(extractor, "Group Extractor", "Python", "Extrai ransomware_group<br/>de custom_attributes")
        Component(enricher, "Intelligence Enricher", "Python", "Coordena busca de<br/>inteligência")
        Component(api_client, "API Client", "Requests", "Cliente HTTP para<br/>Ransomware.live")
        Component(note_creator, "Note Creator", "Python", "Cria notas formatadas<br/>em Markdown")
        Component(ioc_manager, "IOC Manager", "Python", "Adiciona IOCs ao case")
    }
    
    System_Ext(rl_api, "Ransomware.live API", "API REST de threat intelligence")
    
    Rel(analyst, webapp, "Cria casos, visualiza intelligence")
    Rel(webapp, worker, "Envia tarefas")
    Rel(worker, hooks, "Triggers módulo")
    Rel(hooks, extractor, "Extrai grupo")
    Rel(extractor, db, "Query custom_attributes")
    Rel(hooks, enricher, "Enriquece caso")
    Rel(enricher, api_client, "Busca intelligence")
    Rel(api_client, rl_api, "HTTP GET requests")
    Rel(enricher, note_creator, "Cria notas")
    Rel(enricher, ioc_manager, "Adiciona IOCs")
    Rel(note_creator, db, "INSERT notes")
    Rel(ioc_manager, db, "INSERT iocs, ioc_links")
    
    UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="2")
```

---

## 📈 Fluxo de Dados Completo

```mermaid
graph LR
    subgraph "Input"
        A[Caso criado<br/>ransomware_group: Akira]
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

## 🔐 Fluxo de Autenticação com API Key

```mermaid
sequenceDiagram
    participant Module as RansomwareLive Module
    participant Config as Module Config
    participant Session as HTTP Session
    participant API as Ransomware.live API
    
    Module->>Config: 1. Load configuration
    Config-->>Module: 2. Return config dict<br/>{api_key: "xxx", timeout: 30}
    
    alt API Key configurada
        Module->>Session: 3a. Create session with header<br/>X-API-KEY: "xxx"
        Module->>API: 4a. GET /groups/Akira<br/>Header: X-API-KEY
        API-->>API: Validate API key
        API-->>Module: 5a. 200 OK (enhanced access)<br/>+ Priority rate limits
    else Sem API Key
        Module->>Session: 3b. Create session<br/>(no auth header)
        Module->>API: 4b. GET /groups/Akira<br/>(anonymous)
        API-->>Module: 5b. 200 OK (basic access)<br/>+ Standard rate limits
    end
    
    Module->>Module: 6. Process response<br/>Create notes & IOCs
```

