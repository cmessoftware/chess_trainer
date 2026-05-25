# Chess Diagram Recognition - Technical Analysis

**Last Updated:** March 14, 2026  
**Status:** Future Enhancement (Phase 10)  
**Priority:** LOW - Deferred until MVP validation

---

## Executive Summary

**Current Implementation:**
- ✅ OCR extracts **text** from chess books (moves, annotations, explanations)
- ❌ Chess board **diagrams are NOT processed** (remain as images)
- ❌ No FEN generation from visual board positions

**Business Impact:**
- **Text-based RAG covers ~95% of chess knowledge** needed for coaching
- Algebraic notation allows position reconstruction for analysis
- Diagram recognition would enable position-based search ("find this position in my books")

**Recommendation:** 
- Launch AI Coach with text-only RAG
- Monitor user demand for diagram search
- Implement if feature proves valuable (measured user requests)

---

## Problem Statement

### What We Have
```
[PDF Page]
├── Text content ✅ EXTRACTED
│   ├── "In the Italian Game, after 1.e4 e5 2.Nf3 Nc6 3.Bc4..."
│   ├── "Black should consider 3...Bc5 or 3...Nf6"
│   └── Variations with algebraic notation
│
└── Chess Diagram ❌ NOT EXTRACTED
    ┌─────────────┐
    │ ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜ │
    │ ♟ ♟ ♟ ♟ . ♟ ♟ ♟ │
    │ . . ♞ . . . . . │
    │ . . ♗ . ♟ . . . │
    │ . . . . ♙ . . . │
    │ . . . . . ♘ . . │
    │ ♙ ♙ ♙ ♙ . ♙ ♙ ♙ │
    │ ♖ ♘ ♗ ♕ ♔ . . ♖ │
    └─────────────┘
```

### What We Want
```python
# Extract FEN from diagram above
fen = "r1bqkbnr/pppp1ppp/2n5/2B1p3/4P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 3 3"

# Index in ChromaDB
chunk = {
    "text": "In the Italian Game, after 1.e4 e5 2.Nf3 Nc6 3.Bc4...",
    "position": fen,
    "source": "Modern Chess Openings 15th Edition",
    "page": 142
}
```

### Use Cases
1. **Position Search:** "Find this position in my books"
2. **Exercise Extraction:** Convert book puzzles to interactive exercises
3. **Position Index:** Search by FEN across all books
4. **Diagram Context:** Link text explanations to exact positions

---

## Technical Approaches

### Option A: Computer Vision (Open Source)

#### Tech Stack
```python
# Required libraries
import cv2                          # OpenCV for image processing
import numpy as np                  # Array operations
import tensorflow as tf             # Deep learning
from PIL import Image
from pdf2image import convert_from_path
```

#### Implementation Steps

**1. Detect Chess Board in Page**
```python
def detect_chess_board(page_image):
    """
    Find chess diagram using edge detection and pattern matching
    """
    # Convert to grayscale
    gray = cv2.cvtColor(page_image, cv2.COLOR_BGR2GRAY)
    
    # Edge detection
    edges = cv2.Canny(gray, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    # Filter for square-like shapes
    for contour in contours:
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
        
        # Chess board should be roughly square with 4 corners
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = w / float(h)
            
            # Square aspect ratio (0.9 - 1.1)
            if 0.9 <= aspect_ratio <= 1.1:
                return extract_board(page_image, x, y, w, h)
    
    return None
```

**2. Extract 8×8 Grid**
```python
def extract_squares(board_image):
    """
    Divide board into 64 squares
    """
    h, w = board_image.shape[:2]
    square_h = h // 8
    square_w = w // 8
    
    squares = []
    for row in range(8):
        for col in range(8):
            x1 = col * square_w
            y1 = row * square_h
            x2 = x1 + square_w
            y2 = y1 + square_h
            
            square = board_image[y1:y2, x1:x2]
            squares.append(square)
    
    return squares
```

