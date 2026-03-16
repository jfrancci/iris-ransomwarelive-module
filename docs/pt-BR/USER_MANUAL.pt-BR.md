# 📘 Manual do Usuário - IRIS Ransomware.live Module

**Versão:** 3.3.1  
**Data:** Janeiro 2025  
**Autor:** DFIR Team  

---

## 📑 Índice

1. [Introdução](#introdução)
2. [Pré-requisitos](#pré-requisitos)
3. [Instalação Passo a Passo](#instalação-passo-a-passo)
4. [Configuração Inicial](#configuração-inicial)
5. [Primeiro Uso](#primeiro-uso)
6. [Uso Avançado](#uso-avançado)
7. [Troubleshooting](#troubleshooting)
8. [FAQ - Perguntas Frequentes](#faq---perguntas-frequentes)
9. [Glossário](#glossário)

---

## 🎯 Introdução

### O que é o IRIS Ransomware.live Module?

O **IRIS Ransomware.live Module** é uma extensão para a plataforma DFIR-IRIS que automatiza o enriquecimento de casos de ransomware com inteligência de ameaças atualizada.

### O que o módulo faz?

Quando você investiga um incidente de ransomware:

1. ✅ **Identifica automaticamente** o grupo responsável
2. 📊 **Busca inteligência** atualizada da API Ransomware.live
3. 📝 **Cria notas** com informações detalhadas do grupo
4. 🔍 **Adiciona IOCs** (IPs, domínios, hashes) ao caso
5. 🛡️ **Fornece regras YARA** para detecção
6. 📄 **Disponibiliza amostras** de notas de resgate

### Por que usar?

- ⏱️ **Economiza tempo** - Automação completa
- 📈 **Informação atualizada** - API em tempo real
- 🎯 **Mais preciso** - 147+ IOCs por grupo
- 🤝 **Integrado ao IRIS** - Sem ferramentas externas

---

## 🔧 Pré-requisitos

### Requisitos do Sistema

| Item | Requisito | Verificar |
|------|-----------|-----------|
| **DFIR-IRIS** | v2.4.22 ou superior | `docker exec iriswebapp_app cat /iriswebapp/version.txt` |
| **Sistema Operacional** | Ubuntu 22.04 ou 24.04 LTS | `lsb_release -a` |
| **Python** | 3.8+ (no host) | `python3 --version` |
| **Docker** | 20.10+ | `docker --version` |
| **Docker Compose** | 2.0+ | `docker compose version` |
| **Internet** | Acesso à API Ransomware.live | `curl -I https://api-pro.ransomware.live` |

### Verificação Rápida

Execute este script para verificar todos os requisitos:

```bash
#!/bin/bash
echo "=== Verificação de Pré-requisitos ==="
echo ""

# IRIS
if docker ps | grep -q iriswebapp; then
    echo "✅ IRIS está rodando"
    VERSION=$(docker exec iriswebapp_app cat /iriswebapp/version.txt 2>/dev/null || echo "Não detectado")
    echo "   Versão: $VERSION"
else
    echo "❌ IRIS não está rodando"
fi

# Ubuntu
echo ""
echo "Sistema Operacional:"
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
    echo "✅ Acesso à API Ransomware.live OK"
else
    echo "❌ Sem acesso à API Ransomware.live"
fi

echo ""
echo "=== Verificação Concluída ==="
```

---

## 📦 Instalação Passo a Passo

### Método 1: Instalação Automática (Recomendado)

Este é o método mais fácil e rápido.

#### Passo 1: Download do Módulo

```bash
# Navegue até o diretório do IRIS
cd /opt/iris-web

# Clone o repositório do módulo
git clone https://github.com/SEU-USUARIO/iris-ransomwarelive-module.git iris-web_ransomwarelive

# Entre no diretório
cd iris-web_ransomwarelive
```

**💡 Dica:** Se você não tem `git`, instale com:
```bash
sudo apt-get update
sudo apt-get install -y git
```

#### Passo 2: Executar Script de Instalação

```bash
# Dar permissão de execução ao script
chmod +x buildnpush2iris.sh

# Executar instalação completa
./buildnpush2iris.sh -ar
```

**O que significam as flags?**
- `-a` = Instala em **app** E **worker** containers (necessário!)
- `-r` = **Restart** automático dos serviços após instalação

**⏱️ Tempo estimado:** 2-5 minutos

#### Passo 3: Verificar Instalação

```bash
# Verificar no worker
docker exec iriswebapp_worker /opt/venv/bin/pip show iris_ransomwarelive

# Verificar no app
docker exec iriswebapp_app /opt/venv/bin/pip show iris_ransomwarelive

# Deve mostrar:
# Name: iris_ransomwarelive
# Version: 3.3.1
# ...
```

✅ **Se viu as informações acima, a instalação foi bem-sucedida!**

---

### Método 2: Instalação Manual

Use este método se o script automático falhar.

#### Passo 1: Preparar Ambiente

```bash
# Instalar dependências do sistema (Ubuntu 24.04)
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-build python3.12-venv

# Ubuntu 22.04
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv python3-build
```

#### Passo 2: Baixar o Módulo

```bash
cd /opt/iris-web
git clone https://github.com/SEU-USUARIO/iris-ransomwarelive-module.git iris-web_ransomwarelive
cd iris-web_ransomwarelive
```

#### Passo 3: Construir o Pacote

```bash
# Limpar builds anteriores
rm -rf build/ dist/ *.egg-info

# Construir wheel
python3 -m build --wheel --outdir dist

# Verificar se foi criado
ls -lh dist/*.whl
```

#### Passo 4: Instalar no Worker

```bash
# Copiar para o container
docker cp dist/*.whl iriswebapp_worker:/tmp/

# Instalar
docker exec iriswebapp_worker /opt/venv/bin/pip install /tmp/*.whl

# Limpar
docker exec iriswebapp_worker rm /tmp/*.whl
```

#### Passo 5: Instalar no App

```bash
# Copiar para o container
docker cp dist/*.whl iriswebapp_app:/tmp/

# Instalar
docker exec iriswebapp_app /opt/venv/bin/pip install /tmp/*.whl

# Limpar
docker exec iriswebapp_app rm /tmp/*.whl
```

#### Passo 6: Reiniciar Serviços

```bash
cd /opt/iris-web
docker compose restart app worker

# Aguardar serviços subirem
sleep 30
```

---

## ⚙️ Configuração Inicial

### Passo 1: Habilitar o Módulo na Interface

1. **Faça login no IRIS**
   - URL: `https://seu-servidor-iris:8443`
   - Usuário: `administrator`
   - Senha: sua senha

2. **Navegue até Módulos**
   ```
   Menu superior → Advanced → Modules
   ```

3. **Localize o módulo**
   - Procure por: **"Ransomware.live Enrichment"**
   - Status deve estar: **Not enabled**

4. **Habilite o módulo**
   - Clique no botão **"Enable"**
   - Aguarde confirmação
   - Status muda para: **Enabled**

**📸 Screenshot:** [Inserir imagem da tela de módulos]

---

### Passo 2: Configurar Parâmetros do Módulo

1. **Abrir configuração**
   - Na linha do módulo "Ransomware.live Enrichment"
   - Clique no ícone de **engrenagem** ⚙️
   - Ou clique em **"Configure"**

2. **Configurar parâmetros:**

| Parâmetro | Valor Recomendado | Descrição |
|-----------|-------------------|-----------|
| **API URL** | `https://api-pro.ransomware.live` | URL da API (não alterar) |
| **API Key** | *(vazio inicialmente)* | Chave API (opcional) |
| **Request Timeout** | `30` | Timeout em segundos |
| **Auto Enrichment** | `✓ Habilitado` | Enriquecimento automático |

3. **Salvar configuração**
   - Clique em **"Save"** ou **"Update"**

**🔑 Sobre API Key:**
- **Não obrigatório** para funcionamento básico
- **Recomendado** para uso intensivo
- Solicite em: https://ransomware.live

---

### Passo 3: Criar Custom Attribute

Este é o campo que o módulo usa para identificar o grupo de ransomware.

1. **Navegue até Custom Attributes**
   ```
   Menu superior → Advanced → Custom Attributes
   ```

2. **Selecione a aba "Cases"**
   - Clique na aba **"Cases"**

3. **Adicione o atributo**
   - No campo de texto JSON, cole:

```json
{
    "Ransomware Group": {
        "ransomware_group": {
            "type": "input_string",
            "label": "Ransomware group",
            "description": "Nome do grupo de ransomware (ex.: Akira, LockBit, BlackBasta)",
            "mandatory": false,
            "value": ""
        }
    }
}
```

4. **Salvar**
   - Clique em **"Save"** ou **"Update"**

**📸 Screenshot:** [Inserir imagem dos custom attributes]

**⚠️ Importante:**
- O nome do campo **DEVE** ser exatamente: `ransomware_group`
- Maiúsculas/minúsculas importam!
- Se errar, o módulo não funcionará

---

### Passo 4: Verificar Instalação Completa

Execute este checklist:

```bash
# ✅ Módulo instalado no worker
docker exec iriswebapp_worker /opt/venv/bin/pip show iris_ransomwarelive

# ✅ Módulo instalado no app  
docker exec iriswebapp_app /opt/venv/bin/pip show iris_ransomwarelive

# ✅ Módulo aparece na UI
# Acesse: Advanced → Modules → Procure "Ransomware.live"

# ✅ Módulo está habilitado
# Status deve ser: "Enabled"

# ✅ Custom attribute criado
# Acesse: Advanced → Custom Attributes → Aba Cases

# ✅ Sem erros nos logs
docker logs iriswebapp_worker --tail 50 | grep '\[RL\]'
```

✅ **Se todos os itens acima estão OK, você está pronto para usar!**

---

## 🚀 Primeiro Uso

### Cenário: Investigando Incidente de Ransomware Akira

Vamos criar um caso de teste para ver o módulo em ação.

#### Passo 1: Criar um Novo Caso

1. **Acesse o IRIS**
   - Faça login em: `https://seu-servidor-iris:8443`

2. **Crie um novo caso**
   ```
   Menu lateral → Case → Botão "+ New Case"
   ```

3. **Preencha os dados básicos:**
   - **Case Name:** `#001 - Teste Ransomware Akira`
   - **Description:** `Teste de enriquecimento automático`
   - **Customer:** `MESI` (ou seu cliente)
   - **Classification:** `malicious-code:ransomware`
   - **Severity:** `High`
   - **Status:** `Open`

4. **Salve o caso**
   - Clique em **"Add case"**

**📸 Screenshot:** [Inserir imagem da criação de caso]

---

#### Passo 2: Preencher Campo Ransomware Group

Agora vamos ativar o módulo preenchendo o campo especial.

1. **Abra o caso criado**
   - Clique no caso #001 na lista

2. **Vá para a aba Summary**
   - Já deve estar selecionada por padrão

3. **Edite o caso**
   - Clique no botão **"Edit"** (canto superior direito)

4. **Role até encontrar "Ransomware Group"**
   - Está na seção de Custom Attributes
   - Campo: **"Ransomware group"**

5. **Preencha com:** `Akira`
   - Digite exatamente: `Akira`
   - Ou experimente: `LockBit`, `BlackBasta`, `ALPHV`

6. **Salve**
   - Clique em **"Update"**

**🎉 Momento mágico:**
- O módulo detecta automaticamente o campo preenchido
- Inicia enriquecimento em background
- Em 5-10 segundos, a inteligência estará disponível

---

#### Passo 3: Visualizar Inteligência - Notas

1. **Clique na aba "Notes"**
   - Menu superior do caso: `Notes`

2. **Expanda o diretório "Ransomware details"**
   - Clique na pasta 📁 "Ransomware details"

3. **Veja as 4 notas criadas:**

   **📄 Ransomware.live: AKIRA Profile**
   - Descrição do grupo
   - Estatísticas de vítimas
   - Data de primeira/última atividade
   - MITRE ATT&CK TTPs
   - Sites da dark web (status online/offline)

   **🔍 Ransomware.live: AKIRA IOCs**
   - Lista de indicadores de comprometimento
   - IPs, domínios, hashes, e-mails, carteiras crypto

   **📝 Ransomware.live: AKIRA Ransom Notes**
   - Amostras de notas de resgate
   - Padrões comuns
   - Métodos de contato

   **🛡️ Ransomware.live: AKIRA YARA Rules**
   - Regras YARA para detecção
   - Assinaturas do ransomware

**📸 Screenshot:** [Inserir imagem das notas]

---

#### Passo 4: Visualizar IOCs Adicionados

1. **Clique na aba "IOC"**
   - Menu superior do caso: `IOC`

2. **Veja os IOCs automaticamente adicionados:**
   - **147+ indicadores** foram adicionados!
   - Tipos: `ip-dst`, `domain`, `sha256`, `btc`, `email`, etc.
   - Tags: `ransomware`, `akira`, `ransomware-live`

3. **Explore os IOCs:**
   - Clique em qualquer IOC para ver detalhes
   - Use os filtros para buscar tipos específicos
   - Exporte para usar em firewalls, SIEM, etc.

**💡 Dica:** Você pode usar esses IOCs imediatamente para:
- Bloquear IPs/domínios no firewall
- Criar alertas no SIEM
- Fazer threat hunting na rede
- Compartilhar com ISACs/CERTs

**📸 Screenshot:** [Inserir imagem da aba IOC]

---

#### Passo 5: Verificar Logs (Opcional)

Para ver o que aconteceu nos bastidores:

```bash
# Ver logs do módulo
docker logs iriswebapp_worker --tail 100 | grep '\[RL\]'

# Você verá algo como:
# [RL] Enriching case 1 (automatic) with group: Akira
# [RL] Normalized group name: Akira
# [RL] Fetching group profile: https://api-pro.ransomware.live/groups/Akira
# [RL] ✓ Group profile note created successfully
# [RL] ✓✓✓ Successfully added 147 IOCs to case
# [RL] Enrichment complete: 4/4 successful
```

**✅ Parabéns! Você completou seu primeiro enriquecimento automático!**

---

## 🎓 Uso Avançado

### Enriquecimento Manual

Às vezes você quer re-enriquecer um caso (ex: nova inteligência disponível).

#### Como fazer:

1. **Abra o caso**
   - Navegue até o caso desejado

2. **Clique em "Processors"**
   - Botão localizado na barra superior do caso
   - Ao lado de "Manage", "Pipelines"

3. **Selecione o módulo**
   - Procure: `iris_ransomwarelive::on_manual_trigger_case`
   - Clique para selecionar

4. **Execute**
   - Clique no botão **"Run"**
   - Aguarde processamento (5-10 segundos)

5. **Veja o resultado**
   - Mensagem de sucesso/erro aparecerá
   - Novas informações serão adicionadas

**💡 Quando usar enriquecimento manual?**
- Atualizar inteligência antiga
- Forçar re-enriquecimento após erro
- Testar o módulo
- Quando auto-enrich está desabilitado

---

### Usando API Key para Acesso Premium

Se você tem uma API key da Ransomware.live:

#### Passo 1: Obter API Key

1. Visite: https://ransomware.live
2. Contate os administradores
3. Solicite uma API key

#### Passo 2: Configurar no IRIS

1. **Navegue até módulos**
   ```
   Advanced → Modules → Ransomware.live Enrichment
   ```

2. **Clique em Configure** ⚙️

3. **Preencha API Key**
   - Campo: **API Key**
   - Cole sua chave: `rl_1234567890abcdef...`

4. **Salve**

#### Passo 3: Verificar

```bash
# Logs devem mostrar:
docker logs iriswebapp_worker --tail 50 | grep '\[RL\]'

# Procure por:
# [RL] API-KEY configured for requests
```

**🎁 Benefícios da API Key:**
- ⚡ Rate limits mais altos
- 🚀 Prioridade nas requisições
- 📊 Acesso a endpoints premium (futuros)
- 🎯 Dados mais completos

---

### Trabalhando com Múltiplos Casos

#### Cenário: Campanha de Ransomware

Imagine que você tem 5 casos da mesma campanha:

1. **Crie os 5 casos**
   - #001, #002, #003, #004, #005

2. **Em cada caso, preencha:**
   - Campo "Ransomware group": `LockBit`

3. **Resultado:**
   - Todos os 5 casos são enriquecidos automaticamente
   - Mesma inteligência em todos
   - Fácil correlação entre casos

**💡 Dica de Workflow:**
```
1. Criar caso → 2. Preencher grupo → 3. Enriquecimento automático →
4. Análise das notas → 5. Uso dos IOCs → 6. Contenção
```

---

### Grupos Ransomware Suportados

O módulo suporta 100+ grupos. Aqui estão os principais:

| Grupo | Aliases Aceitos | Exemplo de Uso |
|-------|----------------|----------------|
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

**Lista completa:** https://ransomware.live/#/group

**💡 Normalização Automática:**
- `lockbit3` → `Lockbit`
- `Cl0p` → `Clop`
- `ALPHV` → `Alphv`

---

### Integrando com MISP

Você pode exportar os IOCs para MISP (Malware Information Sharing Platform).

#### Script de Exemplo:

```python
#!/usr/bin/env python3
"""
Exportar IOCs do IRIS para MISP
"""

import requests
from pymisp import PyMISP

# Configuração IRIS
IRIS_URL = "https://seu-iris.com"
IRIS_TOKEN = "seu-token-iris"
CASE_ID = 1

# Configuração MISP
MISP_URL = "https://seu-misp.com"
MISP_KEY = "sua-chave-misp"

# Conectar ao MISP
misp = PyMISP(MISP_URL, MISP_KEY)

# Buscar IOCs do IRIS
response = requests.get(
    f"{IRIS_URL}/api/case/{CASE_ID}/iocs",
    headers={"Authorization": f"Bearer {IRIS_TOKEN}"}
)

iocs = response.json()

# Criar evento no MISP
event = misp.new_event(
    distribution=1,
    threat_level_id=2,
    analysis=1,
    info=f"Akira Ransomware - IRIS Case #{CASE_ID}"
)

# Adicionar IOCs
for ioc in iocs:
    misp.add_attribute(
        event,
        {
            "type": ioc["type"],
            "value": ioc["value"],
            "comment": "From Ransomware.live via IRIS",
            "to_ids": True
        }
    )

print(f"✓ Exportados {len(iocs)} IOCs para MISP")
```

---

## 🔧 Troubleshooting

### Problema 1: Módulo Não Aparece na Lista

**Sintomas:**
- Não vejo "Ransomware.live" em Advanced → Modules

**Soluções:**

```bash
# 1. Verificar se está instalado
docker exec iriswebapp_app /opt/venv/bin/pip show iris_ransomwarelive

# Se não aparecer nada:
# 2. Reinstalar no app
./buildnpush2iris.sh -a

# 3. Reiniciar serviços
cd /opt/iris-web
docker compose restart app worker

# 4. Aguardar 30 segundos
sleep 30

# 5. Verificar logs
docker logs iriswebapp_app --tail 50 | grep -i module
```

---

### Problema 2: Enriquecimento Não Funciona

**Sintomas:**
- Preencho o campo mas nada acontece
- Sem notas criadas
- Sem IOCs adicionados

**Diagnóstico:**

```bash
# 1. Verificar logs do worker
docker logs iriswebapp_worker --tail 100 | grep '\[RL\]'

# Procure por erros como:
# [RL] Error fetching group profile: 404
# [RL] No ransomware_group found
# [RL] Failed to create note
```

**Soluções por erro:**

**Erro: "No ransomware_group found"**
- ✅ Verifique se preencheu o campo corretamente
- ✅ Nome do campo deve ser exatamente: `ransomware_group`
- ✅ Verifique JSON do custom attribute

**Erro: "404" ou "Group not found"**
- ✅ Grupo não existe na base Ransomware.live
- ✅ Tente outro nome ou alias
- ✅ Verifique: https://ransomware.live/#/group

**Erro: "Connection timeout"**
- ✅ Verifique conexão internet: `curl https://api-pro.ransomware.live`
- ✅ Verifique firewall/proxy

**Erro: "Failed to create note"**
- ✅ Problema de permissão no banco
- ✅ Reinicie containers: `docker compose restart app worker db`

---

### Problema 3: IOCs Não São Adicionados

**Sintomas:**
- Notas criadas OK
- Mas aba IOC está vazia

**Solução:**

```bash
# 1. Verificar logs específicos de IOCs
docker logs iriswebapp_worker --tail 200 | grep -A 20 "ADDING IOCs"

# 2. Verificar se API retornou IOCs
# Teste manual:
curl "https://api-pro.ransomware.live/iocs/akira"

# 3. Verificar banco de dados
docker exec iriswebapp_db psql -U postgres -d iris_db -c \
  "SELECT COUNT(*) FROM ioc WHERE ioc_description LIKE '%Ransomware.live%';"

# Se retornar 0, há problema de inserção

# 4. Verificar permissões
docker exec iriswebapp_db psql -U postgres -d iris_db -c \
  "SELECT * FROM ioc_type LIMIT 5;"
```

---

### Problema 4: Erro "Module already exists"

**Sintomas:**
- Erro ao tentar habilitar: "Module already exists in Iris"

**Solução:**

```bash
# 1. Módulo já está habilitado, apenas verifique status
# Advanced → Modules → Procure o módulo

# 2. Se quiser realmente reinstalar:
# Desabilite primeiro na UI, depois:
docker exec iriswebapp_worker /opt/venv/bin/pip uninstall -y iris_ransomwarelive
docker exec iriswebapp_app /opt/venv/bin/pip uninstall -y iris_ransomwarelive

# Reinstale
./buildnpush2iris.sh -ar
```

---

### Problema 5: Campo Ransomware Group Não Aparece

**Sintomas:**
- Não vejo o campo ao editar o caso

**Solução:**

1. **Verifique Custom Attributes**
   ```
   Advanced → Custom Attributes → Aba "Cases"
   ```

2. **Verifique JSON:**
   - Deve ter exatamente a estrutura mostrada na seção "Configuração Inicial"
   - **Atenção:** Maiúsculas/minúsculas importam!

3. **Se estiver correto mas não aparece:**
   ```bash
   # Reiniciar containers
   docker compose restart app worker
   
   # Limpar cache do navegador
   # Ctrl+Shift+Delete (Chrome/Firefox)
   
   # Fazer logout e login novamente
   ```

---

### Logs Úteis para Debug

```bash
# Logs do worker (onde o módulo roda)
docker logs iriswebapp_worker -f | grep '\[RL\]'

# Logs do app (interface)
docker logs iriswebapp_app --tail 100

# Logs do banco de dados
docker logs iriswebapp_db --tail 50

# Ver todos os logs do módulo
docker logs iriswebapp_worker 2>&1 | grep '\[RL\]' > module_logs.txt

# Ver últimas 500 linhas
docker logs iriswebapp_worker --tail 500 | grep '\[RL\]'
```

---

## ❓ FAQ - Perguntas Frequentes

### Sobre Funcionalidade

**P: O módulo funciona offline?**  
R: Não. O módulo precisa de conexão com a API Ransomware.live (https://api-pro.ransomware.live).

**P: Quanto tempo demora o enriquecimento?**  
R: Tipicamente 5-10 segundos por caso.

**P: Posso enriquecer casos antigos?**  
R: Sim! Use o enriquecimento manual (botão "Processors").

**P: Quantos IOCs são adicionados em média?**  
R: Entre 100-200 IOCs por grupo, dependendo da disponibilidade na API.

**P: Os IOCs são atualizados automaticamente?**  
R: Não. Para atualizar, use enriquecimento manual novamente.

---

### Sobre Instalação

**P: Funciona no Windows?**  
R: Não diretamente. O IRIS roda em Linux (Ubuntu recomendado). Você pode usar WSL2.

**P: Preciso de API Key?**  
R: Não é obrigatório, mas recomendado para uso intensivo.

**P: Funciona com IRIS em produção?**  
R: Sim! Testado em produção com IRIS v2.4.22.

**P: Posso instalar em um IRIS já em uso?**  
R: Sim, é seguro. Não afeta casos ou dados existentes.

---

### Sobre Grupos Ransomware

**P: Como saber se um grupo é suportado?**  
R: Consulte: https://ransomware.live/#/group

**P: O que fazer se meu grupo não estiver na lista?**  
R: 
1. Verifique aliases (ex: Cl0p → Clop)
2. Aguarde - novos grupos são adicionados frequentemente
3. Solicite adição em: https://ransomware.live

**P: Posso adicionar grupos customizados?**  
R: Não diretamente. O módulo usa a API Ransomware.live.

---

### Sobre Dados e Privacidade

**P: Os dados do meu caso são enviados para Ransomware.live?**  
R: Não! Apenas o NOME do grupo é usado na requisição à API. Nenhum dado sensível é enviado.

**P: Posso usar sem conexão internet?**  
R: Não. A API precisa ser acessível.

**P: Os IOCs são confiáveis?**  
R: Sim, mas sempre faça análise complementar. Não confie 100% em uma única fonte.

---

## 📚 Glossário

| Termo | Significado |
|-------|-------------|
| **IRIS** | Incident Response Investigation System - plataforma DFIR |
| **DFIR** | Digital Forensics & Incident Response |
| **IOC** | Indicator of Compromise - indicador de comprometimento |
| **TTP** | Tactics, Techniques, and Procedures (MITRE ATT&CK) |
| **YARA** | Ferramenta de detecção de malware baseada em regras |
| **Hook** | Ponto de extensão no IRIS para módulos |
| **Enrichment** | Enriquecimento - adicionar inteligência ao caso |
| **Custom Attribute** | Campo customizado no IRIS |
| **Worker** | Container que processa tarefas em background |
| **App** | Container da interface web do IRIS |
| **API Key** | Chave de autenticação para API |

---

## 📞 Suporte

### Precisa de Ajuda?

**🐛 Bugs e Problemas:**
- GitHub Issues: https://github.com/SEU-USUARIO/iris-ransomwarelive-module/issues

**💬 Dúvidas Gerais:**
- IRIS Discord: https://discord.gg/iris
- GitHub Discussions: https://github.com/SEU-USUARIO/iris-ransomwarelive-module/discussions

**📧 Contato Direto:**
- Email: neto@francci.net

**📖 Documentação:**
- README: https://github.com/SEU-USUARIO/iris-ransomwarelive-module
- IRIS Docs: https://docs.dfir-iris.org/

---

## 📝 Checklist de Instalação Completa

Use esta lista para garantir que tudo está configurado:

- [ ] IRIS v2.4.22+ instalado e funcionando
- [ ] Ubuntu 22.04 ou 24.04
- [ ] Python 3.8+ no host
- [ ] Docker e Docker Compose funcionando
- [ ] Acesso à internet (API Ransomware.live)
- [ ] Módulo clonado do GitHub
- [ ] Script `buildnpush2iris.sh` executado com `-ar`
- [ ] Módulo instalado no worker (verificado)
- [ ] Módulo instalado no app (verificado)
- [ ] Módulo habilitado na UI do IRIS
- [ ] Custom attribute "ransomware_group" criado
- [ ] Caso de teste criado
- [ ] Campo "Ransomware group" preenchido
- [ ] Enriquecimento funcionou (notas criadas)
- [ ] IOCs adicionados à aba IOC
- [ ] Logs sem erros

**✅ Se todos os itens acima estão marcados, parabéns! Você está pronto para usar o módulo em produção!**

---

## 🎉 Conclusão

Você completou o manual do usuário! Agora você sabe:

- ✅ Como instalar o módulo
- ✅ Como configurar corretamente
- ✅ Como usar em casos reais
- ✅ Como resolver problemas comuns
- ✅ Como integrar com outras ferramentas

**Próximos Passos:**
1. Teste com casos reais de ransomware
2. Integre os IOCs com suas ferramentas de segurança
3. Compartilhe inteligência com sua equipe
4. Contribua com melhorias no GitHub

**Lembre-se:** Este módulo é uma ferramenta. O conhecimento e análise humana continuam essenciais!

---

**Versão do Manual:** 3.3.1  
**Última Atualização:** Janeiro 2025  
**Licença:** Apache 2.0  

**Made with ❤️ by the DFIR Community**
