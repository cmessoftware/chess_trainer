#Requires -Version 5.1
<#
.SYNOPSIS
    Carga el plan AI Engineering (57 sesiones de 2h) en Google Calendar via OAuth 2.0

.DESCRIPTION
    Script simplificado que crea eventos directamente desde el plan reorganizado.
    Mantiene configuración mínima (Google OAuth credentials).

.PARAMETER DryRun
    Modo simulación: muestra eventos que se crearían sin llamar a API.

.EXAMPLE
    # Primera ejecución — abre navegador para autorizar
    .\sync_plan_to_calendar.ps1

.EXAMPLE
    # Simulación
    .\sync_plan_to_calendar.ps1 -DryRun
#>
[CmdletBinding()]
param(
    [datetime]$PlanStartDate = [datetime]"2026-05-22",
    [string]$CalendarId = "primary",
    [switch]$ResetCalendar,
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ============================================================
# CONFIGURACION
# ============================================================

$ConfigFile = Join-Path $PSScriptRoot "google_calendar.config.json"
$TokenFile = Join-Path $PSScriptRoot "google_token.json"

if (-not (Test-Path $ConfigFile)) {
    Write-Error "ERROR: Falta archivo $ConfigFile. Copia google_calendar.config.example.json y completa ClientId/ClientSecret."
}

$Config = Get-Content $ConfigFile -Raw | ConvertFrom-Json
$ClientId = $Config.ClientId
$ClientSecret = $Config.ClientSecret
$RedirectUri = $Config.RedirectUri

if ([string]::IsNullOrWhiteSpace($RedirectUri)) { $RedirectUri = "http://localhost:8090/callback" }
$RedirectUriObj = [Uri]$RedirectUri
$ListenerPrefix = "{0}://{1}:{2}/" -f $RedirectUriObj.Scheme, $RedirectUriObj.Host, $RedirectUriObj.Port

$Scope = "https://www.googleapis.com/auth/calendar"
$AuthUrl = "https://accounts.google.com/o/oauth2/v2/auth"
$TokenUrl = "https://oauth2.googleapis.com/token"
$CalendarApiBase = "https://www.googleapis.com/calendar/v3"

# ============================================================
# OAUTH FUNCTIONS
# ============================================================

function Get-AuthorizationCode {
    $state = [System.Guid]::NewGuid().ToString("N")
    $params = [System.Web.HttpUtility]::ParseQueryString("")
    $params["client_id"] = $ClientId
    $params["redirect_uri"] = $RedirectUri
    $params["response_type"] = "code"
    $params["scope"] = $Scope
    $params["access_type"] = "offline"
    $params["prompt"] = "consent"
    $params["state"] = $state

    $url = "$AuthUrl`?" + $params.ToString()

    Write-Host "Abriendo navegador para autorizar..." -ForegroundColor Cyan
    try { Start-Process $url } catch { <# silent #> }

    $listener = [System.Net.HttpListener]::new()
    $listener.Prefixes.Add($ListenerPrefix)
    $listener.Start()
    Write-Host "Esperando autorización en $RedirectUri ..." -ForegroundColor Cyan

    $context = $listener.GetContext()
    $request = $context.Request

    $responseHtml = "<html><body><h2>Autorización completada.</h2><p>Puedes cerrar esta ventana.</p></body></html>"
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($responseHtml)
    $context.Response.ContentLength64 = $buffer.Length
    $context.Response.OutputStream.Write($buffer, 0, $buffer.Length)
    $context.Response.Close()
    $listener.Stop()

    # Parse query string robustamente
    $rawQuery = ""
    if ($request.Url -and $request.Url.Query) { $rawQuery = $request.Url.Query }
    Add-Type -AssemblyName System.Web
    $query = [System.Web.HttpUtility]::ParseQueryString($rawQuery)

    $oauthError = $query.Get("error")
    $returnedState = $query.Get("state")
    $authCode = $query.Get("code")

    if (-not [string]::IsNullOrWhiteSpace($oauthError)) { throw "Error OAuth: $oauthError" }
    if ([string]::IsNullOrWhiteSpace($returnedState) -or $returnedState -ne $state) { throw "Estado OAuth inválido" }
    if ([string]::IsNullOrWhiteSpace($authCode)) { throw "No se recibió authorization code" }

    return $authCode
}

function Invoke-TokenExchange {
    param([string]$Code)
    $body = @{
        code          = $Code
        client_id     = $ClientId
        client_secret = $ClientSecret
        redirect_uri  = $RedirectUri
        grant_type    = "authorization_code"
    }
    return Invoke-RestMethod -Uri $TokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
}

function Invoke-TokenRefresh {
    param([string]$RefreshToken)
    $body = @{
        refresh_token = $RefreshToken
        client_id     = $ClientId
        client_secret = $ClientSecret
        grant_type    = "refresh_token"
    }
    return Invoke-RestMethod -Uri $TokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
}

function Get-ValidToken {
    if (Test-Path $TokenFile) {
        $saved = Get-Content $TokenFile -Raw | ConvertFrom-Json
        $expiresAt = [datetime]$saved.expires_at

        if ($expiresAt -gt (Get-Date).AddMinutes(5)) { return $saved.access_token }

        if ($saved.refresh_token) {
            Write-Host "Refrescando token..." -ForegroundColor Cyan
            try {
                $refreshed = Invoke-TokenRefresh -RefreshToken $saved.refresh_token
                $tokenData = @{
                    access_token  = $refreshed.access_token
                    refresh_token = $saved.refresh_token
                    expires_at    = (Get-Date).AddSeconds($refreshed.expires_in).ToString("o")
                } | ConvertTo-Json
                $tokenData | Set-Content $TokenFile -Encoding UTF8
                return $refreshed.access_token
            }
            catch { }
        }
    }

    $code = Get-AuthorizationCode
    $tokens = Invoke-TokenExchange -Code $code
    $tokenData = @{
        access_token  = $tokens.access_token
        refresh_token = $tokens.refresh_token
        expires_at    = (Get-Date).AddSeconds($tokens.expires_in).ToString("o")
    } | ConvertTo-Json
    $tokenData | Set-Content $TokenFile -Encoding UTF8
    return $tokens.access_token
}

function New-CalendarEvent {
    param(
        [string]$AccessToken,
        [string]$CalendarId,
        [string]$Title,
        [string]$Description,
        [datetime]$StartDt,
        [int]$DurationHours,
        [int]$ColorId = 1
    )

    $endDt = $StartDt.AddHours($DurationHours)
    $startStr = $StartDt.ToString("yyyy-MM-ddTHH:mm:sszzz")
    $endStr = $endDt.ToString("yyyy-MM-ddTHH:mm:sszzz")

    $eventBody = @{
        summary     = $Title
        description = $Description
        colorId     = $ColorId.ToString()
        start       = @{ dateTime = $startStr }
        end         = @{ dateTime = $endStr }
        reminders   = @{
            useDefault = $false
            overrides  = @(
                @{ method = "popup"; minutes = 30 }
            )
        }
    } | ConvertTo-Json -Depth 5

    $uri = "$CalendarApiBase/calendars/$([Uri]::EscapeDataString($CalendarId))/events"
    $headers = @{ Authorization = "Bearer $AccessToken"; "Content-Type" = "application/json" }
    return Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $eventBody
}

function Get-CalendarEventsInRange {
    param(
        [string]$AccessToken,
        [string]$CalendarId,
        [datetime]$TimeMin,
        [datetime]$TimeMax
    )

    $timeMinStr = ([datetimeoffset]$TimeMin).ToString("yyyy-MM-ddTHH:mm:sszzz")
    $timeMaxStr = ([datetimeoffset]$TimeMax).ToString("yyyy-MM-ddTHH:mm:sszzz")
    $uri = "$CalendarApiBase/calendars/$([Uri]::EscapeDataString($CalendarId))/events?singleEvents=true&orderBy=startTime&timeMin=$([Uri]::EscapeDataString($timeMinStr))&timeMax=$([Uri]::EscapeDataString($timeMaxStr))&maxResults=2500"
    $headers = @{ Authorization = "Bearer $AccessToken" }
    $response = Invoke-RestMethod -Uri $uri -Method Get -Headers $headers
    return @($response.items)
}

function Remove-CalendarEvent {
    param(
        [string]$AccessToken,
        [string]$CalendarId,
        [string]$EventId
    )

    $uri = "$CalendarApiBase/calendars/$([Uri]::EscapeDataString($CalendarId))/events/$([Uri]::EscapeDataString($EventId))"
    $headers = @{ Authorization = "Bearer $AccessToken" }
    Invoke-RestMethod -Uri $uri -Method Delete -Headers $headers | Out-Null
}

function Get-EventDescription {
    param([string]$Title)

    switch -Regex ($Title) {
        '^\[AI\] Sem1-A:' { return "Objetivo: entender qué es AI, su historia y su relación con ML/DL/GenAI. Laboratorio: investigar 3 casos de éxito de AI en dominios diversos." }
        '^\[AI\] Sem1-B:' { return "Objetivo: dominar conceptos base de ML, pipeline y métricas. Laboratorio: generar un dataset simple de ajedrez (posición → mejor movimiento) y hacer train/test split." }
        '^\[AI\] Sem1-C:' { return "Objetivo: extraer features estructurados desde archivos PGN usando python-chess. Laboratorio: parser PGN, feature extraction, DataFrame por posición y visualización de distribución." }
        '^\[AI\] Sem2-A:' { return "Objetivo: comprender arquitectura neuronal, forward pass, backprop y activaciones. Laboratorio: entrenar una red simple en sklearn/numpy." }
        '^\[AI\] Sem2-B:' { return "Objetivo: procesar texto, vectorización y contexto. Laboratorio: vectorizar análisis de ajedrez con tokenización manual, BoW y TF-IDF." }
        '^\[AI\] Sem2-C:' { return "Objetivo: validar, limpiar y perfilar datasets de ajedrez. Laboratorio: tipos, nulos, outliers, duplicados y data dictionary." }
        '^\[AI\] Sem3-A:' { return "Objetivo: entender tokenizadores modernos y la arquitectura Transformer. Laboratorio: experimentar con tokenizadores Hugging Face." }
        '^\[AI\] Sem3-B:' { return "Objetivo: profundizar en BERT, GPT y T5. Laboratorio: explorar embeddings y fine-tuning conceptual." }
        '^\[AI\] Sem3-C:' { return "Objetivo: generar embeddings de posiciones de ajedrez. Laboratorio: comparar similitud y visualizar en 2D con t-SNE o UMAP." }
        '^\[AI\] Sem4-A:' { return "Objetivo: trabajar con embeddings densos y métricas de similitud. Laboratorio: comparar cosine, dot product y Euclidean distance." }
        '^\[AI\] Sem4-B:' { return "Objetivo: profundizar en calidad de datos y ciclo de vida ML. Laboratorio: detectar drift en features históricos." }
        '^\[AI\] Sem4-C:' { return "Objetivo: agrupar movimientos fallidos con embeddings. Laboratorio: K-means sobre errores y análisis de patrones." }
        '^\[AI\] Sem5-A:' { return "Objetivo: entender foundation models, escala y propiedades emergentes. Laboratorio: analizar 3 modelos por costo, latencia y capacidades." }
        '^\[AI\] Sem5-B:' { return "Objetivo: introducir GenAI y LLMs. Laboratorio: probar una API de LLM y explorar temperatura y outputs." }
        '^\[AI\] Sem5-C:' { return "Objetivo: definir criterios para elegir modelo según caso de uso. Laboratorio: matriz de comparación y recomendación para ajedrez." }
        '^\[AI\] Sem6-A:' { return "Objetivo: comparar LLMs con benchmarks y trade-offs. Laboratorio: ejecutar un benchmark simple en 3 modelos." }
        '^\[AI\] Sem6-B:' { return "Objetivo: aprender técnicas de prompting básicas. Laboratorio: diseñar variaciones de prompt para análisis de partida." }
        '^\[AI\] Sem6-C:' { return "Objetivo: documentar un template estándar de prompting para ajedrez. Laboratorio: evaluar variantes y elegir la mejor." }
        '^\[AI\] Sem7-A:' { return "Objetivo: usar CoT, ReAct y self-consistency. Laboratorio: implementar CoT para análisis táctico." }
        '^\[AI\] Sem7-B:' { return "Objetivo: comprender retrieval systems y ranking. Laboratorio: comparar BM25 vs embeddings en búsqueda simple." }
        '^\[AI\] Sem7-C:' { return "Objetivo: montar una base vectorial local. Laboratorio: indexar partidas históricas en ChromaDB." }
        '^\[AI\] Sem8-A:' { return "Objetivo: preparar aplicaciones de búsqueda con embeddings e indexación. Laboratorio: búsqueda semántica en ChromaDB." }
        '^\[AI\] Sem8-B:' { return "Objetivo: construir un pipeline RAG completo. Laboratorio: chunking, retrieval y ranking sobre documentos." }
        '^\[AI\] Sem8-C:' { return "Objetivo: aplicar RAG a libros y papers de ajedrez. Laboratorio: query → contexto → respuesta con PDFs." }
        '^\[AI\] Sem9-A:' { return "Objetivo: diseñar sistemas con LLMs, agentes y tool use. Laboratorio: arquitectura simple de agent." }
        '^\[AI\] Sem9-B:' { return "Objetivo: controlar generación de texto con temperature, top-k y top-p. Laboratorio: construir un generador simple de texto." }
        '^\[AI\] Sem9-C:' { return "Objetivo: crear un MVP de recomendaciones automáticas para ChessInsightAI. Laboratorio: integrar LLM con PGN y probar partidas reales." }
        '^\[AI\] Sem10-A:' { return "Objetivo: comprender agent loops, planning, memory y ReAct. Laboratorio: adaptar un ejemplo de agente." }
        '^\[AI\] Sem10-B:' { return "Objetivo: orquestar agentes con ejecución async. Laboratorio: implementar una cadena simple de agentes." }
        '^\[AI\] Sem10-C:' { return "Objetivo: construir un agente coach con memoria de sesión. Laboratorio: persistir contexto y respuestas." }
        '^\[AI\] Sem11-A:' { return "Objetivo: operacionalizar LLMs en producción. Laboratorio: diseñar versionado de prompts y monitoreo." }
        '^\[AI\] Sem11-B:' { return "Objetivo: entender el ciclo de vida de aplicaciones GenAI. Laboratorio: crear un framework de evaluación." }
        '^\[AI\] Sem11-C:' { return "Objetivo: medir calidad de respuestas automáticamente. Laboratorio: benchmark baseline vs prompts mejorados." }
        '^\[AI\] Sem12-A:' { return "Objetivo: proteger aplicaciones de AI. Laboratorio: probar prompt injection y mitigaciones." }
        '^\[AI\] Sem12-B:' { return "Objetivo: observar modelos y pipelines en producción. Laboratorio: logging, tracing y alertas." }
        '^\[AI\] Sem12-C:' { return "Objetivo: implementar guardrails de entrada y salida. Laboratorio: filtros y fallback seguro." }
        '^\[AI\] Sem13-A:' { return "Objetivo: introducir fine-tuning, transfer learning y LoRA. Laboratorio: revisar ejemplos de adaptación eficiente." }
        '^\[AI\] Sem13-B:' { return "Objetivo: explorar modelos open source y licencias. Laboratorio: descargar y ejecutar un modelo localmente." }
        '^\[AI\] Sem13-C:' { return "Objetivo: comparar rendimiento entre modelos OSS y propietarios. Laboratorio: benchmark de 5 preguntas de ajedrez." }
        '^\[AI\] Sem14-A:' { return "Objetivo: entender internals de GPT y scaling laws. Laboratorio: revisar código de nanoGPT." }
        '^\[AI\] Sem14-B:' { return "Objetivo: aprender técnicas de fine-tuning modernas. Laboratorio: preparar dataset para FT." }
        '^\[AI\] Sem14-C:' { return "Objetivo: ajustar un modelo con LoRA para estilo de ajedrez. Laboratorio: entrenar y comparar antes/después." }
        '^\[AI\] Sem15-A:' { return "Objetivo: conocer Small Language Models y despliegue eficiente. Laboratorio: explorar capacidades de SLMs." }
        '^\[AI\] Sem15-B:' { return "Objetivo: servir modelos localmente con Ollama o vLLM. Laboratorio: benchmark local vs cloud." }
        '^\[AI\] Sem15-C:' { return "Objetivo: desplegar modelos localmente sin API cloud. Laboratorio: instalar, configurar y medir latencia." }
        '^\[AI\] Sem16-A:' { return "Objetivo: usar function calling, schemas y structured outputs. Laboratorio: llamar una función simple desde un LLM." }
        '^\[AI\] Sem16-B:' { return "Objetivo: diseñar aplicaciones de chat con historial. Laboratorio: construir una interfaz conversacional." }
        '^\[AI\] Sem16-C:' { return "Objetivo: prototipar un coach conversacional de ajedrez. Laboratorio: integrar chat, prompt, memoria y tools." }
        '^\[AI\] Sem17-A:' { return "Objetivo: generar imágenes y evaluar visualmente. Laboratorio: crear diagramas de tableros de ajedrez." }
        '^\[AI\] Sem17-B:' { return "Objetivo: prototipar rápido con herramientas low-code. Laboratorio: montar un flujo en una herramienta visual." }
        '^\[AI\] Sem17-C:' { return "Objetivo: crear visualizaciones didácticas de análisis. Laboratorio: tableros, anotaciones y secuencias." }
        '^\[AI\] Sem18-A:' { return "Objetivo: diseñar UX para aplicaciones de AI. Laboratorio: mockup para coach app con confianza y feedback." }
        '^\[AI\] Sem18-B:' { return "Objetivo: especializarse en la familia Mistral. Laboratorio: comparar variantes y trade-offs." }
        '^\[AI\] Sem18-C:' { return "Objetivo: benchmark de modelos Mistral. Laboratorio: latencia, calidad y costo." }
        '^\[AI\] Sem19-A:' { return "Objetivo: especializarse en la familia Meta/Llama. Laboratorio: comparar variantes Llama." }
        '^\[AI\] Sem19-B:' { return "Objetivo: dejar una arquitectura lista para producción. Laboratorio: checklist de despliegue, escalabilidad y observabilidad." }
        '^\[AI\] Sem19-C:' { return "Objetivo: integrar todo en ChessInsightAI. Laboratorio: pipeline end-to-end, documentación y checklist de producción." }
        default { return "Sesión del roadmap AI Engineering para ChessInsightAI. Ver detalles en docs/ai_theory/01-ai_Engineer_free_couses_plan_detailed.md." }
    }
}

function Remove-ExistingAiEvents {
    param(
        [string]$AccessToken,
        [string]$CalendarId,
        [datetime]$TimeMin,
        [datetime]$TimeMax
    )

    $events = Get-CalendarEventsInRange -AccessToken $AccessToken -CalendarId $CalendarId -TimeMin $TimeMin -TimeMax $TimeMax
    $targets = @($events | Where-Object { $_.summary -match '^\[AI\]' })

    foreach ($event in $targets) {
        Remove-CalendarEvent -AccessToken $AccessToken -CalendarId $CalendarId -EventId $event.id
        Write-Host "- Eliminado: $($event.summary)" -ForegroundColor DarkYellow
    }

    return $targets.Count
}

# ============================================================
# PLAN: 57 sesiones de 2h (19 semanas × 3 sesiones/semana)
# ============================================================

$Plan = @(
    # Semana 1
    @{ Week = 1; Day = 0; Title = "[AI] Sem1-A: Microsoft AI Intro to AI"; Color = 9 }
    @{ Week = 1; Day = 2; Title = "[AI] Sem1-B: Microsoft AI Machine Learning"; Color = 9 }
    @{ Week = 1; Day = 4; Title = "[AI] Sem1-C: Lab PGN → Features"; Color = 9 }
    
    # Semana 2
    @{ Week = 2; Day = 0; Title = "[AI] Sem2-A: Microsoft AI Neural Networks"; Color = 9 }
    @{ Week = 2; Day = 2; Title = "[AI] Sem2-B: Microsoft AI NLP Basics"; Color = 9 }
    @{ Week = 2; Day = 4; Title = "[AI] Sem2-C: Lab Data Cleaning"; Color = 9 }
    
    # Semana 3
    @{ Week = 3; Day = 0; Title = "[AI] Sem3-A: HuggingFace Tokenization"; Color = 9 }
    @{ Week = 3; Day = 2; Title = "[AI] Sem3-B: HuggingFace Transformers"; Color = 9 }
    @{ Week = 3; Day = 4; Title = "[AI] Sem3-C: Lab Embeddings Basics"; Color = 9 }
    
    # Semana 4
    @{ Week = 4; Day = 0; Title = "[AI] Sem4-A: HuggingFace Embeddings"; Color = 9 }
    @{ Week = 4; Day = 2; Title = "[AI] Sem4-B: Made With ML Data Quality"; Color = 9 }
    @{ Week = 4; Day = 4; Title = "[AI] Sem4-C: Lab Clustering Errors"; Color = 9 }
    
    # Semana 5
    @{ Week = 5; Day = 0; Title = "[AI] Sem5-A: Chip Huyen Foundation Models"; Color = 5 }
    @{ Week = 5; Day = 2; Title = "[AI] Sem5-B: GenAI L01 Intro to GenAI"; Color = 5 }
    @{ Week = 5; Day = 4; Title = "[AI] Sem5-C: Lab Model Selection"; Color = 5 }
    
    # Semana 6
    @{ Week = 6; Day = 0; Title = "[AI] Sem6-A: GenAI L02 Comparing LLMs"; Color = 5 }
    @{ Week = 6; Day = 2; Title = "[AI] Sem6-B: GenAI L04 Prompt Engineering"; Color = 5 }
    @{ Week = 6; Day = 4; Title = "[AI] Sem6-C: Lab Prompting Practice"; Color = 5 }
    
    # Semana 7
    @{ Week = 7; Day = 0; Title = "[AI] Sem7-A: GenAI L05 Advanced Prompts"; Color = 6 }
    @{ Week = 7; Day = 2; Title = "[AI] Sem7-B: Chip Huyen Retrieval Systems"; Color = 6 }
    @{ Week = 7; Day = 4; Title = "[AI] Sem7-C: Lab ChromaDB Setup"; Color = 6 }
    
    # Semana 8
    @{ Week = 8; Day = 0; Title = "[AI] Sem8-A: GenAI L08 Vector Databases"; Color = 6 }
    @{ Week = 8; Day = 2; Title = "[AI] Sem8-B: GenAI L15 RAG Pipeline"; Color = 6 }
    @{ Week = 8; Day = 4; Title = "[AI] Sem8-C: Lab RAG on PDFs"; Color = 6 }
    
    # Semana 9
    @{ Week = 9; Day = 0; Title = "[AI] Sem9-A: Full Stack DL LLM Systems"; Color = 11 }
    @{ Week = 9; Day = 2; Title = "[AI] Sem9-B: GenAI L06 Text Generation"; Color = 4 }
    @{ Week = 9; Day = 4; Title = "[AI] Sem9-C: Lab Generador de Recomendaciones (MVP)"; Color = 4 }
    
    # Semana 10
    @{ Week = 10; Day = 0; Title = "[AI] Sem10-A: GenAI L17 AI Agents"; Color = 11 }
    @{ Week = 10; Day = 2; Title = "[AI] Sem10-B: Full Stack DL Orchestration"; Color = 11 }
    @{ Week = 10; Day = 4; Title = "[AI] Sem10-C: Lab Agent + Memory"; Color = 11 }
    
    # Semana 11
    @{ Week = 11; Day = 0; Title = "[AI] Sem11-A: Full Stack DL LLMOps"; Color = 3 }
    @{ Week = 11; Day = 2; Title = "[AI] Sem11-B: GenAI L14 App Lifecycle"; Color = 3 }
    @{ Week = 11; Day = 4; Title = "[AI] Sem11-C: Lab Evaluation Setup"; Color = 3 }
    
    # Semana 12
    @{ Week = 12; Day = 0; Title = "[AI] Sem12-A: GenAI L13 Security"; Color = 3 }
    @{ Week = 12; Day = 2; Title = "[AI] Sem12-B: Made With ML Monitoring"; Color = 3 }
    @{ Week = 12; Day = 4; Title = "[AI] Sem12-C: Lab Guardrails"; Color = 3 }
    
    # Semana 13
    @{ Week = 13; Day = 0; Title = "[AI] Sem13-A: HuggingFace Fine-tuning"; Color = 7 }
    @{ Week = 13; Day = 2; Title = "[AI] Sem13-B: GenAI L16 Open Source Models"; Color = 7 }
    @{ Week = 13; Day = 4; Title = "[AI] Sem13-C: Lab Model Comparison"; Color = 7 }
    
    # Semana 14
    @{ Week = 14; Day = 0; Title = "[AI] Sem14-A: Karpathy GPT Internals"; Color = 7 }
    @{ Week = 14; Day = 2; Title = "[AI] Sem14-B: GenAI L18 Fine-tuning"; Color = 7 }
    @{ Week = 14; Day = 4; Title = "[AI] Sem14-C: Lab LoRA Training"; Color = 7 }
    
    # Semana 15
    @{ Week = 15; Day = 0; Title = "[AI] Sem15-A: GenAI L19 SLMs"; Color = 7 }
    @{ Week = 15; Day = 2; Title = "[AI] Sem15-B: Made With ML Local Inference"; Color = 7 }
    @{ Week = 15; Day = 4; Title = "[AI] Sem15-C: Lab Ollama Setup"; Color = 7 }
    
    # Semana 16
    @{ Week = 16; Day = 0; Title = "[AI] Sem16-A: GenAI L11 Function Calling"; Color = 11 }
    @{ Week = 16; Day = 2; Title = "[AI] Sem16-B: GenAI L07 Chat Apps"; Color = 4 }
    @{ Week = 16; Day = 4; Title = "[AI] Sem16-C: Lab Coach Bot Demo"; Color = 4 }
    
    # Semana 17
    @{ Week = 17; Day = 0; Title = "[AI] Sem17-A: GenAI L09 Image Generation"; Color = 4 }
    @{ Week = 17; Day = 2; Title = "[AI] Sem17-B: GenAI L10 Low Code AI"; Color = 4 }
    @{ Week = 17; Day = 4; Title = "[AI] Sem17-C: Lab Visual Features"; Color = 4 }
    
    # Semana 18
    @{ Week = 18; Day = 0; Title = "[AI] Sem18-A: GenAI L12 UX for AI"; Color = 4 }
    @{ Week = 18; Day = 2; Title = "[AI] Sem18-B: GenAI L20 Mistral Models"; Color = 4 }
    @{ Week = 18; Day = 4; Title = "[AI] Sem18-C: Lab Multi-model Test"; Color = 4 }
    
    # Semana 19
    @{ Week = 19; Day = 0; Title = "[AI] Sem19-A: GenAI L21 Meta Models"; Color = 4 }
    @{ Week = 19; Day = 2; Title = "[AI] Sem19-B: Full Stack DL Production Ready"; Color = 4 }
    @{ Week = 19; Day = 4; Title = "[AI] Sem19-C: Lab Final Integration"; Color = 4 }
)

# ============================================================
# LOGICA PRINCIPAL
# ============================================================

function Get-EventStartDate {
    param([datetime]$PlanStart, [int]$Week, [int]$Day, [string]$TimeStr = "08:00")
    $daysToMonday = [int]$PlanStart.DayOfWeek
    if ($daysToMonday -eq 0) { $daysToMonday = 7 }
    $firstMonday = $PlanStart.AddDays(1 - $daysToMonday)

    $eventDate = $firstMonday.AddDays(($Week - 1) * 7 + $Day)
    $timeParts = $TimeStr -split ":"
    return [datetime]::new($eventDate.Year, $eventDate.Month, $eventDate.Day,
        [int]$timeParts[0], [int]$timeParts[1], 0)
}

Write-Host ""
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host " Sincronizar Plan AI Engineering → Google Calendar"    -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Fecha inicio: $($PlanStartDate.ToString('yyyy-MM-dd'))"
Write-Host "  Sesiones: $($Plan.Count)"
if ($DryRun) { Write-Host "  MODO: DRY RUN" -ForegroundColor Yellow }
Write-Host ""

if (-not $DryRun) {
    $accessToken = Get-ValidToken
    Write-Host "Token activo." -ForegroundColor Green
}

$firstMonday = $PlanStartDate
$daysToMonday = [int]$firstMonday.DayOfWeek
if ($daysToMonday -eq 0) { $daysToMonday = 7 }
$firstMonday = $firstMonday.AddDays(1 - $daysToMonday)
$planEndDate = $firstMonday.AddDays((19 - 1) * 7 + 4).Date.AddHours(23).AddMinutes(59)

if ($ResetCalendar -and -not $DryRun) {
    Write-Host "Borrando eventos anteriores del roadmap en el rango del plan..." -ForegroundColor Yellow
    $deleted = Remove-ExistingAiEvents -AccessToken $accessToken -CalendarId $CalendarId -TimeMin $firstMonday -TimeMax $planEndDate
    Write-Host "Eliminados: $deleted" -ForegroundColor Yellow
}

$created = 0
$errors = 0

foreach ($evt in $Plan) {
    $startDt = Get-EventStartDate -PlanStart $PlanStartDate -Week $evt.Week -Day $evt.Day
    $endDt = $startDt.AddHours(2)

    if ($DryRun) {
        Write-Host "$($startDt.ToString('yyyy-MM-dd HH:mm')) → $($endDt.ToString('HH:mm')) | $($evt.Title)" -ForegroundColor Gray
        $created++
        continue
    }

    try {
        $description = Get-EventDescription -Title $evt.Title
        New-CalendarEvent -AccessToken $accessToken -CalendarId $CalendarId `
            -Title $evt.Title -Description $description -StartDt $startDt -DurationHours 2 -ColorId $evt.Color
        Write-Host "✓ $($evt.Title)" -ForegroundColor Green
        $created++
    }
    catch {
        Write-Warning "✗ $($evt.Title): $_"
        $errors++
    }
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  DRY RUN: $created eventos se crearían" -ForegroundColor Yellow
}
else {
    Write-Host "  Creados: $created" -ForegroundColor Green
    if ($errors -gt 0) { Write-Host "  Errores: $errors" -ForegroundColor Red }
}
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