**3. Classify Pieces with CNN**
```python
# Train CNN model with labeled chess piece images
# Classes: wp, wn, wb, wr, wq, wk, bp, bn, bb, br, bq, bk, empty

def classify_piece(square_image, model):
    """
    Predict piece on square using trained CNN
    """
    # Preprocess
    img = cv2.resize(square_image, (64, 64))
    img = img / 255.0  # Normalize
    img = np.expand_dims(img, axis=0)
    
    # Predict
    prediction = model.predict(img)
    piece_class = np.argmax(prediction)
    
    # Map to piece notation
    pieces = ['wp', 'wn', 'wb', 'wr', 'wq', 'wk', 
              'bp', 'bn', 'bb', 'br', 'bq', 'bk', None]
    
    return pieces[piece_class]
```

**4. Generate FEN**
```python
def board_to_fen(piece_matrix):
    """
    Convert 8×8 piece matrix to FEN string
    """
    fen_rows = []
    
    for row in piece_matrix:
        empty_count = 0
        fen_row = ""
        
        for piece in row:
            if piece is None:
                empty_count += 1
            else:
                if empty_count > 0:
                    fen_row += str(empty_count)
                    empty_count = 0
                fen_row += piece_to_fen_char(piece)
        
        if empty_count > 0:
            fen_row += str(empty_count)
        
        fen_rows.append(fen_row)
    
    # Join rows with '/' and add game state
    board_fen = "/".join(fen_rows)
    
    # Default game state (would need OCR or heuristics)
    return f"{board_fen} w KQkq - 0 1"
```

#### Existing Libraries

**1. tensorflow-chessbot**
- GitHub: https://github.com/Elucidation/tensorflow_chessbot
- Trained CNN for piece recognition
- Supports multiple board styles
- **Status:** Active but requires retraining for book-specific styles

**2. chessboard-finder (OpenCV)**
- GitHub: https://github.com/kvedala/chessboard-finder
- Robust board detection
- Handles perspective transforms
- **Limitation:** Needs clear grid lines

**3. chess-board-recognition**
- End-to-end pipeline
- Board detection + Piece classification + FEN generation
- **Limitation:** Training data quality critical

#### Challenges

| Challenge                 | Impact                                         | Mitigation                                          |
| ------------------------- | ---------------------------------------------- | --------------------------------------------------- |
| **Varied Diagram Styles** | Different books use different piece graphics   | Train/fine-tune CNN on book-specific samples        |
| **Partial Boards**        | Some diagrams show only part of board          | Add validation for 8×8 grid detection               |
| **Figurine Notation**     | Some books use symbols (♔♕) instead of letters | Dual detection mode (symbols + images)              |
| **Rotated Boards**        | Black's perspective diagrams                   | Perspective transform + board orientation detection |
| **False Positives**       | Detecting non-chess grids as boards            | Add chess-specific pattern validation               |
| **Training Data**         | Need labeled chess piece images                | Manual labeling (~500-1000 samples) or augmentation |

#### Development Effort
- **Research & Setup:** 16-24 hours
- **Board Detection:** 20-30 hours
- **CNN Training:** 30-40 hours
- **FEN Generation:** 10-15 hours
- **Integration & Testing:** 20-30 hours
- **Total:** **96-139 hours** (~12-17 days full-time)

---

### Option B: Chessify API (Commercial Service)

