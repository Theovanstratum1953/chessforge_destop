import sys
import os
import traceback
import logging
from PyQt6.QtWidgets import QApplication, QMessageBox
from gui import ChessWindow
from engine_handler import EngineHandler
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
            # We continue even if engine fails, but maybe we should show a warning
            QMessageBox.warning(None, "Engine Error", f"Could not start Stockfish: {e}")

        # 2. Database
        # Put database in a writable location (User's home directory)
        db_dir = os.path.join(os.path.expanduser("~"), ".chess_forge")
        os.makedirs(db_dir, exist_ok=True)
        db_path = os.path.join(db_dir, "chess_repertoire.db")
        logging.info(f"Database path: {db_path}")

        # If database doesn't exist in the writable location, copy the bundled one
        if not os.path.exists(db_path):
            bundled_db = get_resource_path("chess_repertoire.db")
            if os.path.exists(bundled_db):
                logging.info(f"Copying bundled database from {bundled_db}")
                import shutil
                shutil.copy2(bundled_db, db_path)
            else:
                logging.info("No bundled database found, a new one will be created.")

        try:
            db = ChessDatabase(db_path)
            logging.info("Database connected successfully")
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