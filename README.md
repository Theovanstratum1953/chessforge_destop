# ChessForge

ChessForge is a desktop application designed to help chess players build, manage, and train their opening repertoires. It provides an interactive interface for exploring variations, saving them to a local database, and practicing moves using a built-in trainer.

> **Note:** This project is currently under active development.

## Features

- **Repertoire Management**: Create and organize multiple repertoires for both White and Black.
- **Interactive Board**: Explore positions and play moves on a graphical chessboard.
- **Database Integration**: Automatically save your variations and comments to a local SQLite database.
- **Training Mode**: Practice your repertoire. The trainer will play moves from your repertoire as the opponent and verify your responses.
- **Engine Analysis**: Integrated Stockfish support for real-time position evaluation and best move suggestions.
- **Move Visualization**: Clear display of variations and engine evaluations.

## Prerequisites

Before running ChessForge, ensure you have the following installed:

- **Python 3.8+**
- **PyQt6**: For the graphical user interface.
- **python-chess**: For chess logic and SVG rendering.
- **Stockfish**: A Stockfish binary is included in the `engines/` directory for macOS. For other platforms, you may need to provide a compatible binary.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/ChessRepertoire.git
   cd ChessRepertoire
   ```

2. **Install dependencies**:
   ```bash
   pip install PyQt6 python-chess
   ```

## Usage

### Running the Application

Launch the application by running `main.py`:

```bash
python main.py
```

### Basic Workflow

1. **Create a Repertoire**: Click on the "New Repertoire" button, give it a name, and select your color.
2. **Build your Lines**: Make moves on the board. Each move is saved to your current repertoire. Add comments to specific moves to remember key ideas.
3. **Training**: Toggle "Training Mode" to start a practice session. The app will reset the board and ask you to play the moves for your chosen side. The opponent's moves will be selected randomly from the variations you've saved.
4. **Engine Help**: Use the engine evaluation to find the best moves and understand the objective value of the positions in your repertoire.

## Project Structure

- `main.py`: Entry point of the application.
- `gui.py`: Defines the main window and UI logic.
- `board_widget.py`: Interactive chessboard implementation using PyQt6 and SVG.
- `database.py`: SQLite database handler for repertoires and moves.
- `engine_handler.py`: Interface for communicating with the Stockfish engine.
- `trainer.py`: Logic for the repertoire training mode.
- `move_display.py`: Widget for displaying and navigating move lists.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details (if applicable).

---
*Developed with love for the chess community.*
