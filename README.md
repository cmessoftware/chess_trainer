# CHESS TRAINER - Versión: v0.1.47-aa53f1f

# CHESS TRAINER - Version: v0.1.20-f9d0260

# Chess Trainer (stable base version)

This project allows you to analyze and tactically train chess games using data science and interactive visualization.

## Features

- Generation of datasets from PGN files
- Tactical enrichment with Stockfish
- Error classification with automatic labels (`error_label`)
- Exploration and visualization with Streamlit and notebooks
- Training of supervised models for error prediction
- Logging and history of predictions

## Requirements

- Python 3.8+
- streamlit
- pandas, seaborn, matplotlib
- python-chess
- scikit-learn
- Stockfish 

## Structure

See the [`VERSIÓN_BASE.md`](./VERSION_BASE.md) file for the complete project structure.

## Quick usage

### Docker Setup (Recommended)

#### Windows Users - One-Command Setup:
```powershell
.\build_up_clean_all.ps1
```

#### 🎯 Benefits of PowerShell Automation:
- **Complete Environment Setup**: Builds and starts all containers with one command
- **Cross-Platform Compatibility**: Native Windows PowerShell support without Unix permission requirements
- **Automatic Cleanup**: Removes unused Docker images to optimize disk usage
- **Service Integration**: Starts both main application and Jupyter notebooks containers
- **Background Operation**: Containers run detached for continuous development workflow
- **Error Reduction**: Automated sequence minimizes manual configuration mistakes

#### Manual Docker Setup:
```bash
docker-compose build
docker-compose up -d
```

### Local Development:
```bash
# Run the main interface
streamlit run app.py (In development)

# Generate datasets
cd /app/src/pipeline
./run_pipeline.sh interactive

```

# chess_trainer
Chess training software using data science tools and the Stockfish chess engine, implemented in a Docker environment.

# Theory on chess game analysis

To use Machine Learning (ML) and Artificial Intelligence (AI) in chess game analysis, you must first understand how game data is represented and how AIs can "learn" game patterns.

## 1. Representation of game information
Chess games can be represented in different ways. One of the most common is the PGN (Portable Game Notation) format, a standard format used to store the moves of a game. Each move is expressed in algebraic notation, for example: "e4" or "Nf3".

**Some key elements you can analyze from a game are:**

- Opening: The first moves of the game, which are well studied in chess.

- Errors and blunders (serious mistakes): Moves that are significantly worse compared to the best possible moves.

- Accuracy: The number of correct moves made during the game.

- Result: Whether you won, lost, or drew.

- Time spent: Whether the player made impulsive moves or thought a lot before playing.

**Game features**

In Machine Learning terms, the features of the game are the data that feed the models so they can make predictions.

**Some key features could be:**

- Number of errors and blunders: This could indicate the player's general skill.

- Move accuracy: How close the player is to optimal moves.

- Openings: Whether the player prefers a specific opening (e.g., Sicilian, Ruy Lopez, etc.).

- Piece development: Whether the player follows good opening and positioning principles.

- Game score: Whether it was a win, loss, or draw.

## 2. Machine Learning applied to chess

**Objective of Machine Learning in chess**

The main objective of Machine Learning (ML) in this context is to build a model that can identify patterns or make predictions about a player's playing style or the outcome of a game, based on historical data (previous games). Depending on the type of problem, there are several ways to approach the solution:

- Classification: Predict a class (e.g., whether a game will have serious errors or not).

- Regression: Predict a continuous value (such as a player's accuracy during a game).

- Cluster analysis: Group players with similar characteristics (e.g., players who make similar mistakes).

- Outcome prediction: Determine the probability that a player will win, lose, or draw based on previous moves.

**Machine Learning models**

Some of the most used models for chess and game analysis are:

- Regression models:

    To predict a continuous variable, such as a player's accuracy or score.

- Classification models:

    To classify games according to the type of error or whether the player has an "aggressive", "defensive", etc. style.

    For example, Random Forest and Support Vector Machines (SVM) are useful for these types of tasks.

- Neural networks:

    More advanced, these networks can learn complex patterns in the data. They are used for tasks such as pattern recognition or move prediction.

    Neural networks are also used in chess for more sophisticated predictions, such as those made by AlphaZero, which uses a deep neural network to play chess.

## 3. How to apply Machine Learning to chess analysis

**Data preprocessing**

Before feeding a Machine Learning model, you need to preprocess the data to transform it into a form the model can understand. This may include:

- Data cleaning:

    - Remove or impute null values.

    - Ensure all data is in the correct format (e.g., convert dates to a proper date format or classify errors).

**Data transformation:**

- Convert moves and openings into a numeric format:

    For example, using one-hot encoding or natural language processing techniques like Word2Vec for openings.

- Normalization and scaling:

    Some features (such as accuracy) may have different ranges. Make sure to scale them so the model is not biased toward certain features.

- Model training

    Once you have preprocessed your data, you can start training your model. To do this, you must split your data into two parts:

        Training set:
        The dataset on which you train the model.

        Test set:
        The dataset the model has not seen, to evaluate its performance.

The model will learn from the features of the games, such as errors, accuracy, and openings, and will try to predict the outcome of the game or identify playing patterns.

- Model evaluation

    Once your model is trained, you must evaluate its performance using the test set. Some common metrics for evaluating classification models are:

        Accuracy: Proportion of correct predictions.

        Precision: How accurate the positive predictions are.

        Recall: How well the model detects all positive predictions.

        F1-score: A combination of precision and recall.

        Hyperparameter tuning

        Some models like Random Forest or SVM have "hyperparameters" that you can adjust to improve model performance. You can use techniques like GridSearchCV to find the best hyperparameters.

## 4. Personalized recommendations to improve play

Once the model is trained, you can use it to make personalized recommendations to players based on their playing style and previous mistakes. For example:

- Opening recommendations:

    If the player makes mistakes in a specific opening, you can suggest other safer openings.

- Move suggestions:

    Based on their style and mistakes made in previous games, the model can suggest more accurate moves or more effective strategies.

- Analysis of previous games:

    Show the player the games in which they made the most mistakes, how they could have played better, and give advice to avoid those mistakes.

# 5. Summary of next steps:

- Collect game data (PGN, Chess.com API or Lichess API).

- Preprocess the data (cleaning, transforming moves into numeric values).

- Train a Machine Learning model to predict patterns or errors in games.

- Evaluate the model and make adjustments if necessary.

- Implement the model in your Django API and generate personalized recommendations for users.

This approach will provide you with a solid foundation to integrate Machine Learning and AI into your chess project, improving both game analysis and user experience.

## Credits

Developed by cmessoftware as part of their practical work for the Data Science Diploma.
