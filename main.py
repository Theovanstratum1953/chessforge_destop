import sys
import os
import traceback
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from gui import ChessWindow
from engine_handler import EngineHandler
# CRITICAL: We import from your new file
from database import ChessDatabase

# Set up logging to a file
log_path = os.path.join(os.path.expanduser("~"), "chess_forge_debug.log")
logging.basicConfig(
    filename=log_path,
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def get_resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)


def main():
    logging.info("Starting ChessForge")
    app = QApplication(sys.argv)

    try:
        # 1. Engine
        engine_path = get_resource_path(os.path.join("engines", "stockfish"))
        logging.info(f"Engine path: {engine_path}")

        # Ensure executable permissions on macOS/Linux
        if os.path.exists(engine_path) and not os.access(engine_path, os.X_OK):
            logging.info("Setting executable permissions on engine")
            os.chmod(engine_path, 0o755)

        engine = EngineHandler(engine_path)
        try:
            engine.start_engine()
            logging.info("Engine started successfully")
        except Exception as e:
            logging.error(f"Engine Error: {e}")
            logging.error(traceback.format_exc())
            QMessageBox.warning(None, "Engine Error", f"Could not start Stockfish: {e}")

        # 2. Database
        logging.info("Initializing Database...")
        try:
            # --- THE FIX IS HERE ---
            # We call it WITHOUT arguments.
            # This allows the class to use its own logic (Documents/ChessForge).
            db = ChessDatabase()
            logging.info(f"Database connected at: {db.db_path}")

        except Exception as e:
            logging.error(f"Database Error: {e}")
            logging.error(traceback.format_exc())
            QMessageBox.critical(None, "Database Error", f"Could not open database: {e}")
            sys.exit(1)

        # 3. GUI
        try:
            window = ChessWindow(engine, db)
            window.show()
            window.initial_load()
            logging.info("GUI started successfully")
        except Exception as e:
            logging.error(f"GUI Error: {e}")
            logging.error(traceback.format_exc())
            QMessageBox.critical(None, "GUI Error", f"Critical error during GUI startup: {e}")
            sys.exit(1)

        exit_code = app.exec()

        logging.info(f"Exiting with code {exit_code}")
        engine.stop_engine()
        db.close()
        sys.exit(exit_code)

    except Exception as e:
        logging.critical(f"Unexpected error: {e}")
        logging.critical(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()