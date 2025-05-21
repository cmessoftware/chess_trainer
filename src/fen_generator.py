import cv2
import numpy as np
import chess

class ChessboardFENExtractor:
    def __init__(self, image_path):
        """
        Initialize the ChessboardFENExtractor with the path to the chessboard image.
        
        Args:
            image_path (str): Path to the chessboard image file.
        """
        self.image_path = image_path
        self.chessboard_img = None
        self.square_size = 50  # Size of each square after resizing (400x400 board / 8)
        
        # Load and preprocess the image during initialization
        self._load_chessboard()

    def _load_chessboard(self):
        """
        Load and preprocess the chessboard image, detecting the board and resizing it.
        """
        # Load the image
        img = cv2.imread(self.image_path)
        if img is None:
            raise ValueError("Image not found or unable to load.")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply edge detection to find the chessboard
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        
        # Find contours to detect the chessboard
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Find the largest contour (assumed to be the chessboard)
        chessboard_contour = max(contours, key=cv2.contourArea)
        
        # Get the bounding rectangle of the chessboard
        x, y, w, h = cv2.boundingRect(chessboard_contour)
        
        # Crop the image to the chessboard
        chessboard_img = img[y:y+h, x:x+w]
        
        # Resize the chessboard to a standard size (400x400 for 8x8 grid, 50x50 per square)
        self.chessboard_img = cv2.resize(chessboard_img, (400, 400))

    def _split_into_squares(self):
        """
        Split the chessboard into an 8x8 grid of squares.
        
        Returns:
            list: A 2D list of 8x8 squares (each square is an image).
        """
        squares = []
        for row in range(8):
            row_squares = []
            for col in range(8):
                # Extract each square
                square = self.chessboard_img[row * self.square_size:(row + 1) * self.square_size,
                                            col * self.square_size:(col + 1) * self.square_size]
                row_squares.append(square)
            squares.append(row_squares)
        return squares

    def _identify_piece(self, square):
        """
        Identify the chess piece on a given square using basic color thresholding.
        
        Args:
            square (numpy.ndarray): Image of a single square.
        
        Returns:
            str: Piece in the format 'wP' (white pawn), 'bK' (black king), or None if empty.
        """
        # Convert square to grayscale
        gray = cv2.cvtColor(square, cv2.COLOR_BGR2GRAY)
        
        # Calculate the average intensity (to determine if a piece is present)
        avg_intensity = np.mean(gray)
        
        # If the square is mostly empty (background), return None
        if 100 < avg_intensity < 150:  # Adjust these thresholds based on your image
            return None
        
        # Convert to HSV for color detection (to distinguish white vs black pieces)
        hsv = cv2.cvtColor(square, cv2.COLOR_BGR2HSV)
        avg_hue = np.mean(hsv[:, :, 0])
        
        # Check for piece type (simplified: we’ll use pixel patterns or shapes)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        white_pixels = np.sum(binary == 255)
        
        # Determine if the piece is white or black based on hue
        piece_color = 'w' if avg_hue < 100 else 'b'  # Adjust hue threshold as needed
        
        # Determine piece type based on white pixel count (simplified)
        if white_pixels > 1000:
            piece_type = 'K'  # King
        elif white_pixels > 800:
            piece_type = 'Q'  # Queen
        elif white_pixels > 600:
            piece_type = 'B'  # Bishop
        elif white_pixels > 400:
            piece_type = 'N'  # Knight
        else:
            piece_type = 'P'  # Pawn
        
        return piece_color + piece_type

    def _board_to_fen(self, squares):
        """
        Convert the board state (squares) to FEN notation.
        
        Args:
            squares (list): A 2D list of 8x8 squares.
        
        Returns:
            str: FEN string representing the board state.
        """
        board = []
        
        # Process each rank (row) from 8 to 1
        for row in range(8):
            rank = []
            empty_count = 0
            for col in range(8):
                piece = self._identify_piece(squares[row][col])
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count > 0:
                        rank.append(str(empty_count))
                        empty_count = 0
                    # Convert piece to FEN notation (e.g., 'wK' -> 'K', 'bK' -> 'k')
                    fen_piece = piece[1].upper() if piece[0] == 'w' else piece[1].lower()
                    rank.append(fen_piece)
            if empty_count > 0:
                rank.append(str(empty_count))
            board.append(''.join(rank))
        
        # Join ranks with '/' for FEN
        fen_board = '/'.join(board)
        
        # Add remaining FEN components (simplified assumptions)
        fen = f"{fen_board} w - - 0 1"
        return fen

    def get_fen(self):
        """
        Extract the FEN from the chessboard image.
        
        Returns:
            str: FEN string representing the board state.
        
        Raises:
            ValueError: If the FEN is invalid or the image cannot be processed.
        """
        # Split the chessboard into squares
        squares = self._split_into_squares()
        
        # Convert to FEN
        fen = self._board_to_fen(squares)
        
        # Validate the FEN
        try:
            chess.Board(fen)
        except ValueError as e:
            raise ValueError(f"Invalid FEN generated: {fen}. Error: {str(e)}")
        
        return fen

# Example usage
if __name__ == "__main__":
    image_path = "../img/chessboard.png"  # Replace with your image path
    try:
        extractor = ChessboardFENExtractor(image_path)
        fen = extractor.get_fen()
        print("Generated FEN:", fen)
    except Exception as e:
        print("Error:", str(e))