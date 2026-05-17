#Requires -Version 5.1
<#
.SYNOPSIS
    Carga el plan de estudio AI Engineering + GenAI for Beginners en Google Calendar.

.DESCRIPTION
    Usa Google Calendar API v3 con OAuth 2.0 (flujo Desktop App) para crear
    los eventos del roadmap directamente en tu calendario de Google.

.PARAMETER PlanStartDate
    Fecha de inicio del plan (Semana 1). Por defecto: 2026-06-01.
    Todos los eventos se calculan relativos a esta fecha.

.PARAMETER CalendarId
    ID del calendario destino. Usar "primary" para el calendario principal,
    o el ID de un calendario específico (obtenible en Google Calendar > Ajustes).

.PARAMETER DryRun
    Si se especifica, muestra los eventos que se crearían SIN llamar a la API.

.EXAMPLE
    # Primera ejecución — abrirá el navegador para autorizar
    .\load_plan_to_google_calendar.ps1 -PlanStartDate "2026-06-01"

.EXAMPLE
    # Modo simulación — no crea nada
    .\load_plan_to_google_calendar.ps1 -DryRun

.NOTES
    CONFIGURACION REQUERIDA antes de ejecutar — ver sección marcada con <<<.
    El token OAuth se guarda en google_token.json en el mismo directorio.
    Si el token expira, el script lo refresca automáticamente.
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [datetime]$PlanStartDate = [datetime]"2026-06-01",
    [string]$CalendarId = "primary",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# ============================================================
# <<< CONFIGURACION — MODIFICAR ESTOS VALORES ANTES DE USAR >>>
# ============================================================
# Paso 1: Ve a https://console.cloud.google.com/
# Paso 2: Crear proyecto > APIs y servicios > Habilitar API > "Google Calendar API"
# Paso 3: Credenciales > Crear credenciales > ID de cliente OAuth > Tipo: "Aplicación de escritorio"
# Paso 4: Descarga el JSON o copia los valores aquí:
$ClientId = "REEMPLAZAR_CON_TU_CLIENT_ID.apps.googleusercontent.com"
$ClientSecret = "REEMPLAZAR_CON_TU_CLIENT_SECRET"

# URI de redirección — debe coincidir exactamente con la configurada en Google Cloud Console
# En la consola: Credenciales > tu cliente OAuth > Agregar URI de redirección autorizado: http://localhost:8080/callback
$RedirectUri = "http://localhost:8080/callback"

# Archivos locales
$TokenFile = Join-Path $PSScriptRoot "google_token.json"

# Duración en horas de cada sesión de estudio
$SessionHours = 2

# Hora de inicio de las sesiones (formato HH:mm)
$SessionStartTime = "09:00"
# ============================================================

$Scope = "https://www.googleapis.com/auth/calendar"
$AuthUrl = "https://accounts.google.com/o/oauth2/v2/auth"
$TokenUrl = "https://oauth2.googleapis.com/token"
$CalendarApiBase = "https://www.googleapis.com/calendar/v3"

# ============================================================
# FUNCIONES OAUTH2
# ============================================================

