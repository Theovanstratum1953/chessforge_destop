import chess.engine
import os


class EngineHandler:
    def __init__(self, engine_path):
        self.engine_path = engine_path
        self.engine = None

    def start_engine(self):
        if not os.path.exists(self.engine_path):
            raise FileNotFoundError(f"Engine not found at: {self.engine_path}")

        # Start the process
        try:
            self.engine = chess.engine.SimpleEngine.popen_uci(self.engine_path)

        except Exception as e:
            print(f"Failed to start engine: {e}")
            raise e

    def get_evaluation(self, fen, time_limit=0.1):
        """Returns info about the position (score, best move)."""
        if not self.engine:
            return None

        board = chess.Board(fen)
        # analyse returns a dictionary of info
        info = self.engine.analyse(board, chess.engine.Limit(time=time_limit))
        return info

    def get_best_move(self, fen, time_limit=0.1):
        """Returns just the best move object."""
        if not self.engine:
            return None

        board = chess.Board(fen)
        result = self.engine.play(board, chess.engine.Limit(time=time_limit))
        return result.move

    def stop_engine(self):
        if self.engine:
            self.engine.quit()