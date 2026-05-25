"""
🎯 Predicciones Interactivas de Ajedrez
Herramienta para predecir errores en jugadas de ajedrez en tiempo real
"""

import pandas as pd
import pickle
from pathlib import Path
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChessErrorPredictor:
    """Predictor de errores en jugadas de ajedrez"""
    
    def __init__(self):
        self.model = None
        self.features = None
        self.is_loaded = False
    
    def load_model(self):
        """Cargar modelo y features"""
        
        model_path = Path("models/chess_error_classifier.pkl")
        features_path = Path("models/feature_names.pkl")
        
        if not model_path.exists() or not features_path.exists():
            logger.error("❌ Modelo no encontrado. Ejecuta simple_predictions.py primero.")
            return False
        
        try:
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            with open(features_path, 'rb') as f:
                self.features = pickle.load(f)
            
            self.is_loaded = True
            logger.info("✅ Modelo cargado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error cargando modelo: {e}")
            return False
    
    def predict_move(self, move_data):
        """
        Predecir error de una jugada
        
        move_data: dict con las características de la jugada
        Ejemplo:
        {
            'material_balance': 0,
            'material_total': 39,
            'num_pieces': 32,
            'branching_factor': 20,
            'self_mobility': 28,
            'opponent_mobility': 28,
            'score_diff': 0.15,
            'move_number': 5,
            'white_elo': 1800,
            'black_elo': 1850
        }
        """
        
        if not self.is_loaded:
            logger.error("❌ Modelo no cargado")
            return None
        
        try:
            # Crear DataFrame con las features necesarias
            X = pd.DataFrame([move_data], columns=self.features)
            X = X.fillna(0)  # Rellenar valores faltantes
            
            # Hacer predicción
            prediction = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            confidence = probabilities.max()
            
            # Obtener probabilidades por clase
            classes = self.model.classes_
            class_probs = dict(zip(classes, probabilities))
            
            return {
                'prediction': prediction,
                'confidence': confidence,
                'probabilities': class_probs
            }
            
        except Exception as e:
            logger.error(f"❌ Error en predicción: {e}")
            return None
    
    def get_feature_info(self):
        """Obtener información sobre las features"""
        
        if not self.is_loaded:
            return None
        
        feature_descriptions = {
            'material_balance': 'Balance material (blancas - negras)',
            'material_total': 'Material total en el tablero',
            'num_pieces': 'Número total de piezas',
            'branching_factor': 'Factor de ramificación (jugadas posibles)',
            'self_mobility': 'Movilidad de quien juega',
            'opponent_mobility': 'Movilidad del oponente',
            'score_diff': 'Diferencia de evaluación (después - antes)',
            'move_number': 'Número de jugada',
            'white_elo': 'ELO del jugador blanco',
            'black_elo': 'ELO del jugador negro'
        }
        
        return feature_descriptions

def create_sample_move():
    """Crear una jugada de ejemplo"""
    
    return {
        'material_balance': 0,      # Posición equilibrada
        'material_total': 39,       # Posición inicial
        'num_pieces': 32,           # Todas las piezas
        'branching_factor': 20,     # Jugadas típicas de apertura
        'self_mobility': 28,        # Movilidad normal
        'opponent_mobility': 28,    # Movilidad normal
        'score_diff': -0.5,         # Jugada que empeora posición
        'move_number': 10,          # Medio juego
        'white_elo': 1600,          # Jugador intermedio
        'black_elo': 1580           # Jugador intermedio
    }

