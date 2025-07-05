import os
from pathlib import Path
import streamlit as st
import tempfile
from typing import List, Dict, Any, Optional
import dotenv

dotenv.load_dotenv()
PGN_PATH = os.environ.get("PGN_PATH")

class FileUploader:
    """Enhanced file uploader component with multi-format support"""
    
    def __init__(self, pgn_path: str = PGN_PATH):
        self.pgn_path = Path(pgn_path) if pgn_path else Path("data/games")
        self.pgn_path.mkdir(parents=True, exist_ok=True)
    
    def render_basic_uploader(self, label: str = "📂 Subí un archivo", file_types: List[str] = None, content: bool = False):
        """Basic single file uploader (legacy support)"""
        file_types = file_types or ["pgn"]
        uploaded_file = st.file_uploader(label, type=file_types)
        
        if uploaded_file:
            save_path = self.pgn_path / uploaded_file.name
            
            if save_path.exists():
                st.warning(f"⚠️ Ya existe un archivo llamado {uploaded_file.name}. Se sobrescribirá.")
            
            file_bytes = uploaded_file.read()
            with open(save_path, "wb") as f:
                f.write(file_bytes)
            
            st.success(f"✅ Archivo guardado: {save_path}")
            
            if content:
                try:
                    decoded = file_bytes.decode("utf-8")
                    return decoded
                except UnicodeDecodeError:
                    st.error("❌ Error al decodificar el contenido del archivo como UTF-8.")
                    return None
            return file_bytes.decode("utf-8")
    
    def render_enhanced_uploader(self, 
                               label: str = "🎯 Selecciona archivos PGN o comprimidos",
                               file_types: List[str] = None,
                               multiple: bool = True,
                               help_text: str = None) -> List[Any]:
        """Enhanced multi-format file uploader"""
        
        file_types = file_types or ["pgn", "zip", "tar", "gz", "bz2", "tgz"]
        help_text = help_text or "Soporta archivos PGN y formatos comprimidos (ZIP, TAR, GZ, BZ2)"
        
        uploaded_files = st.file_uploader(
            label,
            type=file_types,
            accept_multiple_files=multiple,
            help=help_text
        )
        
        return uploaded_files if multiple else ([uploaded_files] if uploaded_files else [])
    
    def save_temp_files(self, uploaded_files: List[Any]) -> List[Path]:
        """Save uploaded files to temporary locations"""
        temp_files = []
        
        for uploaded_file in uploaded_files:
            temp_dir = Path(tempfile.mkdtemp())
            temp_file = temp_dir / uploaded_file.name
            
            with open(temp_file, "wb") as f:
                f.write(uploaded_file.read())
            
            temp_files.append(temp_file)
        
        return temp_files
    
    def render_upload_summary(self, validation_results: List[Dict[str, Any]]) -> None:
        """Render summary table of uploaded files"""
        if not validation_results:
            return
        
        import pandas as pd
        
        df_display = pd.DataFrame([
            {
                "Archivo": r["file_name"],
                "Tipo": r["file_type"], 
                "PGNs": r.get("total_pgn_files", 0),
                "Partidas": r.get("total_games", 0),
                "Estado": "✅ Válido" if r["status"] == "valid" else "❌ Error",
                "Mensaje": r.get("message", "")
            }
            for r in validation_results
        ])
        
        st.dataframe(df_display, use_container_width=True)
        
        # Summary metrics
        total_files = len(validation_results)
        valid_files = len([r for r in validation_results if r["status"] == "valid"])
        total_games = sum(r.get("total_games", 0) for r in validation_results if r["status"] == "valid")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📁 Archivos válidos", f"{valid_files}/{total_files}")
        with col2:
            st.metric("♟️ Total partidas", total_games)
        with col3:
            estimated_time = total_games * 0.05
            st.metric("⏱️ Tiempo estimado", f"{estimated_time:.1f}s")
        
        return {
            "total_files": total_files,
            "valid_files": valid_files,
            "total_games": total_games,
            "estimated_time": estimated_time
        }
    
    def render_processing_controls(self, 
                                 validation_results: List[Dict[str, Any]],
                                 on_import_callback = None,
                                 on_save_callback = None) -> None:
        """Render processing control buttons"""
        
        valid_results = [r for r in validation_results if r["status"] == "valid"]
        total_games = sum(r.get("total_games", 0) for r in valid_results)
        
        if total_games == 0:
            st.warning("⚠️ No hay archivos válidos para procesar")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Importar a base de datos", type="primary"):
                if on_import_callback:
                    on_import_callback(valid_results)
                else:
                    st.info("Callback de importación no configurado")
        
        with col2:
            if st.button("💾 Solo guardar archivos"):
                if on_save_callback:
                    on_save_callback(valid_results)
                else:
                    self._default_save_files(valid_results)
    
    def _default_save_files(self, validation_results: List[Dict[str, Any]]) -> None:
        """Default file saving implementation"""
        saved_count = 0
        
        for result in validation_results:
            if result["status"] == "valid" and result["file_path"]:
                try:
                    permanent_path = self.pgn_path / result["file_name"]
                    import shutil
                    shutil.copy2(result["file_path"], permanent_path)
                    saved_count += 1
                except Exception as e:
                    st.error(f"Error guardando {result['file_name']}: {e}")
        
        if saved_count > 0:
            st.success(f"✅ {saved_count} archivos guardados en {self.pgn_path}")

# Legacy function for backward compatibility
def upload_file(label: str = "📂 Subí un archivo", type = "pgn", file_path=PGN_PATH, content: bool = False):
    """Legacy upload function - maintained for backward compatibility"""
    uploader = FileUploader(file_path)
    return uploader.render_basic_uploader(label, [type], content)