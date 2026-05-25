import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import asyncio
from pathlib import Path


class LogService:
    """Servicio para manejo de logs del sistema"""

    def __init__(self):
        # Por ahora usaremos un almacenamiento en memoria simple
        # En producción debería usar una base de datos o sistema de logs robusto
        self._logs = []
        self._next_id = 1

        # Configurar logging a archivo también
        self._setup_file_logging()

    def _setup_file_logging(self):
        """Configurar logging a archivo"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Logger específico para eventos de chess
        self.chess_logger = logging.getLogger("chess_events")
        if not self.chess_logger.handlers:
            handler = logging.FileHandler(log_dir / "chess_events.log")
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            self.chess_logger.addHandler(handler)
            self.chess_logger.setLevel(logging.INFO)

    async def log_event(
        self,
        module: str,
        action: str,
        user_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Registrar un evento en el sistema

        Args:
            module: Módulo del sistema (chess, games, analysis, etc.)
            action: Acción realizada (board_move, game_load, etc.)
            user_id: ID del usuario que realizó la acción
            data: Datos adicionales del evento

        Returns:
            Dict con información del log creado
        """
        try:
            timestamp = datetime.now().isoformat()

            log_entry = {
                "id": self._next_id,
                "module": module,
                "action": action,
                "user_id": user_id,
                "data": data or {},
                "timestamp": timestamp,
            }

            # Agregar a memoria
            self._logs.append(log_entry)
            self._next_id += 1

            # Log específico por módulo
            log_message = (
                f"{user_id} - {action} - {json.dumps(data) if data else 'No data'}"
            )

            if module == "chess":
                self.chess_logger.info(log_message)
            else:
                logging.info(f"[{module.upper()}] {log_message}")

            return log_entry

        except Exception as e:
            logging.error(f"Error creando log entry: {e}")
            raise

    async def get_logs(
        self,
        module: Optional[str] = None,
        action: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Obtener logs filtrados

        Args:
            module: Filtrar por módulo
            action: Filtrar por acción
            user_id: Filtrar por usuario
            limit: Número máximo de resultados
            offset: Desplazamiento para paginación

        Returns:
            Dict con logs y metadata de paginación
        """
        try:
            # Filtrar logs
            filtered_logs = self._logs.copy()

            if module:
                filtered_logs = [
                    log for log in filtered_logs if log["module"] == module
                ]

            if action:
                filtered_logs = [
                    log for log in filtered_logs if log["action"] == action
                ]

            if user_id:
                filtered_logs = [
                    log for log in filtered_logs if log["user_id"] == user_id
                ]

            # Ordenar por timestamp descendente (más recientes primero)
            filtered_logs.sort(key=lambda x: x["timestamp"], reverse=True)

            # Paginación
            total = len(filtered_logs)
            paginated_logs = filtered_logs[offset : offset + limit]

            return {
                "logs": paginated_logs,
                "total": total,
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logging.error(f"Error obteniendo logs: {e}")
            raise

    async def get_log_stats(self) -> Dict[str, Any]:
        """
        Obtener estadísticas de logs

        Returns:
            Dict con estadísticas de uso por módulo y acción
        """
        try:
            stats = {
                "total_events": len(self._logs),
                "modules": {},
                "actions": {},
                "users": {},
            }

            for log in self._logs:
                # Estadísticas por módulo
                module = log["module"]
                if module not in stats["modules"]:
                    stats["modules"][module] = 0
                stats["modules"][module] += 1

                # Estadísticas por acción
                action = log["action"]
                if action not in stats["actions"]:
                    stats["actions"][action] = 0
                stats["actions"][action] += 1

                # Estadísticas por usuario
                user_id = log["user_id"]
                if user_id and user_id not in stats["users"]:
                    stats["users"][user_id] = 0
                if user_id:
                    stats["users"][user_id] += 1

            return stats

        except Exception as e:
            logging.error(f"Error obteniendo estadísticas: {e}")
            raise

    async def clear_logs(self, module: Optional[str] = None) -> int:
        """
        Limpiar logs (solo para admin/testing)

        Args:
            module: Si se especifica, solo limpia logs de ese módulo

        Returns:
            Número de logs eliminados
        """
        try:
            if module:
                original_count = len(self._logs)
                self._logs = [log for log in self._logs if log["module"] != module]
                removed_count = original_count - len(self._logs)
            else:
                removed_count = len(self._logs)
                self._logs = []
                self._next_id = 1

            logging.info(f"Logs limpiados: {removed_count} entradas")
            return removed_count

        except Exception as e:
            logging.error(f"Error limpiando logs: {e}")
            raise
