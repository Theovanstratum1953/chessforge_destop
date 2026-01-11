from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QPainter
from PyQt6.QtCore import pyqtSignal, Qt, QSize, QRectF
import chess
import chess.svg


class InteractiveBoard(QWidget):
    move_played = pyqtSignal(chess.Move)

    def __init__(self, board=None):
        super().__init__()
        self.board = board if board else chess.Board()
        self.selected_square = None
        self.is_flipped = False
        self.setMouseTracking(True)

        # --- NEW: Tell the widget to expand ---
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.renderer = QSvgRenderer()
        self.update_board()

    def set_orientation(self, is_flipped):
        if self.is_flipped != is_flipped:
            self.is_flipped = is_flipped
            self.update_board()

    def sizeHint(self):
        return QSize(400, 400)

    def paintEvent(self, event):
        painter = QPainter(self)

        # Calculate the largest square that fits in the widget
        side = float(min(self.width(), self.height()))

        # Center the board in the widget
        x = (self.width() - side) / 2.0
        y = (self.height() - side) / 2.0

        target_rect = QRectF(x, y, side, side)
        self.renderer.render(painter, target_rect)
        painter.end()

    def update_board(self):
        fill = {}

        if self.board.move_stack:
            last_move = self.board.peek()
            fill[last_move.from_square] = "#ccff00aa"
            fill[last_move.to_square] = "#ccff00aa"

        if self.selected_square is not None:
            fill[self.selected_square] = "#00ffffcc"
            for move in self.board.legal_moves:
                if move.from_square == self.selected_square:
                    fill[move.to_square] = "#ffff0088"

        svg_data = chess.svg.board(
            self.board,
            fill=fill,
            orientation=chess.BLACK if self.is_flipped else chess.WHITE,
            size=400
        ).encode("UTF-8")

        self.renderer.load(svg_data)
        self.update()

    def get_square_from_mouse(self, x, y):
        side = float(min(self.width(), self.height()))
        offset_x = (self.width() - side) / 2.0
        offset_y = (self.height() - side) / 2.0

        rel_x = x - offset_x
        rel_y = y - offset_y

        if rel_x < 0 or rel_x > side or rel_y < 0 or rel_y > side:
            return None

        sq_width = side / 8.0
        sq_height = side / 8.0

        col_idx = int(rel_x // sq_width)
        row_idx = int(rel_y // sq_height)

        if 0 <= col_idx <= 7 and 0 <= row_idx <= 7:
            if self.is_flipped:
                file_idx = 7 - col_idx
                rank_idx = row_idx
            else:
                file_idx = col_idx
                rank_idx = 7 - row_idx

            return chess.square(file_idx, rank_idx)
        return None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            clicked_square = self.get_square_from_mouse(event.pos().x(), event.pos().y())

            if clicked_square is None:
                return

            if self.selected_square is None:
                self.handle_selection(clicked_square)
            else:
                if clicked_square == self.selected_square:
                    self.selected_square = None
                else:
                    success = self.try_move(self.selected_square, clicked_square)
                    if success:
                        self.selected_square = None
                    else:
                        self.handle_selection(clicked_square)

            self.update_board()

    def handle_selection(self, square):
        piece = self.board.piece_at(square)
        if piece and piece.color == self.board.turn:
            self.selected_square = square
        else:
            self.selected_square = None

    def try_move(self, start, end):
        move = chess.Move(start, end)
        piece = self.board.piece_at(start)

        if piece and piece.piece_type == chess.PAWN:
            if (piece.color == chess.WHITE and chess.square_rank(end) == 7) or \
                    (piece.color == chess.BLACK and chess.square_rank(end) == 0):
                move = chess.Move(start, end, promotion=chess.QUEEN)

        if move in self.board.legal_moves:
            self.move_played.emit(move)
            return True
        return False