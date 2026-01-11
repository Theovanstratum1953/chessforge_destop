from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLabel, QTextEdit, QComboBox, QMessageBox, QDialog,
                             QLineEdit, QDialogButtonBox)
from PyQt6.QtCore import Qt, QTimer
import chess
import chess.svg
from board_widget import InteractiveBoard
from move_display import MoveDisplay
from trainer import RepertoireTrainer


class NewRepertoireDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Repertoire")
        self.setFixedWidth(300)

        layout = QVBoxLayout()
        self.setLayout(layout)

        layout.addWidget(QLabel("Name:"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("e.g. King's Indian Defense")
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Color:"))
        self.color_input = QComboBox()
        self.color_input.addItems(["White", "Black"])
        layout.addWidget(self.color_input)

        layout.addSpacing(10)

        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

    def get_data(self):
        return self.name_input.text(), self.color_input.currentText()


class ChessWindow(QWidget):
    def __init__(self, engine_handler, database):
        super().__init__()
        self.engine_handler = engine_handler
        self.db = database
        self.trainer = RepertoireTrainer(database)
        self.board = chess.Board()
        self.current_repertoire_id = None
        self.is_training = False

        self.redo_stack = []

        self.setWindowTitle("ChessForge")
        self.setGeometry(100, 100, 1100, 700)

        self.main_layout = QHBoxLayout()
        self.setLayout(self.main_layout)

        # --- LEFT: BOARD ---
        self.board_container = QWidget()
        self.board_layout = QVBoxLayout()
        self.board_container.setLayout(self.board_layout)

        self.board_widget = InteractiveBoard(self.board)
        self.board_widget.setMinimumSize(400, 400)
        self.board_widget.move_played.connect(self.on_board_move)

        self.board_layout.addWidget(self.board_widget)

        # NAV BUTTONS
        nav_layout = QHBoxLayout()
        self.btn_nav_start = QPushButton("<<")
        self.btn_nav_back = QPushButton("<")
        self.btn_nav_forward = QPushButton(">")
        self.btn_nav_end = QPushButton(">>")

        nav_style = "font-weight: bold; font-size: 14px; max-width: 50px;"
        for b in [self.btn_nav_start, self.btn_nav_back, self.btn_nav_forward, self.btn_nav_end]:
            b.setStyleSheet(nav_style)
            nav_layout.addWidget(b)

        self.btn_nav_start.clicked.connect(self.go_start)
        self.btn_nav_back.clicked.connect(self.go_back)
        self.btn_nav_forward.clicked.connect(self.go_forward)
        self.btn_nav_end.clicked.connect(self.go_end)

        self.board_layout.addLayout(nav_layout)

        self.status_label = QLabel("Start Position")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.board_layout.addWidget(self.status_label)

        self.main_layout.addWidget(self.board_container, stretch=1)

        # --- MIDDLE: MOVE DISPLAY ---
        self.tree_container = QWidget()
        self.tree_layout = QVBoxLayout()
        self.tree_container.setLayout(self.tree_layout)
        self.tree_container.setFixedWidth(350)

        self.tree_layout.addWidget(QLabel("<b>Opening Notation</b>"))
        self.move_display = MoveDisplay(self.db)
        self.move_display.move_clicked.connect(self.on_move_clicked)
        self.move_display.delete_requested.connect(self.on_delete_move)

        self.tree_layout.addWidget(self.move_display)
        self.main_layout.addWidget(self.tree_container)

        # --- RIGHT: CONTROLS ---
        self.controls_container = QWidget()
        self.controls_layout = QVBoxLayout()
        self.controls_container.setLayout(self.controls_layout)
        self.controls_container.setFixedWidth(250)

        self.controls_layout.addWidget(QLabel("<b>Repertoire:</b>"))
        self.combo_repertoire = QComboBox()
        self.combo_repertoire.currentIndexChanged.connect(self.on_repertoire_changed)
        self.controls_layout.addWidget(self.combo_repertoire)

        self.btn_reset = QPushButton("Reset Board / Start Position")
        self.btn_reset.clicked.connect(self.reset_board)
        self.controls_layout.addWidget(self.btn_reset)

        self.controls_layout.addSpacing(10)

        self.btn_train = QPushButton("Start Training")
        self.btn_train.setCheckable(True)
        self.btn_train.clicked.connect(self.toggle_training)
        self.btn_train.setStyleSheet("background-color: #009c25; font-weight: bold;")
        self.controls_layout.addWidget(self.btn_train)

        self.controls_layout.addSpacing(10)

        self.btn_new_rep = QPushButton("+ New Repertoire")
        self.btn_new_rep.clicked.connect(self.create_repertoire_dialog)
        self.controls_layout.addWidget(self.btn_new_rep)

        self.btn_delete_rep = QPushButton("Delete Repertoire")
        self.btn_delete_rep.clicked.connect(self.delete_current_repertoire)
        self.btn_delete_rep.setStyleSheet("color: #c00;")
        self.controls_layout.addWidget(self.btn_delete_rep)

        self.controls_layout.addSpacing(20)

        self.controls_layout.addWidget(QLabel("<b>Comment:</b>"))
        self.comment_box = QTextEdit()
        self.comment_box.setMaximumHeight(100)
        self.controls_layout.addWidget(self.comment_box)

        self.controls_layout.addSpacing(20)
        self.btn_analyze = QPushButton("Ask Stockfish")
        self.btn_analyze.clicked.connect(self.ask_engine)
        self.controls_layout.addWidget(self.btn_analyze)

        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.controls_layout.addWidget(self.console_output)

        self.main_layout.addWidget(self.controls_container)
        self.board_widget.update_board()

    def initial_load(self):
        self.refresh_repertoires()

    # --- SMART NAVIGATION LOGIC ---
    def go_back(self):
        """Undo last move. If history is lost (due to jump), query DB for parent."""
        if self.board.move_stack:
            # Normal Undo
            move = self.board.pop()
            self.redo_stack.append(move)
            self.board_widget.update_board()
            self.status_label.setText("Step Back")
        elif self.current_repertoire_id:
            # Smart Undo (Database)
            current_fen = self.board.fen()
            parent_fen = self.db.get_parent_fen(self.current_repertoire_id, current_fen)
            if parent_fen:
                self.board.set_fen(parent_fen)
                self.board_widget.update_board()
                self.status_label.setText("Step Back (Jumped)")
                # Clear redo because we jumped
                self.redo_stack.clear()

    def go_forward(self):
        """Redo move OR play next move from Repertoire."""
        if self.redo_stack:
            # Normal Redo
            move = self.redo_stack.pop()
            self.board.push(move)
            self.board_widget.update_board()
            self.status_label.setText(f"Forward: {self.board.san(move)}")
        elif self.current_repertoire_id:
            # Smart Forward (Database)
            current_fen = self.board.fen()
            moves = self.db.get_moves_from_fen(self.current_repertoire_id, current_fen)

            if moves:
                # Play the first move found (Main Line)
                try:
                    move = chess.Move.from_uci(moves[0]['uci'])
                    self.board.push(move)
                    self.board_widget.update_board()
                    self.status_label.setText(f"Forward (Repo): {self.board.san(move)}")
                except:
                    pass

    def go_start(self):
        self.board.reset()
        self.redo_stack.clear()
        self.board_widget.update_board()
        self.status_label.setText("Start Position")

    def go_end(self):
        # Only works for current Redo stack, as "End of Tree" is ambiguous
        while self.redo_stack:
            move = self.redo_stack.pop()
            self.board.push(move)
        self.board_widget.update_board()
        self.status_label.setText("End of Line")

    def set_nav_buttons_enabled(self, enabled):
        self.btn_nav_start.setEnabled(enabled)
        self.btn_nav_back.setEnabled(enabled)
        self.btn_nav_forward.setEnabled(enabled)
        self.btn_nav_end.setEnabled(enabled)

    # ------------------------------

    def create_repertoire_dialog(self):
        dlg = NewRepertoireDialog(self)
        if dlg.exec():
            name, color = dlg.get_data()
            if name:
                self.db.add_repertoire(name, color)
                self.refresh_repertoires()
                self.console_output.append(f"Created: {name} ({color})")

                index = self.combo_repertoire.findText(f"{name} ({color})")
                if index >= 0:
                    self.combo_repertoire.setCurrentIndex(index)

    def reset_board(self):
        self.board.reset()
        self.redo_stack.clear()
        self.board_widget.update_board()
        self.status_label.setText("Start Position")

    def on_delete_move(self, move_id):
        reply = QMessageBox.question(self, "Confirm Delete",
                                     "Delete this move?\n(This will also delete all variations following it)",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_move(move_id)
            self.move_display.update_display(self.current_repertoire_id)
            self.reset_board()
            self.status_label.setText("Move deleted.")

    def delete_current_repertoire(self):
        if not self.current_repertoire_id: return
        name = self.combo_repertoire.currentText()
        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete '{name}'?\nThis will delete all moves in this opening.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_repertoire(self.current_repertoire_id)
            self.refresh_repertoires()
            self.console_output.append(f"Deleted: {name}")

    def toggle_training(self):
        if self.btn_train.isChecked():
            if not self.current_repertoire_id:
                self.btn_train.setChecked(False)
                return
            self.is_training = True
            self.set_nav_buttons_enabled(False)
            self.btn_train.setText("Stop Training")
            self.btn_train.setStyleSheet("background-color: #b34c55; font-weight: bold;")
            self.status_label.setText("Training Mode: Play your moves!")
            self.start_new_training_round()
        else:
            self.is_training = False
            self.set_nav_buttons_enabled(True)
            self.btn_train.setText("Start Training")
            self.btn_train.setStyleSheet("background-color: #009c25; font-weight: bold;")
            self.status_label.setText("Edit Mode")
            self.move_display.update_display(self.current_repertoire_id)

    def start_new_training_round(self):
        self.board.reset()
        self.board_widget.update_board()
        self.move_display.clear()
        rep_text = self.combo_repertoire.currentText()
        color = "White" if "(White)" in rep_text else "Black"
        computer_move = self.trainer.start_session(self.current_repertoire_id, color)
        if computer_move:
            san = self.board.san(computer_move)
            self.board.push(computer_move)
            self.board_widget.update_board()
            self.status_label.setText(f"Opponent played: {san}")
        else:
            self.status_label.setText("Your turn!")

    def on_board_move(self, move):
        self.redo_stack.clear()
        if self.is_training:
            is_correct, comment = self.trainer.check_user_move(self.board, move.uci())
            if is_correct:
                self.board.push(move)
                self.board_widget.update_board()
                self.status_label.setText("Correct!")
                if comment: self.console_output.append(f"Coach: {comment}")
                QTimer.singleShot(600, self.computer_reply_turn)
            else:
                self.status_label.setText("Wrong move! Try again.")
                self.console_output.append("That move is not in your repertoire.")
                self.board_widget.update_board()
        else:
            from_fen = self.board.fen()
            san_move = self.board.san(move)
            self.board.push(move)
            self.board_widget.update_board()
            self.status_label.setText(f"Played: {san_move}")
            comment = self.comment_box.toPlainText()
            self.save_move_to_db(from_fen, self.board.fen(), move.uci(), comment)
            self.move_display.update_display(self.current_repertoire_id)
            self.comment_box.clear()

    def computer_reply_turn(self):
        if not self.is_training: return
        fen = self.board.fen()
        reply = self.trainer.get_computer_move(fen)
        if reply:
            san = self.board.san(reply)
            self.board.push(reply)
            self.board_widget.update_board()
            self.status_label.setText(f"Opponent played: {san}")
        else:
            self.status_label.setText("End of line.")
            QMessageBox.information(self, "Training", "End of variation reached!")
            self.start_new_training_round()

    def on_move_clicked(self, fen):
        if not self.is_training:
            self.board.set_fen(fen)
            self.redo_stack.clear()
            self.board_widget.update_board()
            self.status_label.setText("Jumped to position")

    def save_move_to_db(self, from_fen, to_fen, uci_move, comment):
        if self.current_repertoire_id:
            self.db.add_move(self.current_repertoire_id, from_fen, to_fen, uci_move, comment)
        else:
            self.console_output.append("Moved (Not Saved)")

    def refresh_repertoires(self):
        self.combo_repertoire.blockSignals(True)
        self.combo_repertoire.clear()
        repos = self.db.get_repertoires()
        if not repos:
            self.combo_repertoire.addItem("No Repertoires Found")
            self.current_repertoire_id = None
        else:
            for r in repos:
                self.combo_repertoire.addItem(f"{r['name']} ({r['color']})", r['id'])
            self.current_repertoire_id = self.combo_repertoire.currentData()
        self.combo_repertoire.blockSignals(False)
        self.on_repertoire_changed()

    def on_repertoire_changed(self):
        self.current_repertoire_id = self.combo_repertoire.currentData()
        self.board.reset()
        self.redo_stack.clear()
        if self.current_repertoire_id:
            color = self.db.get_repertoire_color(self.current_repertoire_id)
            self.board_widget.set_orientation(color == "Black")
        else:
            self.board_widget.set_orientation(False)
        self.board_widget.update_board()
        self.status_label.setText("Start Position")
        self.move_display.update_display(self.current_repertoire_id)

    def ask_engine(self):
        self.console_output.append("Thinking...")
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        fen = self.board.fen()
        info = self.engine_handler.get_evaluation(fen)
        if info:
            score = info["score"].white()
            best_move = info.get("pv")[0] if "pv" in info else None
            self.console_output.append(f"Score: {score}")
            self.console_output.append(f"Best: {best_move}")