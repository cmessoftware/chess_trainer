"""
GameUploadService - Service layer for handling PGN and ZIP file uploads
Integrates with existing repository and processing infrastructure
"""

import os
import tempfile
import zipfile
import tarfile
import gzip
import bz2
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import chess.pgn
import shutil
import logging

from modules.pgn_inspector import inspect_pgn_sources_from_zip
from modules.pgn_utils import extract_features_from_game, get_game_hash
from db.repository.games_repository import GamesRepository

logger = logging.getLogger(__name__)

class GameUploadService:
    """Service for handling game file uploads and processing"""
    
    SUPPORTED_EXTENSIONS = [".pgn", ".zip", ".tar", ".gz", ".bz2", ".tgz", ".tar.gz"]
    
    def __init__(self, repository: Optional[GamesRepository] = None):
        self.repository = repository or GamesRepository()
        self.temp_dirs = []
    
    def validate_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate uploaded file and extract metadata"""
        try:
            if not file_path.exists():
                return self._error_result(file_path.name, "File not found")
            
            if file_path.suffix.lower() == '.pgn':
                return self._validate_pgn_file(file_path)
            elif file_path.suffix.lower() in ['.zip', '.tar', '.gz', '.bz2'] or file_path.name.endswith('.tar.gz'):
                return self._validate_compressed_file(file_path)
            else:
                return self._error_result(file_path.name, f"Unsupported file type: {file_path.suffix}")
                
        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            return self._error_result(file_path.name, str(e))
    
    def _validate_pgn_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate a single PGN file"""
        try:
            game_count = 0
            with open(file_path, 'r', encoding='utf-8') as f:
                while True:
                    try:
                        game = chess.pgn.read_game(f)
                        if game is None:
                            break
                        game_count += 1
                    except Exception as e:
                        logger.warning(f"Error reading game {game_count + 1} in {file_path}: {e}")
                        break
            
            return {
                "file_name": file_path.name,
                "file_type": "PGN",
                "file_path": file_path,
                "total_games": game_count,
                "total_pgn_files": 1,
                "status": "valid",
                "message": f"✅ {game_count} partidas válidas encontradas",
                "estimated_import_time_sec": game_count * 0.05,
                "estimated_tactical_analysis_time_sec": game_count * 0.15
            }
        except Exception as e:
            return self._error_result(file_path.name, f"Error reading PGN: {e}")
    
    def _validate_compressed_file(self, file_path: Path) -> Dict[str, Any]:
        """Validate compressed file using existing inspection functionality"""
        try:
            result = inspect_pgn_sources_from_zip(file_path)
            result.update({
                "file_name": file_path.name,
                "file_type": "Compressed",
                "file_path": file_path,
                "status": "valid",
                "message": f"✅ {result['total_games']} partidas en {result['total_pgn_files']} archivos PGN"
            })
            return result
        except Exception as e:
            return self._error_result(file_path.name, f"Error processing compressed file: {e}")
    
    def _error_result(self, file_name: str, error_message: str) -> Dict[str, Any]:
        """Create standardized error result"""
        return {
            "file_name": file_name,
            "file_type": "Error",
            "file_path": None,
            "total_games": 0,
            "total_pgn_files": 0,
            "status": "error",
            "message": f"❌ {error_message}",
            "estimated_import_time_sec": 0,
            "estimated_tactical_analysis_time_sec": 0
        }
    
    def save_uploaded_file(self, uploaded_file, target_dir: Path) -> Path:
        """Save uploaded file to target directory"""
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / uploaded_file.name
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.read())
        
        return file_path
    
    def extract_compressed_file(self, file_path: Path) -> Path:
        """Extract compressed file to temporary directory"""
        temp_dir = Path(tempfile.mkdtemp())
        self.temp_dirs.append(temp_dir)
        
        try:
            if file_path.suffix.lower() == '.zip':
                with zipfile.ZipFile(file_path, 'r') as z:
                    z.extractall(temp_dir)
            elif file_path.suffix.lower() == '.tar' or file_path.name.endswith('.tar.gz'):
                with tarfile.open(file_path, 'r:*') as tar:
                    tar.extractall(temp_dir)
            elif file_path.suffix.lower() == '.gz':
                with gzip.open(file_path, 'rb') as f_in:
                    out_path = temp_dir / file_path.stem
                    with open(out_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            elif file_path.suffix.lower() == '.bz2':
                with bz2.open(file_path, 'rb') as f_in:
                    out_path = temp_dir / file_path.stem
                    with open(out_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
            
            return temp_dir
        except Exception as e:
            logger.error(f"Error extracting {file_path}: {e}")
            raise
    
    def import_pgn_file(self, file_path: Path, source: str = "uploaded") -> Tuple[int, int]:
        """Import games from a single PGN file"""
        imported_count = 0
        duplicate_count = 0
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                while True:
                    try:
                        game = chess.pgn.read_game(f)
                        if game is None:
                            break
                        
                        pgn_str = str(game)
                        game_data = extract_features_from_game(pgn_str)
                        game_data["source"] = source
                        
                        if not self.repository.game_exists(game_data["game_id"]):
                            self.repository.save_game(game_data)
                            imported_count += 1
                        else:
                            duplicate_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Error processing game in {file_path}: {e}")
                        continue
            
            self.repository.commit()
            return imported_count, duplicate_count
            
        except Exception as e:
            logger.error(f"Error importing from {file_path}: {e}")
            raise
    
    def import_file(self, file_validation_result: Dict[str, Any], source: str = "uploaded") -> Dict[str, Any]:
        """Import games from validated file"""
        if file_validation_result["status"] != "valid":
            return {
                "success": False,
                "message": file_validation_result["message"],
                "imported_count": 0,
                "duplicate_count": 0
            }
        
        file_path = file_validation_result["file_path"]
        
        try:
            if file_validation_result["file_type"] == "PGN":
                imported, duplicates = self.import_pgn_file(file_path, source)
                return {
                    "success": True,
                    "message": f"✅ {imported} partidas importadas, {duplicates} duplicadas",
                    "imported_count": imported,
                    "duplicate_count": duplicates
                }
            else:
                # For compressed files, extract and process all PGN files
                return self._import_compressed_file(file_path, source)
                
        except Exception as e:
            logger.error(f"Error importing file {file_path}: {e}")
            return {
                "success": False,
                "message": f"❌ Error durante la importación: {e}",
                "imported_count": 0,
                "duplicate_count": 0
            }
    
    def _import_compressed_file(self, file_path: Path, source: str) -> Dict[str, Any]:
        """Import games from compressed file"""
        try:
            extracted_dir = self.extract_compressed_file(file_path)
            total_imported = 0
            total_duplicates = 0
            
            # Find all PGN files in extracted directory
            pgn_files = list(extracted_dir.rglob("*.pgn"))
            
            if not pgn_files:
                return {
                    "success": False,
                    "message": "❌ No se encontraron archivos PGN en el archivo comprimido",
                    "imported_count": 0,
                    "duplicate_count": 0
                }
            
            for pgn_file in pgn_files:
                imported, duplicates = self.import_pgn_file(pgn_file, source)
                total_imported += imported
                total_duplicates += duplicates
            
            return {
                "success": True,
                "message": f"✅ {total_imported} partidas importadas de {len(pgn_files)} archivos PGN, {total_duplicates} duplicadas",
                "imported_count": total_imported,
                "duplicate_count": total_duplicates
            }
            
        except Exception as e:
            logger.error(f"Error importing compressed file {file_path}: {e}")
            return {
                "success": False,
                "message": f"❌ Error procesando archivo comprimido: {e}",
                "imported_count": 0,
                "duplicate_count": 0
            }
    
    def cleanup(self):
        """Clean up temporary directories"""
        for temp_dir in self.temp_dirs:
            try:
                if temp_dir.exists():
                    shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Error cleaning up temp directory {temp_dir}: {e}")
        
        self.temp_dirs.clear()
    
    def __del__(self):
        """Cleanup on object destruction"""
        self.cleanup()
