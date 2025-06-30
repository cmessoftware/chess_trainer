# CHESS TRAINER - Versión: v0.1.20-f9d0260

# Chess Trainer (versión base estable)

Este proyecto permite analizar y entrenar tácticamente partidas de ajedrez usando ciencia de datos y visualización interactiva.

## Funcionalidades

- Generación de conjuntos de datos desde archivos PGN
- Enriquecimiento táctico con Stockfish
- Clasificación de errores con etiquetas automáticas (`error_label`)
- Exploración y visualización con Streamlit y notebooks
- Entrenamiento de modelos supervisados para predicción de errores
- Registro e historial de predicciones

## Requisitos

- Python 3.8+
- streamlit
- pandas, seaborn, matplotlib
- python-chess
- scikit-learn
- Stockfish

## Estructura

Consulta el archivo [`VERSIÓN_BASE.md`](./VERSION_BASE.md) para ver la estructura completa del proyecto.

## Uso rápido

### Configuración Docker (Recomendado)

#### Usuarios de Windows - Configuración con Un Solo Comando:
```powershell
.\build_up_clean_all.ps1
```

#### 🎯 Beneficios de la Automatización PowerShell:
- **Configuración Completa del Entorno**: Construye e inicia todos los contenedores con un comando
- **Compatibilidad Multiplataforma**: Soporte nativo de PowerShell de Windows sin requisitos de permisos Unix
- **Limpieza Automática**: Elimina imágenes Docker no utilizadas para optimizar el uso de disco
- **Integración de Servicios**: Inicia tanto la aplicación principal como los contenedores de notebooks Jupyter
- **Operación en Segundo Plano**: Los contenedores se ejecutan separados para flujo de trabajo de desarrollo continuo
- **Reducción de Errores**: La secuencia automatizada minimiza errores de configuración manual

#### Configuración Manual de Docker:
```bash
docker-compose build
docker-compose up -d
```

### Desarrollo Local:
```bash
# Ejecutar la interfaz principal
streamlit run app.py (En desarrollo)

# Generar conjuntos de datos
cd /app/src/pipeline
./run_pipeline.sh interactive

```

# chess_trainer
Software de entrenamiento de ajedrez utilizando herramientas de ciencia de datos y el motor de ajedrez Stockfish, implementado en un entorno Docker.

# Teoría sobre el análisis de partidas de ajedrez

Para utilizar Machine Learning (ML) e Inteligencia Artificial (IA) en el análisis de partidas de ajedrez, primero debes comprender cómo se representan los datos del juego y cómo las IA pueden "aprender" patrones de juego.

## 1. Representación de la información de la partida
Las partidas de ajedrez pueden representarse de diferentes maneras. Una de las más comunes es mediante el formato PGN (Portable Game Notation), que es un formato estándar utilizado para almacenar las jugadas de una partida. Cada jugada se expresa en notación algebraica, por ejemplo: "e4" o "Nf3".

**Algunos elementos clave que puedes analizar de una partida son:**

- Apertura: Las primeras jugadas de la partida, que en ajedrez están bien estudiadas.

- Errores y blunders (errores graves): Jugadas que son significativamente malas en comparación con las mejores jugadas posibles.

- Precisión: La cantidad de jugadas correctas realizadas durante la partida.

- Resultado: Si ganaste, perdiste o empataste.

- Tiempo de juego: Si el jugador hizo movimientos impulsivos o pensó mucho antes de jugarlas.

**Características de la partida**

En términos de Machine Learning, las características (features) de la partida son los datos que alimentan a los modelos para que puedan hacer predicciones.

**Algunas características clave podrían ser:**

- Número de errores y blunders: Esto podría indicar la habilidad general del jugador.

- Precisión de las jugadas: ¿Cuánto se acerca el jugador a las jugadas óptimas?

- Aperturas: Si el jugador prefiere una apertura específica (por ejemplo, Siciliana, Apertura Ruy López, etc.).

- Desarrollo de las piezas: Si el jugador sigue buenos principios de apertura y posicionamiento.

- Puntuación de la partida: Si fue una victoria, derrota o empate.

## 2. Machine Learning aplicado al ajedrez

**Objetivo del Machine Learning en ajedrez**

El objetivo principal del Machine Learning (ML) en este contexto es construir un modelo que pueda identificar patrones o hacer predicciones sobre el estilo de juego de un jugador o el resultado de una partida, basándose en los datos históricos (las partidas previas). Dependiendo del tipo de problema, hay varias formas de enfocar la solución:

- Clasificación: Predecir una clase (por ejemplo, si una partida tendrá errores graves o no).

- Regresión: Predecir un valor continuo (como la precisión de un jugador durante una partida).