function Get-AuthorizationCode {
    <# Abre el navegador para que el usuario autorice y captura el código via HTTP listener #>
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

    Write-Host ""
    Write-Host "Abriendo el navegador para autorizar Google Calendar..." -ForegroundColor Cyan
    Write-Host "Si el navegador no abre, accede manualmente a:" -ForegroundColor Yellow
    Write-Host $url -ForegroundColor Yellow
    Write-Host ""

    # Intentar abrir el navegador
    try { Start-Process $url } catch { <# silencioso si falla #> }

    # Iniciar listener HTTP para recibir el callback
    $listener = [System.Net.HttpListener]::new()
    $listener.Prefixes.Add("http://localhost:8080/")
    $listener.Start()

    Write-Host "Esperando autorización en http://localhost:8080/callback ..." -ForegroundColor Cyan

    $context = $listener.GetContext()
    $request = $context.Request

    # Responder al navegador
    $responseHtml = "<html><body><h2>Autorización completada.</h2><p>Puedes cerrar esta ventana.</p></body></html>"
    $buffer = [System.Text.Encoding]::UTF8.GetBytes($responseHtml)
    $context.Response.ContentLength64 = $buffer.Length
    $context.Response.OutputStream.Write($buffer, 0, $buffer.Length)
    $context.Response.Close()
    $listener.Stop()

    $query = $request.QueryString
    if ($query["error"]) {
        throw "Error de autorización Google OAuth: $($query['error'])"
    }
    if ($query["state"] -ne $state) {
        throw "Estado OAuth inválido — posible ataque CSRF."
    }

    return $query["code"]
}

function Invoke-TokenExchange {
    param([string]$Code)
    <# Intercambia el código de autorización por access_token + refresh_token #>
    $body = @{
        code          = $Code
        client_id     = $ClientId
        client_secret = $ClientSecret
        redirect_uri  = $RedirectUri
        grant_type    = "authorization_code"
    }
    $response = Invoke-RestMethod -Uri $TokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
    return $response
}

function Invoke-TokenRefresh {
    param([string]$RefreshToken)
    <# Refresca el access_token usando el refresh_token guardado #>
    $body = @{
        refresh_token = $RefreshToken
        client_id     = $ClientId
        client_secret = $ClientSecret
        grant_type    = "refresh_token"
    }
    $response = Invoke-RestMethod -Uri $TokenUrl -Method Post -Body $body -ContentType "application/x-www-form-urlencoded"
    return $response
}

function Get-ValidToken {
    <# Devuelve un access_token válido, refresca o hace OAuth si es necesario #>
    Add-Type -AssemblyName System.Web

    if (Test-Path $TokenFile) {
        $saved = Get-Content $TokenFile -Raw | ConvertFrom-Json
        $expiresAt = [datetime]$saved.expires_at

        if ($expiresAt -gt (Get-Date).AddMinutes(5)) {
            # Token aún vigente
            return $saved.access_token
        }

        if ($saved.refresh_token) {
            Write-Host "Refrescando token OAuth..." -ForegroundColor Cyan
            try {
                $refreshed = Invoke-TokenRefresh -RefreshToken $saved.refresh_token
                $tokenData = [PSCustomObject]@{
                    access_token  = $refreshed.access_token
                    refresh_token = $saved.refresh_token
                    expires_at    = (Get-Date).AddSeconds($refreshed.expires_in).ToString("o")
                }
                $tokenData | ConvertTo-Json | Set-Content $TokenFile -Encoding UTF8
                return $refreshed.access_token
            }
            catch {
                Write-Warning "No se pudo refrescar el token. Iniciando flujo OAuth completo..."
            }
        }
    }

    # Flujo OAuth completo
    $code = Get-AuthorizationCode
    $tokens = Invoke-TokenExchange -Code $code
    $tokenData = [PSCustomObject]@{
        access_token  = $tokens.access_token
        refresh_token = $tokens.refresh_token
        expires_at    = (Get-Date).AddSeconds($tokens.expires_in).ToString("o")
    }
    $tokenData | ConvertTo-Json | Set-Content $TokenFile -Encoding UTF8
    Write-Host "Token OAuth guardado en: $TokenFile" -ForegroundColor Green
    return $tokens.access_token
}

# ============================================================
# FUNCION: CREAR EVENTO EN GOOGLE CALENDAR
# ============================================================

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
    $tzId = [System.TimeZoneInfo]::Local.Id

    # Google Calendar espera formato ISO 8601
    $startStr = $StartDt.ToString("yyyy-MM-ddTHH:mm:ss")
    $endStr = $endDt.ToString("yyyy-MM-ddTHH:mm:ss")

    $eventBody = @{
        summary     = $Title
        description = $Description
        colorId     = $ColorId.ToString()
        start       = @{ dateTime = $startStr; timeZone = $tzId }
        end         = @{ dateTime = $endStr; timeZone = $tzId }
        reminders   = @{
            useDefault = $false
            overrides  = @(
                @{ method = "popup"; minutes = 30 }
            )
        }
    } | ConvertTo-Json -Depth 5

    $uri = "$CalendarApiBase/calendars/$([Uri]::EscapeDataString($CalendarId))/events"
    $headers = @{ Authorization = "Bearer $AccessToken"; "Content-Type" = "application/json" }

    $created = Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $eventBody
    return $created
}