#### Service Overview
- **Provider:** Chessify (https://chessify.me)
- **Product:** Board Recognition API
- **Technology:** Proprietary computer vision
- **Quality:** Commercial-grade accuracy

#### API Integration

**Endpoint:**
```
POST https://api.chessify.me/v1/board-recognition
```

**Python Implementation:**
```python
import requests
from pdf2image import convert_from_path
import io

class ChessifyDiagramExtractor:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.chessify.me/v1"
    
    def extract_diagrams_from_pdf(self, pdf_path: str) -> list:
        """
        Extract all chess diagrams from PDF
        """
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=300)
        
        diagrams = []
        for page_num, image in enumerate(images, 1):
            # Convert PIL Image to bytes
            img_bytes = io.BytesIO()
            image.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            # Call Chessify API
            response = requests.post(
                f"{self.base_url}/board-recognition",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "image/png"
                },
                data=img_bytes.read()
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Check if board detected
                if result.get("board_detected"):
                    diagrams.append({
                        "page": page_num,
                        "fen": result["fen"],
                        "confidence": result.get("confidence", 1.0),
                        "bounding_box": result.get("board_location")
                    })
        
        return diagrams
    
    def process_all_books(self, raw_books_dir: str) -> dict:
        """
        Process entire library
        """
        from pathlib import Path
        
        results = {}
        pdf_files = list(Path(raw_books_dir).glob("**/*.pdf"))
        
        for pdf_path in pdf_files:
            print(f"Processing {pdf_path.name}...")
            diagrams = self.extract_diagrams_from_pdf(str(pdf_path))
            results[pdf_path.stem] = diagrams
        
        return results
```

**Usage:**
```python
# Initialize extractor
extractor = ChessifyDiagramExtractor(api_key="your_api_key")

# Process single book
diagrams = extractor.extract_diagrams_from_pdf("data/chess_books/raw/MCO-15.pdf")

# Output
# [
#   {"page": 42, "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"},
#   {"page": 43, "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3"},
#   ...
# ]
```

#### Pricing Analysis

**Cost Estimation (as of 2026 - verify current rates):**
- Assumption: ~50 diagrams per book average
- 66 books × 50 diagrams = **3,300 diagrams**

| Tier              | Price/Image | Total Cost (3,300 images) |
| ----------------- | ----------- | ------------------------- |
| Pay-as-you-go     | $0.10       | $330                      |
| Bulk Plan (1000+) | $0.05       | $165                      |
| Enterprise        | Custom      | Contact sales             |

**One-Time vs Ongoing:**
- Initial library processing: **One-time cost**
- New books added: Incremental cost
- Re-processing (if needed): Additional cost

**ROI Calculation:**
```
Developer Time (CV Approach): 100 hours × $50/hr = $5,000
Chessify API Cost: $165-$330
Savings: $4,670-$4,835 (30-33x cheaper)
Time to Production: Days vs Weeks
```

#### Advantages
✅ **Fast Integration:** 8-16 hours vs 100+ hours  
✅ **Proven Accuracy:** Commercial-grade recognition  
✅ **Multi-Style Support:** Handles varying book formats  
✅ **No Training Required:** API pre-trained  
✅ **Scalable:** Process 66 books efficiently  
✅ **Maintenance-Free:** No model updates needed  

#### Disadvantages
❌ **Ongoing Cost:** Pay per image processed  
❌ **External Dependency:** Requires internet + API availability  
❌ **Vendor Lock-In:** Tied to Chessify service  
❌ **Privacy:** Sending book images to third party  
❌ **Rate Limits:** API quotas may apply  

#### Security Considerations
- Books are copyrighted material (fair use for personal analysis)
- Ensure Chessify terms allow book processing
- Consider data residency/privacy policies

---

### Option C: Hybrid Approach

**Strategy:** Selective automation based on value

#### Implementation
```python
class HybridDiagramExtractor:
    def __init__(self, chessify_api_key: str = None):
        self.chessify = ChessifyDiagramExtractor(chessify_api_key) if chessify_api_key else None
        self.manual_annotations = self.load_manual_annotations()
    
    def extract_positions(self, book_name: str, pdf_path: str) -> list:
        """
        Use best method based on book priority
        """
        # High-priority books → Chessify API
        if book_name in HIGH_PRIORITY_BOOKS and self.chessify:
            return self.chessify.extract_diagrams_from_pdf(pdf_path)
        
        # Manual annotations → Load from file
        elif book_name in self.manual_annotations:
            return self.manual_annotations[book_name]
        
        # Low-priority → Skip diagrams, text only
        else:
            return []
    
    def load_manual_annotations(self) -> dict:
        """
        Load manually curated critical positions
        """
        # Example: data/chess_books/manual_positions.json
        # {
        #   "Modern Chess Openings 15th Edition": [
        #     {"page": 42, "fen": "...", "description": "Italian Game main line"}
        #   ]
        # }
        pass
```

**Prioritization:**
```python
HIGH_PRIORITY_BOOKS = [
    "kupdf.net_modern-chess-openings-15th-edition",  # MCO-15: Critical reference
    "fundamental-chess-endings_compress",             # Endgame bible
    "my-system-21st-century-edition-aaron-nimzowitsch"  # Strategic classic
]

MANUAL_ANNOTATION_BOOKS = [
    # Critical positions manually noted during reading
]

TEXT_ONLY_BOOKS = [
    # Everything else - text extraction sufficient
]
```

**Cost Optimization:**
- High-priority (3 books × 50 diagrams = 150) × $0.10 = **$15**
- Manual (20 critical positions) × 0 = **$0** (human time: ~2 hours)
- Total: **$15 + 2 hours** instead of $330 or 100 development hours

---

## Decision Matrix

| Criterion               | CV (Open Source) | Chessify API | Hybrid    | Text-Only (Current) |
| ----------------------- | ---------------- | ------------ | --------- | ------------------- |
| **Development Cost**    | $5,000 (100h)    | $0           | $100 (2h) | $0                  |
| **Processing Cost**     | $0               | $165-$330    | $15       | $0                  |
| **Time to Production**  | 2-3 weeks        | 2-3 days     | 1 week    | Now                 |
| **Accuracy**            | 85-95%           | 98-99%       | 95-99%    | N/A                 |
| **Maintenance**         | High             | None         | Low       | None                |
| **Scalability**         | Good             | Excellent    | Moderate  | Excellent           |
| **Total Cost (Year 1)** | $5,000           | $165-$330    | $115      | $0                  |

## Recommendation

### Phase 1: Launch with Text-Only RAG ✅
**Status:** Current implementation  
**Coverage:** ~95% of chess knowledge  
**Cost:** $0  
**Rationale:** Text + algebraic notation sufficient for coaching

### Phase 2: Monitor User Demand 📊
**Metrics to Track:**
- User requests for "find this position"
- Queries about specific board diagrams
- Complaints about missing visual context

**Decision Threshold:**
- If >10% of users request diagram search → proceed to Phase 3
- If <5% request → defer indefinitely

### Phase 3: Pilot with Hybrid Approach 🚀
**If Justified:**
1. Use Chessify API for 3 high-priority books ($15)
2. Manually annotate 20 critical positions (2 hours)
3. Measure feature engagement
4. Calculate diagram search usage

### Phase 4: Scale Based on ROI 📈
**If Pilot Succeeds:**
- **High engagement + low cost tolerance:** Full Chessify API ($330)
- **High engagement + budget constraints:** CV development (100h)
- **Low engagement:** Maintain hybrid approach

---

## Implementation Roadmap

### If Implementing (Future)

#### Milestone 1: Proof of Concept (Week 1)
- [ ] Test Chessify API with 10 sample pages
- [ ] Measure accuracy on book-specific diagrams
- [ ] Validate FEN extraction quality
- [ ] Calculate cost per book

#### Milestone 2: Integration (Week 2)
- [ ] Create `DiagramExtractor` class
- [ ] Integrate with `PDFProcessor`
- [ ] Store FENs in ChromaDB with context
- [ ] Update chunking to include position metadata

#### Milestone 3: Search Enhancement (Week 3)
- [ ] Add position-based search endpoint
- [ ] Create UI for "find similar positions"
- [ ] Implement FEN query parsing
- [ ] Add position visualization

#### Milestone 4: Validation (Week 4)
- [ ] User testing with diagram search
- [ ] Accuracy validation on sample sets
- [ ] Performance benchmarking
- [ ] Cost analysis and optimization

---

## Conclusion

**Current Status:** Not prioritized (Phase 10)

**Key Insights:**
1. **Text-based RAG is 95% sufficient** for AI Chess Coach MVP
2. **Chessify API is most cost-effective** if feature needed ($165 vs $5,000)
3. **Hybrid approach minimizes risk** with $15 pilot
4. **User demand should drive decision** (data-driven prioritization)

**Next Steps:**
1. ✅ Complete text-only RAG system (in progress)
2. ✅ Launch AI Coach MVP
3. 📊 Measure user feedback on missing diagrams
4. 🚀 Implement if justified by demand

**Documentation Updates:**
- Roadmap: Phase 10 added
- This document: Comprehensive analysis complete
- Decision deferred to post-launch metrics

---

**References:**
- Chessify API: https://chessify.me/api
- tensorflow-chessbot: https://github.com/Elucidation/tensorflow_chessbot
- chessboard-finder: https://github.com/kvedala/chessboard-finder
- OpenCV Tutorials: https://docs.opencv.org/4.x/d9/df8/tutorial_root.html