- Análisis de clústeres: Agrupar jugadores con características similares (por ejemplo, jugadores que cometen errores similares).

- Predicción de resultados: Determinar la probabilidad de que un jugador gane, pierda o empate según las jugadas previas.

**Modelos de Machine Learning**

Algunos de los modelos más utilizados para análisis de ajedrez y juegos son:

- Modelos de regresión:

    Para predecir una variable continua, como la precisión o el puntaje de un jugador.

- Modelos de clasificación:

    Para clasificar partidas según el tipo de error o si el jugador tiene un estilo "agresivo", "defensivo", etc.

    Por ejemplo, Random Forest y Support Vector Machines (SVM) son útiles para estos tipos de tareas.

- Redes neuronales:

    Más avanzadas, estas redes pueden aprender patrones complejos en los datos. Se utilizan para tareas como el reconocimiento de patrones o la predicción de jugadas.

    Las redes neuronales también se utilizan en el ajedrez para predicciones más sofisticadas, como las que hace AlphaZero, que emplea una red neuronal profunda para jugar ajedrez.

## 3. Cómo aplicar Machine Learning al análisis de ajedrez

**Preprocesamiento de datos**

Antes de alimentar un modelo de Machine Learning, necesitas preprocesar los datos para transformarlos en una forma que el modelo pueda entender. Esto puede incluir:

- Limpieza de los datos:

    - Eliminar o imputar valores nulos.

    - Asegurarte de que todos los datos estén en el formato adecuado (por ejemplo, convertir fechas a un formato de fecha adecuado o clasificar errores).

**Transformación de los datos:**

- Convertir jugadas y aperturas en un formato numérico:

    Por ejemplo, usando codificación one-hot o técnicas de procesamiento de lenguaje natural como Word2Vec para las aperturas.

- Normalización y escalado:

    Algunas características (como la precisión) pueden tener diferentes rangos. Asegúrate de escalarlas para que el modelo no se vea sesgado hacia ciertas características.

- Entrenamiento del modelo

    Una vez que hayas preprocesado tus datos, puedes empezar a entrenar tu modelo. Para ello, debes dividir tus datos en dos partes:

        Conjunto de entrenamiento:
        Conjunto de datos sobre el que entrenas el modelo.

        Conjunto de prueba:
        Conjunto de datos que el modelo no ha visto, para evaluar su rendimiento.

El modelo aprenderá de las características de las partidas, como los errores, la precisión y las aperturas, y tratará de predecir el resultado de la partida o identificar patrones de juego.

- Evaluación del modelo

    Una vez que tu modelo esté entrenado, debes evaluar su rendimiento usando el conjunto de prueba. Algunas métricas comunes para evaluar modelos de clasificación son:

        Exactitud: Proporción de predicciones correctas.

        Precisión: Cuán exactas son las predicciones positivas.

        Recall: Cuán bien el modelo detecta todas las predicciones positivas.

        F1-score: Una combinación de precisión y recall.

        Ajuste de hiperparámetros

        Algunos modelos como Random Forest o SVM tienen "hiperparámetros" que puedes ajustar para mejorar el rendimiento del modelo. Puedes usar técnicas como GridSearchCV para encontrar los mejores hiperparámetros.

## 4. Recomendaciones personalizadas para mejorar el juego

Una vez que el modelo esté entrenado, puedes usarlo para hacer recomendaciones personalizadas a los jugadores basadas en su estilo de juego y sus errores previos. Por ejemplo:

- Recomendaciones de apertura:

    Si el jugador comete errores en una apertura específica, puedes sugerirle otras aperturas más seguras.

- Sugerencias de jugadas:

    Basadas en su estilo y los errores cometidos en partidas anteriores, el modelo puede sugerir jugadas más precisas o estrategias más efectivas.

- Análisis de partidas anteriores:

    Mostrar al jugador las partidas en las que cometió más errores, cómo podría haber jugado mejor, y dar consejos para evitar esos errores.

# 5. Resumen de los siguientes pasos:

- Recolectar datos de partidas (PGN, Chess.com API o Lichess API).

- Preprocesar los datos (limpieza, transformación de jugadas en valores numéricos).

- Entrenar un modelo de Machine Learning para predecir patrones o errores en las partidas.

- Evaluar el modelo y realizar ajustes si es necesario.

- Implementar el modelo en tu API Fast API y generar recomendaciones personalizadas para los usuarios.

Este enfoque te proporcionará una base sólida para integrar Machine Learning e IA en tu proyecto de ajedrez, mejorando tanto el análisis de partidas como la experiencia del usuario.

## Créditos

Desarrollado por cmessoftware como parte de su trabajo práctico para la Diplomatura en Ciencia de Datos.
