ChessInsight — estado al 28 de agosto de 2026
Resumen ejecutivo

El principal bloqueo del informe anterior fue resuelto: la rama del módulo 07 fue integrada en main mediante la PR #144 el 27 de agosto.

La integración es amplia —65 archivos, 10.174 líneas agregadas—, pero el núcleo funcional apenas comienza: solamente F07-001 Game import figura terminado. Stockfish, MultiPV, posiciones críticas, candidatas, SHAP integrado, ejercicios y UI siguen pendientes según el plan del módulo 07.

El riesgo inmediato es que la PR se integró con CI fallido: Python 3.10 no puede instalar numpy==2.3.1, por lo que los tests ni siquiera se ejecutaron.

Progreso verificado desde el 21 de agosto
Área	Avance verificado	Estado real
Integración	PR #144 fusionada en main	Completado
Módulo 07	Plan dividido en 07.0–07.8, catálogo de 44 features y criterios verificables	Diseño integrado
Importación PGN	Reconstrucción de jugadas, SAN/UCI y FEN antes/después	F07-001 terminado
Ingestión personal	Descarga Chess.com/Lichess, rango de fechas, persistencia y generación opcional de features/tácticas	Implementado, no validado por CI
Modelo mental	Prototipo de triggers, taxonomía de candidatas y anti-blunder para jugador aproximado de 1600	Prueba de concepto descartable
Validación humana	Notebook y especificación 6.6 agregados	Infraestructura experimental
LLM	Proveedor compatible con API OpenAI y configuración ampliada	Implementado
FastAPI/Streamlit	Sin cambios funcionales en la PR	Diferidos explícitamente
Stockfish módulo 07	Sin implementación nueva	Pendiente
SHAP	Sin cambios	Persisten riesgos anteriores
Generación de ejercicios	Solo definición F07-044; sin validador automático	Pendiente

La nueva ingestión de jugadores constituye un avance útil para alimentar los casos reales: importa partidas, evita duplicados, genera features y permite ejecutar la detección táctica existente mediante with_tactics.

Bloqueadores y riesgos priorizados
Prioridad	Bloqueador o riesgo	Consecuencia
P0	CI fallido por numpy==2.3.1 sobre Python 3.10	Ningún test de la PR fue ejecutado
P0	Solo F07-001 está terminado	Todavía no existe el flujo PGN → Stockfish → posición crítica → candidatas
P0	Evaluación Stockfish sin POV normalizado	Riesgo de invertir pérdidas y ventajas al cambiar el turno
P1	PR muy grande, sin descripción ni revisión registrada	Mezcla documentación, prototipos, ingestión y LLM; dificulta detectar regresiones
P1	Código analysis/mental_model declarado descartable, pero ya integrado	Puede transformarse accidentalmente en contrato de producción
P1	SHAP mantiene fallbacks aleatorios silenciosos	Una explicación simulada puede presentarse como evidencia real
P1	SHAP multiclase sigue suponiendo que el índice 1 representa “error”	Explicaciones incorrectas para good/inaccuracy/mistake/blunder
P2	Detección táctica y generación de ejercicios continúan confundidas	Una etiqueta táctica no garantiza un puzzle válido
P2	FastAPI, Streamlit y código del curso usan todavía límites y nomenclaturas históricas	Riesgo de integrar el módulo 07 mediante adaptadores inconsistentes

El problema SHAP está confirmado en el servicio actual: si falta el modelo o falla el cálculo, genera predicciones y valores SHAP aleatorios.

Decisiones necesarias
Prioridad	Decisión	Recomendación
P0	Runtime Python oficial	Mantener Python 3.10 implica fijar NumPy compatible; migrar a 3.11 exige validar todo el entorno. Resolverlo antes de continuar
P0	Contratos definitivos	No reutilizar directamente las dataclass del prototipo; crear DTO/Pydantic canónicos para posición, análisis, candidata y review pack
P0	Política Stockfish	POV fijo del jugador, límites reproducibles, MultiPV=3 y persistencia de versión/opciones
P1	Alcance del prototipo mental	Conservarlo como laboratorio; promover únicamente funciones respaldadas por PGN reales y golden tests
P1	Modo SHAP	Simulación solo mediante bandera explícita de desarrollo; error duro en producción
P2	FastAPI/Streamlit	FastAPI como frontera futura; Streamlit como cliente de validación. Mantener ambos fuera del primer incremento
P2	Ejercicio válido	Exigir legalidad, solución superior, estabilidad, deduplicación y dificultad antes de guardar el ejercicio
Próximos pasos concretos
Orden	Entregable	Criterio de finalización
1	Reparar CI	Dependencias instaladas y suite completa ejecutada en verde
2	Contratos analysis_contracts	Independientes del prototipo, notebooks, FastAPI y Streamlit
3	Casos reales	10–20 posiciones propias con PGN, FEN y resultado humano esperado
4	Stockfish F07-003/004/005	Evaluación normalizada, pérdida en centipeones y mates probados para ambos colores
5	Detector mínimo F07-006/012/013	Ranking reproducible donde los errores conocidos aparezcan entre los primeros
6	MultiPV F07-014/015/016	Tres candidatas legales y evaluación independiente de la jugada realizada
7	Comparación y abstención	Diferencias objetivas; NEEDS_REVIEW cuando la evidencia no alcanza
8	Review pack y golden dataset	JSON reproducible y al menos diez regresiones automáticas
9	Endurecer SHAP	Sin aleatoriedad implícita, clases por nombre y modelo/esquema versionados
10	Validador de ejercicios	Convierte diagnósticos confirmados en ejercicios; no consume simples etiquetas tácticas
11	FastAPI	Endpoint asíncrono sobre contratos ya estables
12	Streamlit	Tablero y evidencia para revisión humana, sin lógica de dominio
Supuestos explícitos
No se considera trabajo local o todavía no publicado en GitHub.
Los estados del catálogo del módulo 07 se toman como fuente de verdad.
Los tests nuevos pueden funcionar localmente, pero no se consideran verificados porque GitHub Actions se detuvo durante la instalación.
FastAPI, Streamlit, SHAP y tácticas preexistentes continúan disponibles, pero no están integrados ni validados contra los contratos del módulo 07.

El cuello de botella cambió: ya no es integrar la especificación, sino recuperar una base verificable después de una fusión grande. La secuencia correcta es CI → contratos → Stockfish/POV → posiciones críticas → MultiPV → validación humana. API, UI, SHAP pedagógico y ejercicios quedan después.