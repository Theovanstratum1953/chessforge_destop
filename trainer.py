import random
import chess


class RepertoireTrainer:
    def __init__(self, database):
        self.db = database
        self.repertoire_id = None
        self.color = None  # chess.WHITE or chess.BLACK
        self.current_fen = None

    def start_session(self, repertoire_id, color_name):
        """Starts a new training session."""
        self.repertoire_id = repertoire_id
        self.color = chess.WHITE if color_name == "White" else chess.BLACK
        self.current_fen = chess.STARTING_FEN

        # If we are Black, we need the computer to make the first move for White
        if self.color == chess.BLACK:
            return self.get_computer_move(self.current_fen)
        return None

    def check_user_move(self, board, move_uci):
        """
        Verifies if the user's move exists in the repertoire.
        Returns: (is_correct, comment)
        """
        # Look for this specific move in the DB
        moves = self.db.get_moves_from_fen(self.repertoire_id, board.fen())

        for row in moves:
            if row['uci'] == move_uci:
                return True, row['comment']

        return False, "Move not in repertoire."

    def get_computer_move(self, fen):
        """
        Picks a move for the opponent from the database.
        Returns: chess.Move or None (if end of line)
        """
        moves = self.db.get_moves_from_fen(self.repertoire_id, fen)

        if not moves:
            return None

        # Pick a random move from the available variations
        selected_row = random.choice(moves)
        return chess.Move.from_uci(selected_row['uci'])