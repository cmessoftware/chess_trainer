#!/usr/bin/env python3
"""
Script para reparar features con error_label NULL
Regenera SOLO los movimientos que actualmente tienen error_label NULL
"""
import sys
import os
from pathlib import Path

# Agregar src al path
current_dir = Path(__file__).parent
src_dir = current_dir / "src"
sys.path.append(str(src_dir))

from db.session import get_session
from db.models.features import Features  
from db.models.games import Games
import chess.pgn
from io import StringIO

def repair_null_error_labels():
    """Reparar features con error_label NULL"""
    session = get_session()
    
    try:
        print("🔧 REPARANDO FEATURES CON ERROR_LABEL NULL")
        print("=" * 60)
        
        # Encontrar features con NULL error_label de Th3Hound
        null_features = session.query(Features).join(
            Games, Features.game_id == Games.game_id
        ).filter(
            (Games.white_player.ilike('%th3%')) | 
            (Games.black_player.ilike('%th3%')),
            Features.error_label.is_(None)
        ).all()
        
        print(f"📊 Features con error_label NULL: {len(null_features)}")
        
        if len(null_features) == 0:
            print("✅ No hay features NULL para reparar")
            return
        
        print("🎯 CLASIFICANDO JUGADAS NORMALES...")
        
        repaired_count = 0
        batch_size = 100
        
        for i, feature in enumerate(null_features):
            # Clasificar jugada basada en score_diff y contexto
            error_label = classify_normal_move(feature)
            
            # Actualizar en base de datos
            feature.error_label = error_label
            repaired_count += 1
            
            # Commit en lotes
            if repaired_count % batch_size == 0:
                session.commit()
                print(f"   📝 Reparadas: {repaired_count}/{len(null_features)}")
        
        # Commit final
        session.commit()
        print(f"✅ REPARACIÓN COMPLETADA: {repaired_count} features asignadas")
        
        # Mostrar nueva distribución
        show_new_distribution(session)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()

def classify_normal_move(feature):
    """
    Clasificar jugada normal basada en score_diff y contexto
    
    Lógica para ML:
    - excellent: Jugadas muy precisas (score_diff <= 10)
    - good: Jugadas normales sin error significativo (score_diff <= 25) 
    - inaccuracy: Error menor (score_diff <= 50)
    - mistake: Error medio (score_diff <= 150)  
    - blunder: Error grave (score_diff > 150)
    """
    score_diff = abs(feature.score_diff or 0)
    move_number = feature.move_number or 1
    
    # Jugadas de apertura (primeros 12 movimientos)
    if move_number <= 12:
        if score_diff <= 15:
            return "book"  # Teoría de apertura
        elif score_diff <= 30:
            return "good"  # Apertura razonable
        else:
            return "inaccuracy"  # Error temprano
    
    # Jugadas de medio juego y final
    if score_diff <= 10:
        return "excellent"  # Jugada muy precisa
    elif score_diff <= 25:
        return "good"      # Jugada normal, sin errores
    elif score_diff <= 50:
        return "inaccuracy"  # Error menor
    elif score_diff <= 150:
        return "mistake"     # Error medio
    else:
        return "blunder"     # Error grave

def show_new_distribution(session):
    """Mostrar nueva distribución de error_labels"""
    print("\n📊 NUEVA DISTRIBUCIÓN DE ERROR_LABELS:")
    
    # Contar por tipo para Th3Hound
    th3_features = session.query(Features).join(
        Games, Features.game_id == Games.game_id
    ).filter(
        (Games.white_player.ilike('%th3%')) | 
        (Games.black_player.ilike('%th3%'))
    ).all()
    
    error_counts = {}
    total = len(th3_features)
    
    for feature in th3_features:
        label = feature.error_label or "NULL"
        error_counts[label] = error_counts.get(label, 0) + 1
    
    print(f"   📈 Total features: {total}")
    for label, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total) * 100
        print(f"   📋 {label}: {count} ({percentage:.1f}%)")

def get_move_context_info(feature):
    """Obtener información contextual del movimiento (futuro enhancement)"""
    # TODO: Analizar si es captura, jaque, jugada forzada, etc.
    # Esto requeriría reconstruir la posición FEN
    return {
        'is_capture': False,
        'is_check': False, 
        'is_forced': False,
        'legal_moves_count': None
    }

if __name__ == "__main__":
    repair_null_error_labels()