# ============================================================
# DEFINICION DEL PLAN DE ESTUDIO
# Campos: WeekOffset (0-based), DayOffset (0=lunes..6=domingo),
#         Title, Description, DurationHours, ColorId
# ColorId Google Calendar: 1=azul, 2=verde sage, 3=uva, 4=flamingo,
#   5=banana, 6=tangerina, 7=pavo real, 9=blueberry, 10=albahaca, 11=grafito
# ============================================================

$StudyPlan = @(

    # ── ETAPA 1 — Semanas 1–2: Fundamentos AI/ML ──────────────────────────────
    @{
        WeekOffset = 0; DayOffset = 0; DurationHours = 2; ColorId = 9
        Title = "[AI] Sem1 – Microsoft AI for Beginners: Intro AI + ML"
        Description = "SESION A — Teoria`nRecurso: https://github.com/microsoft/AI-For-Beginners`nTemas: Introduccion a AI, Machine Learning, Redes neuronales, NLP basico`n`nSESION B — Ingenieria`nMade With ML: ML systems overview, Data quality, Lifecycle ML`n`nLABORATORIO`nImplementar: Pipeline PGN → features, Notebook exploratorio, Visualizacion de metricas"
    }
    @{
        WeekOffset = 1; DayOffset = 0; DurationHours = 2; ColorId = 9
        Title = "[AI] Sem2 – Microsoft AI for Beginners: NLP basico"
        Description = "SESION A — Teoria`nRecurso: https://github.com/microsoft/AI-For-Beginners`nTemas: NLP basico, clasificacion, secuencias`n`nSESION B — Ingenieria`nMade With ML: Data quality profundo, Lifecycle ML`n`nLABORATORIO`nImplementar: Limpieza datasets, Visualizacion metricas ajedrez"
    }

    # ── ETAPA 1 — Semanas 3–4: HuggingFace NLP ────────────────────────────────
    @{
        WeekOffset = 2; DayOffset = 0; DurationHours = 2; ColorId = 9
        Title = "[AI] Sem3 – HuggingFace NLP: Tokenization y Transformers"
        Description = "SESION A — Teoria`nRecurso: https://huggingface.co/learn/nlp-course/chapter1/1`nTemas: Tokenization, Transformers, Attention`n`nSESION B — Ingenieria`nMade With ML: Experiment tracking, Model evaluation, Metricas ML`n`nLABORATORIO`nImplementar: Similarity search, Embeddings basicos"
    }
    @{
        WeekOffset = 3; DayOffset = 0; DurationHours = 2; ColorId = 9
        Title = "[AI] Sem4 – HuggingFace NLP: Embeddings"
        Description = "SESION A — Teoria`nRecurso: https://huggingface.co/learn/nlp-course`nTemas: Embeddings, fine-tuning intro, BERT family`n`nSESION B — Ingenieria`nMade With ML: Metricas ML, Model evaluation`n`nLABORATORIO`nClustering de errores de ajedrez con embeddings"
    }

    # ── ETAPA 1 — Semanas 5–6: Chip Huyen + GenAI L01, L02, L04, L05 ─────────
    @{
        WeekOffset = 4; DayOffset = 0; DurationHours = 2; ColorId = 5
        Title = "[AI] Sem5 – Chip Huyen: Foundation Models + GenAI L01+L02"
        Description = "SESION A — Teoria`nChip Huyen AI Engineering: Foundation models, Prompting, Context windows, LLM applications`nRecurso: https://www.oreilly.com/library/view/ai-engineering/9781098166298/`n`n[GenAI for Beginners] L01 - Introduction to GenAI and LLMs`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/01-introduction-to-genai`nTemas: Que es GenAI, arquitectura LLMs, tokens, casos de uso`n`n[GenAI for Beginners] L02 - Exploring and Comparing LLMs`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/02-exploring-and-comparing-different-llms`nTemas: Comparacion modelos, criterios seleccion, benchmarks`n`nSESION B — Ingenieria`nMade With ML: Feature stores, Serving concepts, Pipelines productivos`n`nLABORATORIO`nFastAPI inference service, Endpoint PGN → analisis"
    }
    @{
        WeekOffset = 5; DayOffset = 0; DurationHours = 2; ColorId = 5
        Title = "[AI] Sem6 – GenAI L04+L05: Prompt Engineering"
        Description = "SESION A — Teoria + Practica`n`n[GenAI for Beginners] L04 - Prompt Engineering Fundamentals`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/04-prompt-engineering-fundamentals`nTemas: Few-shot, zero-shot, system prompts, templates, roles`n`n[GenAI for Beginners] L05 - Advanced Prompts`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/05-advanced-prompts`nTemas: Chain-of-thought, ReAct, self-consistency, prompt chaining`n`nAplicacion ChessInsightAI:`n- Prompts para explicacion de jugadas y planes posicionales`n- Base para pipeline de analisis posicional"
    }

    # ── ETAPA 2 — Semanas 7–10: RAG + Embeddings + GenAI L08, L15 ────────────
    @{
        WeekOffset = 6; DayOffset = 0; DurationHours = 2; ColorId = 6
        Title = "[AI] Sem7 – Chip Huyen: Retrieval + GenAI L08 Embeddings/Search"
        Description = "SESION A — Teoria`nChip Huyen: Retrieval, Embeddings, RAG, Inference systems`n`n[GenAI for Beginners] L08 - Building Search Apps + Vector Databases`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/08-building-search-applications`nTemas: Embeddings, cosine similarity, vector search, indexing, Azure AI Search`n`nSESION B — Ingenieria`nMade With ML: Deployment, Monitoring, Drift, Observabilidad`n`nLABORATORIO`nVector DB local — iniciar con ChromaDB o FAISS"
    }
    @{
        WeekOffset = 8; DayOffset = 0; DurationHours = 2; ColorId = 6
        Title = "[AI] Sem9 – GenAI L15: RAG and Vector Databases"
        Description = "SESION A — Teoria + Build`n`n[GenAI for Beginners] L15 - RAG and Vector Databases`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/15-rag-and-vector-databases`nTemas: RAG pipeline completo, chunking, retrieval, grounding, re-ranking`n`nChip Huyen: RAG profundo, inference systems`n`nSESION B — Ingenieria`nMade With ML: Drift, Observabilidad`n`nLABORATORIO`nRAG sobre PDFs de ajedrez, indexar posiciones FEN con embeddings"
    }

    # ── ETAPA 2 — Semanas 11–14: Full Stack DL + GenAI L11, L17 ──────────────
    @{
        WeekOffset = 10; DayOffset = 0; DurationHours = 2; ColorId = 11
        Title = "[AI] Sem11 – Full Stack DL: LLM Systems + GenAI L11 Function Calling"
        Description = "SESION A — Teoria`nFull Stack Deep Learning: LLM systems, Agents, Evaluation, Orchestration`nRecurso: https://fullstackdeeplearning.com/`n`n[GenAI for Beginners] L11 - Function Calling`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/11-integrating-with-function-calling`nTemas: Tool use, function schemas, JSON mode, structured outputs, orquestacion`n`nSESION B — Ingenieria`nFull Stack DL: Serving, Async pipelines, Latency, Batching`n`nLABORATORIO`nLLM llamando Stockfish como herramienta externa mediante function calling"
    }
    @{
        WeekOffset = 12; DayOffset = 0; DurationHours = 2; ColorId = 11
        Title = "[AI] Sem13 – GenAI L17: AI Agents"
        Description = "SESION A — Teoria + Build`n`n[GenAI for Beginners] L17 - AI Agents`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/17-ai-agents`nTemas: Agent loops, planning, memory, tool use, ReAct pattern, frameworks`n`nFull Stack Deep Learning: Planner/Executor, Logging de prompts, Tracing de inferencias`n`nSESION B — Ingenieria`nFull Stack DL: Async pipelines, Latency avanzado`n`nLABORATORIO`nAgente coach con memoria de sesion e historial de partidas"
    }

    # ── ETAPA 3 — Semanas 15–18: LLMOps + GenAI L13, L14 ────────────────────
    @{
        WeekOffset = 14; DayOffset = 0; DurationHours = 2; ColorId = 3
        Title = "[AI] Sem15 – Full Stack DL: LLMOps + GenAI L14 App Lifecycle"
        Description = "SESION A — Teoria`nFull Stack Deep Learning: LLMOps, Prompt evaluation, Tool use, Memory systems`n`n[GenAI for Beginners] L14 - GenAI Application Lifecycle`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/14-the-generative-ai-application-lifecycle`nTemas: LLMOps, evaluacion continua, versionado de prompts, metricas de calidad`n`nSESION B — Ingenieria`nPrompt versioning, Retries/fallbacks, Guardrails, Observabilidad`n`nLABORATORIO`nEvaluation pipeline, Hallucination checks, Checklist LLMOps para produccion"
    }
    @{
        WeekOffset = 16; DayOffset = 0; DurationHours = 2; ColorId = 3
        Title = "[AI] Sem17 – GenAI L13: Securing AI Applications"
        Description = "SESION A — Teoria`n`n[GenAI for Beginners] L13 - Securing AI Applications`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/13-securing-ai-applications`nTemas: Prompt injection, jailbreaks, guardrails, contenido harmful, red teaming`n`nSESION B — Ingenieria`nGrounding validator, Quality scoring, Guardrails en pipeline`n`nLABORATORIO`nGuardrails en endpoint de analisis de ajedrez`nProteger contra prompt injection en input de usuario"
    }

    # ── ETAPA 3 — Semanas 19–22: Fine-tuning + GenAI L16, L18, L19 ───────────
    @{
        WeekOffset = 18; DayOffset = 0; DurationHours = 2; ColorId = 7
        Title = "[AI] Sem19 – HuggingFace + GenAI L16: Open Source Models"
        Description = "SESION A — Teoria`nHuggingFace NLP: Fine-tuning overview, Embeddings avanzados, Inference optimization`n`n[GenAI for Beginners] L16 - Open Source Models + HuggingFace`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/16-open-source-models`nTemas: Modelos OSS, HuggingFace Hub, deployment, licencias, OSS vs propietarios`n`nSESION B — Ingenieria`nQuantization, Ollama, vLLM, Local inference`n`nLABORATORIO`nEvaluar modelos open-source para analisis de partidas"
    }
    @{
        WeekOffset = 20; DayOffset = 0; DurationHours = 2; ColorId = 7
        Title = "[AI] Sem21 – Andrej Karpathy + GenAI L18: Fine-Tuning LLMs"
        Description = "SESION A — Teoria`nAndrej Karpathy: GPT internals, Transformers intuition, Token prediction, LLM architecture`nRecurso: https://www.youtube.com/@AndrejKarpathy`n`n[GenAI for Beginners] L18 - Fine-Tuning LLMs`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/18-fine-tuning`nTemas: Fine-tuning, LoRA, RLHF, dataset curation, evaluacion post-fine-tune`n`nLABORATORIO`nPipeline hibrido: Stockfish + ML tabular + LLM explanations`nFine-tune modelo para terminologia y estilos de ajedrez"
    }
    @{
        WeekOffset = 21; DayOffset = 0; DurationHours = 2; ColorId = 7
        Title = "[AI] Sem22 – GenAI L19: Building with SLMs"
        Description = "SESION A — Teoria + Build`n`n[GenAI for Beginners] L19 - Building with SLMs`nhttps://github.com/cmessoftware/generative-ai-for-beginners/tree/main/19-slm`nTemas: Small Language Models, edge deployment, eficiencia energetica, trade-offs vs LLMs`n`nSESION B — Ingenieria`nOllama local, vLLM, local inference profundo`n`nLABORATORIO`nSLMs para inferencia local sin dependencia de API cloud en ChessInsightAI"
    }
)

