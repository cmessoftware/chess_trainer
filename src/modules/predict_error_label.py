def assign_tactical_label(row):
    diff = row.get("depth_score_diff", 0)
    mate_threat = row.get("threatens_mate", False)
    forced = row.get("is_forced_move", False)

    if mate_threat and diff >= 100 and not forced:
        return "Brillante"
    elif forced:
        return "Forzada"
    elif diff <= -200:
        return "Blunder"
    elif diff <= -80:
        return "Error"
    elif diff <= -20:
        return "Imprecisa"
    elif diff >= 20:
        return "Excelente"
    else:
        return "Aceptable"