def interactive_prediction():
    """Interfaz interactiva para predicciones"""
    
    print("🎯 PREDICTOR INTERACTIVO DE ERRORES EN AJEDREZ")
    print("=" * 60)
    
    # Cargar predictor
    predictor = ChessErrorPredictor()
    if not predictor.load_model():
        return
    
    print("\n📋 INFORMACIÓN DE FEATURES:")
    feature_info = predictor.get_feature_info()
    for feature, description in feature_info.items():
        print(f"   • {feature}: {description}")
    
    while True:
        print("\n" + "="*60)
        print("🔍 OPCIONES:")
        print("1. 🎲 Probar con jugada de ejemplo")
        print("2. ✏️  Introducir jugada personalizada")
        print("3. 📊 Ver features importantes")
        print("4. 🚪 Salir")
        
        try:
            choice = input("\n🎯 Elige una opción (1-4): ").strip()
            
            if choice == '1':
                # Jugada de ejemplo
                move_data = create_sample_move()
                print("\n🎲 JUGADA DE EJEMPLO:")
                for feature, value in move_data.items():
                    print(f"   {feature}: {value}")
                
                result = predictor.predict_move(move_data)
                if result:
                    display_prediction(result)
            
            elif choice == '2':
                # Jugada personalizada
                print("\n✏️  INTRODUCIR JUGADA PERSONALIZADA:")
                move_data = {}
                
                for feature in predictor.features:
                    while True:
                        try:
                            description = feature_info.get(feature, feature)
                            value_str = input(f"   {feature} ({description}): ").strip()
                            
                            if value_str == "":
                                move_data[feature] = 0  # Valor por defecto
                                break
                            else:
                                move_data[feature] = float(value_str)
                                break
                                
                        except ValueError:
                            print("   ⚠️  Por favor introduce un número válido")
                
                result = predictor.predict_move(move_data)
                if result:
                    display_prediction(result)
            
            elif choice == '3':
                # Mostrar importancia de features
                print("\n📊 IMPORTANCIA DE FEATURES:")
                print("   (Basado en el modelo entrenado)")
                print("   1. score_diff (~89%) - ¡La más importante!")
                print("   2. material_balance (~4%)")
                print("   3. self_mobility (~2%)")
                print("   4. opponent_mobility (~1%)")
                print("   5. Otras features (~4%)")
                print("\n💡 CONSEJOS:")
                print("   • score_diff negativo → mayor probabilidad de error")
                print("   • Material desequilibrado puede indicar problemas")
                print("   • Baja movilidad puede señalar posiciones difíciles")
            
            elif choice == '4':
                print("\n👋 ¡Hasta luego! Gracias por usar el predictor")
                break
            
            else:
                print("   ⚠️  Opción no válida. Elige 1-4.")
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")

def display_prediction(result):
    """Mostrar resultado de predicción"""
    
    prediction = result['prediction']
    confidence = result['confidence']
    probabilities = result['probabilities']
    
    print("\n🔮 RESULTADO DE PREDICCIÓN:")
    print(f"   🎯 Predicción: {prediction}")
    print(f"   📊 Confianza: {confidence:.3f} ({confidence*100:.1f}%)")
    
    # Interpretar resultado
    if prediction == 'good':
        emoji = "✅"
        interpretation = "Jugada buena/normal"
    elif prediction == 'inaccuracy':
        emoji = "⚠️"
        interpretation = "Imprecisión menor"
    elif prediction == 'mistake':
        emoji = "⚠️"
        interpretation = "Error moderado"
    elif prediction == 'blunder':
        emoji = "❌"
        interpretation = "Error grave"
    else:
        emoji = "❓"
        interpretation = "Clasificación desconocida"
    
    print(f"   {emoji} Interpretación: {interpretation}")
    
    # Mostrar todas las probabilidades
    print("\n📈 PROBABILIDADES POR CLASE:")
    sorted_probs = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    for class_name, prob in sorted_probs:
        bar_length = int(prob * 20)  # Barra de 20 caracteres max
        bar = "█" * bar_length + "░" * (20 - bar_length)
        print(f"   {class_name:12} {bar} {prob:.3f} ({prob*100:.1f}%)")
    
    # Dar consejos basados en confianza
    if confidence > 0.9:
        print("\n💡 Alta confianza - La predicción es muy confiable")
    elif confidence > 0.7:
        print("\n💡 Confianza moderada - La predicción es bastante confiable")
    else:
        print("\n⚠️  Baja confianza - La predicción es incierta")

def main():
    """Función principal"""
    
    try:
        interactive_prediction()
    except Exception as e:
        logger.error(f"❌ Error en predicción interactiva: {e}")
        print(f"\n❌ Error inesperado: {e}")
        print("💡 Asegúrate de haber ejecutado simple_predictions.py primero")

if __name__ == "__main__":
    main()
