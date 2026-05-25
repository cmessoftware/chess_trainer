#!/usr/bin/env python3
"""
AI Chess Coach Pipeline - Installation Test

Tests all components of the AI Coach system to verify installation.

Usage:
    conda activate chess_trainer
    python src/scripts/test_ai_coach_pipeline.py
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_imports():
    """Test that all required libraries are installed."""
    logger.info("🧪 Testing Python imports...")
    
    errors = []
    
    # Test sentence-transformers
    try:
        from sentence_transformers import SentenceTransformer
        logger.info("   ✅ sentence-transformers OK")
    except ImportError as e:
        errors.append(f"sentence-transformers: {e}")
        logger.error(f"   ❌ sentence-transformers FAILED: {e}")
    
    # Test chromadb
    try:
        import chromadb
        logger.info("   ✅ chromadb OK")
    except ImportError as e:
        errors.append(f"chromadb: {e}")
        logger.error(f"   ❌ chromadb FAILED: {e}")
    
    # Test langchain
    try:
        from langchain_ollama import OllamaLLM
        logger.info("   ✅ langchain-ollama OK")
    except ImportError as e:
        errors.append(f"langchain-ollama: {e}")
        logger.error(f"   ❌ langchain-ollama FAILED: {e}")
    
    # Test pypdf2
    try:
        import PyPDF2
        logger.info("   ✅ PyPDF2 OK")
    except ImportError as e:
        errors.append(f"PyPDF2: {e}")
        logger.error(f"   ❌ PyPDF2 FAILED: {e}")
    
    # Test pdfplumber
    try:
        import pdfplumber
        logger.info("   ✅ pdfplumber OK")
    except ImportError as e:
        errors.append(f"pdfplumber: {e}")
        logger.error(f"   ❌ pdfplumber FAILED: {e}")
    
    if errors:
        logger.error(f"\n❌ {len(errors)} import errors found")
        return False
    
    logger.info("\n✅ All imports successful!")
    return True


def test_embedding_model():
    """Test sentence-transformers model loading."""
    logger.info("\n🧪 Testing embedding model...")
    
    try:
        from sentence_transformers import SentenceTransformer
        
        logger.info("   Loading model 'all-MiniLM-L6-v2'...")
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Test encoding
        test_sentence = "This is a test sentence for chess coaching."
        embedding = model.encode(test_sentence)
        
        logger.info(f"   Embedding shape: {embedding.shape}")
        logger.info(f"   ✅ Embedding model working correctly")
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Embedding model failed: {e}")
        return False


def test_vector_database():
    """Test ChromaDB vector database."""
    logger.info("\n🧪 Testing vector database...")
    
    try:
        import chromadb
        from chromadb.config import Settings
        
        # Create temporary in-memory client
        client = chromadb.Client()
        
        # Create test collection
        collection = client.create_collection(
            name="test_collection",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Add test documents
        collection.add(
            documents=["This is a test document about chess tactics."],
            ids=["test_doc_1"]
        )
        
        # Query
        results = collection.query(
            query_texts=["chess tactics"],
            n_results=1
        )
        
        logger.info(f"   Query results: {len(results['ids'][0])} documents")
        logger.info(f"   ✅ Vector database working correctly")
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Vector database failed: {e}")
        return False


def test_ollama_connection():
    """Test connection to Ollama server."""
    logger.info("\n🧪 Testing Ollama connection...")
    
    try:
        import httpx
        
        response = httpx.get("http://localhost:11434", timeout=5.0)
        
        if response.status_code == 200:
            logger.info("   ✅ Ollama server is running")
            
            # List available models
            try:
                from langchain_ollama import OllamaLLM
                
                # Try to initialize with a small model
                llm = OllamaLLM(
                    model="llama3.2:3b",
                    base_url="http://localhost:11434",
                    temperature=0.7
                )
                
                logger.info("   ✅ LLM client initialized successfully")
                return True
                
            except Exception as e:
                logger.warning(f"   ⚠️ LLM client warning: {e}")
                logger.info("   💡 Make sure models are downloaded: ollama pull llama3.2:3b")
                return False
        else:
            logger.error(f"   ❌ Ollama server returned status: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"   ❌ Cannot connect to Ollama: {e}")
        logger.info("   💡 Start Ollama with: ollama serve")
        return False


def test_pdf_processing():
    """Test PDF processing capabilities."""
    logger.info("\n🧪 Testing PDF processing...")
    
    try:
        import PyPDF2
        import pdfplumber
        
        logger.info("   ✅ PDF processing libraries available")
        logger.info("   💡 To test with real PDFs, add chess books to data/chess_books/raw/")
        return True
        
    except Exception as e:
        logger.error(f"   ❌ PDF processing failed: {e}")
        return False


def test_project_structure():
    """Test that required directories exist."""
    logger.info("\n🧪 Testing project structure...")
    
    required_dirs = [
        "src/ai_coach",
        "src/ai_coach/rag",
        "src/ai_coach/llm",
        "src/ai_coach/prompts",
        "data/chess_books",
        "data/vectorstore"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            logger.info(f"   ✅ {dir_path}")
        else:
            logger.warning(f"   ⚠️ Missing: {dir_path}")
            missing_dirs.append(dir_path)
    
    if missing_dirs:
        logger.warning(f"\n   ⚠️ {len(missing_dirs)} directories missing")
        logger.info("   💡 Run: .\\setup_ai_coach.ps1 -CreateStructure")
        return False
    
    logger.info("   ✅ Project structure OK")
    return True


def run_all_tests():
    """Run all installation tests."""
    logger.info("=" * 70)
    logger.info("🤖 AI CHESS COACH - INSTALLATION TEST")
    logger.info("=" * 70)
    
    results = {
        "imports": test_imports(),
        "embedding_model": test_embedding_model(),
        "vector_database": test_vector_database(),
        "ollama": test_ollama_connection(),
        "pdf_processing": test_pdf_processing(),
        "project_structure": test_project_structure()
    }
    
    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"   {test_name.ljust(20)}: {status}")
    
    logger.info(f"\n   Total: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n🎉 All tests passed! AI Coach system is ready.")
        logger.info("\n📚 Next steps:")
        logger.info("   1. Implement src/ai_coach/feature_summarizer.py")
        logger.info("   2. Implement src/ai_coach/rag/chess_rag.py")
        logger.info("   3. Implement src/ai_coach/llm/coaching_llm.py")
        logger.info("   4. See docs/AI_COACH_IMPLEMENTATION_GUIDE.md")
        return True
    else:
        logger.error("\n❌ Some tests failed. Review errors above.")
        logger.info("\n💡 Installation help:")
        logger.info("   - Run: .\\setup_ai_coach.ps1 -InstallAll")
        logger.info("   - Check: docs/AI_COACH_IMPLEMENTATION_GUIDE.md")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
