## ANALISIS DETALLADO PROCESO DE PREDICCIONES DEL CHESS TRAINER

Mientras pruebas te pido que me generes un notebook de jupiter en carpeta notebooks con fines académicos para:
- 1. Probar paso a paso el entrenamiento de un modelo de ML, obteniendo datos de features ya cargadas desde la base de datos.
- 2. Implementando diferetnes modelos para detectar error_label, comparación de metricas, criterios para elegir el mejor modelo.
- 3. Generación del modelo en formato pkl.
- 4. Uso de ese modelo para predecir error_level usando partidas no participes del entrenamiento.
- 5. Analisis SHAP para determinar pesos de features en la predicción, poder analizar esos resultados para tener una brebe descripcion (explicar como un humano le podria sacar provecho).
- 6. Generar un promt adaptado para enviar a API de LLM evitando alucinaciones, ambigüedades, falsos positivos (marcar como errro jugada normales por ej), falso negativo (no marcar como error jugadas blunder).
- 7. Invocr api de LLM y obtener resultado en lenguaje natural.
- 8. Indicar criterios para que un humano pueda validar el resultado del LLM con repecto al Promt , al analisis SHAP y a la partida en si misma (exportandola a un estudio de lichess por ejemplo).
- 9. Documentar todo el proceso para que un usuario humano pueda usar el notebook para entender y aprender elproceso descripto , pudiendo modificarlo para adaptar a sus necesidades. 
- 10. Agregar a la documentación un apartado para explicar como se puede extender este proceso a otros problemas como analisis financierdo, trading, scoring crediticio, predicción de errores en farmacia, industria, procesos administrativos.