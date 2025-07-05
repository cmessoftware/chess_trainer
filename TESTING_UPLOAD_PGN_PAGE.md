# Testing Guide: Enhanced Upload PGN Page

## 🧪 How to Test the Upload PGN Page

### Prerequisites

1. **Environment Setup**
```bash
# Ensure you have the necessary dependencies
pip install streamlit chess python-chess pandas
```

2. **Environment Variables**
```bash
# Check that PGN_PATH is set in your .env file
echo $PGN_PATH  # Should point to data/games directory
```

3. **Database Connection**
```bash
# Ensure CHESS_TRAINER_DB_URL is configured
echo $CHESS_TRAINER_DB_URL  # Should be your PostgreSQL connection string
```

---

## 🚀 Running the Upload Page

### Method 1: Direct Streamlit Execution
```bash
# Navigate to the project root
cd c:\Users\sergiosal\source\repos\chess_trainer

# Run the upload page directly
streamlit run src/pages/upload_pgn.py --server.port 8501
```

### Method 2: Through Main App (if available)
```bash
# Run the main Streamlit app
streamlit run app.py

# Navigate to the upload page in the UI
```

### Method 3: Docker Environment
```bash
# Start the Docker containers
.\build_up_clean_all.ps1

# Access the upload page through the containerized app
# URL: http://localhost:8501 (or your configured port)
```

---

## 📝 Test Cases to Execute

### 1. **Single PGN File Upload** ✅

**Test Files Needed:**
```bash
# Create a simple test PGN file
mkdir -p test_data
cat > test_data/test_game.pgn << 'EOF'
[Event "Test Game"]
[Site "Test"]
[Date "2025.07.05"]
[Round "1"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bb5 a6 4. Ba4 Nf6 5. O-O Be7 6. Re1 b5 7. Bb3 d6 8. c3 O-O 9. h3 Nb8 10. d4 Nbd7 1-0
EOF
```

**Steps to Test:**
1. Open the upload page
2. Click "Select files" 
3. Choose the `test_game.pgn` file
4. Verify the file appears in the preview table
5. Check that validation shows "✅ Válido" 
6. Verify game count shows "1"
7. Click "📥 Importar a base de datos"
8. Confirm success message appears

### 2. **Multiple PGN Files Upload** ✅

**Test Files Needed:**
```bash
# Create multiple test PGN files
for i in {1..3}; do
cat > test_data/game_$i.pgn << EOF
[Event "Test Game $i"]
[Site "Test"]
[Date "2025.07.05"]
[Round "$i"]
[White "Player1"]
[Black "Player2"]
[Result "1-0"]

1. e4 e5 2. Nf3 1-0
EOF
done
```

**Steps to Test:**
1. Select all 3 PGN files simultaneously
2. Verify all files appear in preview table
3. Check total game count is correct
4. Test both import and save options

### 3. **ZIP File Upload** ✅

**Test Files Needed:**
```bash
# Create a ZIP file with multiple PGNs
zip test_data/games_collection.zip test_data/*.pgn
```

**Steps to Test:**
1. Upload the ZIP file
2. Verify ZIP is recognized as "Comprimido" type
3. Check that game count extraction works
4. Test the import process

### 4. **Invalid Files Testing** ❌

**Test Files Needed:**
```bash
# Create invalid files for error handling testing
echo "This is not a PGN file" > test_data/invalid.pgn
echo "Random content" > test_data/fake.zip
```

**Steps to Test:**
1. Upload invalid PGN file
2. Verify error message appears
3. Upload corrupted ZIP file
4. Confirm proper error handling

### 5. **Large File Testing** ⚠️

**Test Files Needed:**
```bash
# Create a larger PGN file (optional)
# Download sample PGN from chess databases
curl -o test_data/large_games.pgn "http://www.pgnmentor.com/files.html#players"
```

**Steps to Test:**
1. Upload large PGN file
2. Verify progress tracking works
3. Check time estimation accuracy
4. Confirm memory usage is reasonable

---

## 🔍 Debugging and Troubleshooting

### Common Issues and Solutions

#### **1. Import Errors**
```bash
# If you get module import errors
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
# or
set PYTHONPATH=%PYTHONPATH%;%CD%\src
```

#### **2. Database Connection Issues**
```bash
# Test database connection
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.environ.get('CHESS_TRAINER_DB_URL'))
with engine.connect() as conn:
    print('✅ Database connection successful')
"
```

#### **3. Missing Dependencies**
```bash
# Install missing chess libraries
pip install python-chess chess
```

#### **4. Environment Variables**
```bash
# Check .env file exists and has required variables
cat .env | grep -E "(PGN_PATH|CHESS_TRAINER_DB_URL)"
```

---

## 📊 Expected Test Results

### **Successful Upload Flow:**
1. **File Selection**: File picker shows supported formats
2. **Validation**: Files are analyzed and results shown in table
3. **Preview**: Game counts and file info displayed
4. **Statistics**: Summary metrics (files, games, time estimate)
5. **Processing**: Progress bar during import
6. **Completion**: Success message with import counts

### **UI Elements to Verify:**
- ✅ Multi-format file uploader (pgn, zip, tar, gz, bz2)
- ✅ Preview table with file analysis
- ✅ Summary statistics (files, games, time)
- ✅ Import and save buttons
- ✅ Progress tracking during processing
- ✅ Error messages for invalid files
- ✅ Success confirmations
- ✅ Help sections and documentation

---

## 🧩 Advanced Testing Scenarios

### **1. Stress Testing**
```bash
# Create many small PGN files
for i in {1..50}; do
    echo "[Event \"Game $i\"] [Result \"1-0\"] 1. e4 1-0" > test_data/bulk_$i.pgn
done

# Test bulk upload
zip test_data/bulk_games.zip test_data/bulk_*.pgn
```

### **2. Edge Cases**
- Empty PGN files
- PGN files with special characters
- Very large ZIP files (>100MB)
- Nested ZIP files
- Password-protected ZIP files

### **3. Performance Testing**
- Upload 1000+ games simultaneously
- Monitor memory usage during processing
- Test concurrent user uploads

---

## 📋 Test Checklist

- [ ] **Environment Setup**: All dependencies installed
- [ ] **Single PGN Upload**: File validation and import
- [ ] **Multiple PGN Upload**: Batch processing
- [ ] **ZIP File Upload**: Compression format support
- [ ] **Error Handling**: Invalid file processing
- [ ] **Progress Tracking**: Visual feedback during operations
- [ ] **Database Integration**: Games saved correctly
- [ ] **File Storage**: Alternative save option works
- [ ] **UI Responsiveness**: Smooth user experience
- [ ] **Memory Management**: No memory leaks
- [ ] **Cleanup**: Temporary files removed

---

## 🚀 Quick Test Script

```bash
# Create and run a quick test
mkdir -p test_data

# Generate test PGN
cat > test_data/quick_test.pgn << 'EOF'
[Event "Quick Test"]
[Site "Local"]
[Date "2025.07.05"]
[White "TestPlayer1"]
[Black "TestPlayer2"]
[Result "1-0"]

1. e4 e5 2. Nf3 Nc6 3. Bc4 1-0
EOF

# Run upload page
echo "✅ Test file created: test_data/quick_test.pgn"
echo "🚀 Starting upload page..."
streamlit run src/pages/upload_pgn.py --server.port 8501

# Page will open at: http://localhost:8501
```

**Once the page loads:**
1. Upload the `quick_test.pgn` file
2. Verify it shows "1 partida válida"
3. Click "📥 Importar a base de datos"
4. Confirm success message

This should validate that Issue #74 is working correctly! 🎉