# ============================================================
# LOGICA PRINCIPAL
# ============================================================

function Get-EventStartDate {
    param([datetime]$PlanStart, [int]$WeekOffset, [int]$DayOffset, [string]$TimeStr)
    # Mover al lunes de la semana de inicio
    $daysToMonday = [int]$PlanStart.DayOfWeek
    if ($daysToMonday -eq 0) { $daysToMonday = 7 }   # domingo = 7
    $firstMonday = $PlanStart.AddDays(1 - $daysToMonday)

    $eventDate = $firstMonday.AddDays($WeekOffset * 7 + $DayOffset)
    $timeParts = $TimeStr -split ":"
    return [datetime]::new($eventDate.Year, $eventDate.Month, $eventDate.Day,
        [int]$timeParts[0], [int]$timeParts[1], 0)
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host " Plan de Estudio AI Engineering → Google Calendar"    -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Fecha inicio del plan : $($PlanStartDate.ToString('yyyy-MM-dd'))"
Write-Host "  Calendario destino    : $CalendarId"
Write-Host "  Sesiones a crear      : $($StudyPlan.Count)"
if ($DryRun) {
    Write-Host "  MODO                  : DRY RUN (no se crea nada)" -ForegroundColor Yellow
}
Write-Host ""

# Verificar configuración
if (-not $DryRun) {
    if ($ClientId -match "^REEMPLAZAR") {
        Write-Error @"
ERROR: ClientId no configurado.
Edita el script y reemplaza REEMPLAZAR_CON_TU_CLIENT_ID con el Client ID real de Google Cloud Console.
Instrucciones:
  1. Ve a https://console.cloud.google.com/
  2. Proyecto > APIs y servicios > Credenciales
  3. Crear credenciales > ID de cliente OAuth > Aplicacion de escritorio
  4. Copia el Client ID y Client Secret en las variables al inicio del script
"@
    }
    if ($ClientSecret -match "^REEMPLAZAR") {
        Write-Error "ERROR: ClientSecret no configurado. Ver instrucciones en el script."
    }
}

# Obtener token
$accessToken = $null
if (-not $DryRun) {
    $accessToken = Get-ValidToken
    Write-Host "Token OAuth activo." -ForegroundColor Green
}

# Crear eventos
$created = 0
$skipped = 0
$errors = 0

foreach ($evt in $StudyPlan) {
    $startDt = Get-EventStartDate -PlanStart $PlanStartDate `
        -WeekOffset $evt.WeekOffset `
        -DayOffset  $evt.DayOffset `
        -TimeStr    $SessionStartTime

    $endDt = $startDt.AddHours($evt.DurationHours)

    if ($DryRun) {
        Write-Host "[DRY RUN] $($startDt.ToString('yyyy-MM-dd HH:mm')) -> $($endDt.ToString('HH:mm'))  |  $($evt.Title)" -ForegroundColor Gray
        $created++
        continue
    }

    if ($PSCmdlet.ShouldProcess($evt.Title, "Crear evento en Google Calendar")) {
        try {
            $result = New-CalendarEvent `
                -AccessToken   $accessToken `
                -CalendarId    $CalendarId `
                -Title         $evt.Title `
                -Description   $evt.Description `
                -StartDt       $startDt `
                -DurationHours $evt.DurationHours `
                -ColorId       $evt.ColorId

            Write-Host "  [OK] $($startDt.ToString('yyyy-MM-dd'))  $($evt.Title)" -ForegroundColor Green
            $created++
        }
        catch {
            Write-Warning "  [ERROR] $($evt.Title): $_"
            $errors++
        }
    }
}

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Cyan
if ($DryRun) {
    Write-Host "  DRY RUN completado. Eventos que se crearían: $created" -ForegroundColor Yellow
}
else {
    Write-Host "  Eventos creados : $created" -ForegroundColor Green
    if ($errors -gt 0) {
        Write-Host "  Errores         : $errors" -ForegroundColor Red
    }
}
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
