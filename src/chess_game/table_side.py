"""Todo lo que está apoyado en la mesa alrededor del tablero (reemplaza al panel lateral): carteles, reloj,
planilla, bandejas de capturadas, placas-botón y la tarjeta de fin de partida. Ubica cada objeto según la
disposición (`table_layout`) y junta sus sombras para hornearlas en el fondo de la mesa."""
import chess
from PyQt6.QtCore import QObject, QRectF, pyqtSignal
from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QWidget

from src.chess_game.art_library import ArtLibrary
from src.chess_game.brass_button import PRIMARY, SECONDARY, BrassButton
from src.chess_game.chess_clock import ChessClock
from src.chess_game.material import balance, lost_pieces
from src.chess_game.result_card import ResultCard
from src.chess_game.score_sheet import ScoreSheet
from src.chess_game.table_layout import TableLayout
from src.chess_game.table_plates import CapturedTray, NamePlate
from src.chess_game.table_sprites import UiSprites
from src.common.theme import TABLE_LOOK


class TableSide(QObject):
    undo_requested = pyqtSignal()
    new_game_requested = pyqtSignal()
    back_requested = pyqtSignal()

    def __init__(self, table: QWidget, sprites: UiSprites, art: ArtLibrary):
        super().__init__(table)
        self.rival_plate, self.own_plate = NamePlate(sprites, table), NamePlate(sprites, table)
        self.clock = ChessClock(sprites, table)
        self.sheet = ScoreSheet(sprites, table)
        self.tray_rival = CapturedTray(sprites, art, table)
        self.tray_own = CapturedTray(sprites, art, table, from_bottom=True)  # del lado del jugador
        self.new_game_button = BrassButton("Nueva partida", PRIMARY, sprites, table)
        self.undo_button = BrassButton("Deshacer", SECONDARY, sprites, table)
        self.back_button = BrassButton("Menú", SECONDARY, sprites, table)
        self.card = ResultCard(sprites, table)
        for button, signal in ((self.new_game_button, self.new_game_requested),
                               (self.undo_button, self.undo_requested), (self.back_button, self.back_requested)):
            button.clicked.connect(signal.emit)
        self.status_text = ""
        self.player = chess.WHITE

    @property
    def objects(self) -> list:
        """Los objetos con sombra en la mesa (la tarjeta lleva la suya)."""
        return [self.tray_rival, self.tray_own, self.rival_plate, self.clock, self.sheet, self.own_plate,
                self.new_game_button, self.undo_button, self.back_button]

    def place(self, layout: TableLayout) -> None:
        s = layout.s
        for widget, rect in ((self.tray_rival, layout.tray_rival), (self.tray_own, layout.tray_own),
                             (self.rival_plate, layout.rival_plate), (self.clock, layout.clock),
                             (self.sheet, layout.sheet), (self.own_plate, layout.own_plate),
                             (self.new_game_button, layout.primary), (self.undo_button, layout.secondary[0]),
                             (self.back_button, layout.secondary[1])):
            widget.place(rect, s)
        card = QRectF(0, 0, TABLE_LOOK.card_w * s, TABLE_LOOK.card_h * s)
        card.moveCenter(layout.sheet.center())
        self.card.place(card, s)

    def shadow_layers(self) -> list[tuple[QImage, QRectF]]:
        return [layer for widget in self.objects for layer in widget.shadow_layers()]

    # --- estado de la partida ------------------------------------------------------------------------------------
    def set_info(self, rival: str, player: chess.Color) -> None:
        self.player = player
        self.rival_plate.set_text(rival)
        self.own_plate.set_text(f"Vos · {'Blancas' if player == chess.WHITE else 'Negras'}")

    def set_status(self, text: str) -> None:
        """Para lectores de pantalla y tooltip del reloj (el estado se ve en el reloj y en la tarjeta)."""
        self.status_text = text
        self.clock.setToolTip(text)
        self.clock.setAccessibleDescription(text)

    def set_moves(self, sans: list[str]) -> None:
        self.sheet.set_moves(sans)

    @property
    def move_texts(self) -> list[str]:
        return list(self.sheet.moves)

    def set_board(self, board: chess.Board) -> None:
        """Capturadas de cada lado y quién va adelante en material."""
        ahead = balance(board, self.player)
        self.tray_rival.set_pieces(lost_pieces(board, self.player), max(0, -ahead))
        self.tray_own.set_pieces(lost_pieces(board, not self.player), max(0, ahead))

    def show_card(self, headline: str, text: str) -> None:
        self.card.show_card(headline, text)

    def hide_card(self) -> None:
        self.card.hide()
