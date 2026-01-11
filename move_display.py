from PyQt6.QtWidgets import QTextBrowser, QMenu
from PyQt6.QtCore import pyqtSignal, Qt, QUrl
from PyQt6.QtGui import QAction
import chess


class MoveDisplay(QTextBrowser):
    # Signal: Emits FEN when left-clicked
    move_clicked = pyqtSignal(str)
    # Signal: Emits Move ID when right-clicked -> Delete
    delete_requested = pyqtSignal(int)

    def __init__(self, database):
        super().__init__()
        self.db = database
        self.setOpenLinks(False)
        self.anchorClicked.connect(self.on_anchor_clicked)

        self.setStyleSheet("""
            QTextBrowser {
                font-size: 14px;
                line-height: 1.5;
                padding: 10px;
            }
        """)

    def contextMenuEvent(self, event):
        """Handle Right-Click to Delete."""
        pos = event.pos()
        anchor = self.anchorAt(pos)  # Get the URL under mouse

        # Check if the user right-clicked on a move link
        if anchor and anchor.startswith("move:"):
            move_id = int(anchor.split(":")[1])

            menu = QMenu(self)
            delete_action = QAction("Delete this Move (and variations)", self)
            delete_action.triggered.connect(lambda: self.delete_requested.emit(move_id))
            menu.addAction(delete_action)

            menu.exec(event.globalPos())

    def on_anchor_clicked(self, url):
        """Handle Left-Click to Jump."""
        link = url.toString()
        # Newer links use "move:123" format
        if link.startswith("move:"):
            move_id = int(link.split(":")[1])
            fen = self.db.get_move_by_id(move_id)
            if fen:
                self.move_clicked.emit(fen)
        # Fallback for older links (if any exist) that used FEN directly
        else:
            self.move_clicked.emit(link)

    def update_display(self, repertoire_id):
        if not repertoire_id:
            self.clear()
            return

        board = chess.Board()
        html = self._generate_html_recursive(repertoire_id, board, set())

        full_html = f"""
        <html>
        <head>
            <style>
                a {{ text-decoration: none; color: #2b5b84; font-weight: bold; }}
                .comment {{ color: #666; font-style: italic; font-size: 0.9em; }}
                ul {{ margin-top: 5px; margin-bottom: 5px; padding-left: 20px; }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """
        self.setHtml(full_html)

    def _generate_html_recursive(self, repertoire_id, board, visited_fens):
        current_fen = board.fen()
        fen_simple = " ".join(current_fen.split(" ")[:4])

        if fen_simple in visited_fens:
            return " <span style='color:red'>(Loop)</span>"
        visited_fens.add(fen_simple)

        # Ensure database.py is updated to return 'id' in this call!
        moves_data = self.db.get_moves_from_fen(repertoire_id, current_fen)

        if not moves_data:
            visited_fens.remove(fen_simple)
            return ""

        html_out = ""
        is_branching = len(moves_data) > 1

        if is_branching:
            html_out += "<ul>"

        for row in moves_data:
            # We need the ID for the delete logic
            move_id = row['id']
            uci = row['uci']
            comment = row['comment']

            try:
                move = chess.Move.from_uci(uci)
                san = board.san(move)
            except ValueError:
                continue

            move_num = board.fullmove_number
            if board.turn == chess.WHITE:
                move_text = f"{move_num}. {san}"
            else:
                if is_branching or not html_out.strip():
                    move_text = f"{move_num}... {san}"
                else:
                    move_text = san

            # --- KEY CHANGE: Link is now 'move:ID', not 'FEN' ---
            link = f"<a href='move:{move_id}' title='{comment if comment else ''}'>{move_text}</a>"

            comment_span = f" <span class='comment'>{{{comment}}}</span>" if comment else ""

            board.push(move)
            children_html = self._generate_html_recursive(repertoire_id, board, visited_fens)
            board.pop()

            if is_branching:
                html_out += f"<li>{link}{comment_span}{children_html}</li>"
            else:
                html_out += f" {link}{comment_span} {children_html}"

        if is_branching:
            html_out += "</ul>"

        visited_fens.remove(fen_simple)
        return html_out