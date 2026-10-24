"""Diálogo "Acerca de": versión, licencia, créditos y (si hay enlaces) donaciones. Vidrio oscuro como el resto de los
avisos (GlassDialog); se abre con el enlace discreto del inicio o con F1 en cualquier pantalla. Esc cierra."""
from html import escape

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import QLabel, QLayout, QWidget

from src.common import app_info, paths
from src.common.glass_dialog import GlassDialog
from src.common.theme import COLORS, px

WIDTH = 460  # unidades


def link(text: str, url: str) -> str:
    return f'<a href="{escape(url)}" style="color: {COLORS.accent}; text-decoration: none;">{escape(text)}</a>'


def license_html() -> str:
    text = (f"Software libre bajo la licencia {link(app_info.LICENSE_NAME, app_info.LICENSE_URL)}: podés usarlo, "
            "estudiarlo, modificarlo y compartirlo.")
    if app_info.SOURCE_URL:
        text += f" {link('Código fuente', app_info.SOURCE_URL)}."
    return text


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " y " + items[-1]


def credits_html() -> str:
    """Un renglón por rol; la licencia una sola vez si todos los del rol la comparten."""
    roles: dict[str, list] = {}
    for credit in app_info.CREDITS:
        roles.setdefault(credit.role, []).append(credit)
    rows = []
    for role, credits in roles.items():
        if len({c.license for c in credits}) == 1:
            names = _join([link(c.name, c.url) for c in credits]) + f" · {escape(credits[0].license)}"
        else:
            names = _join([f"{link(c.name, c.url)} · {escape(c.license)}" for c in credits])
        rows.append(f"{escape(role)}: {names}")
    rows.append("Arte del ajedrez: renders propios en Blender")
    return "<br>".join(rows)


def donations_html() -> str | None:
    links = app_info.donation_links()
    if not links:
        return None
    return "Es gratis. Si te gusta, podés invitarme un café: " + " · ".join(link(n, u) for n, u in links)


class AboutDialog(GlassDialog):
    def __init__(self, parent: QWidget, u: float):
        super().__init__(parent, u, app_info.APP_NAME)
        self.version = self.add_label(f"Versión {app_info.VERSION} · © {app_info.AUTHOR}")
        self.license = self._rich(license_html())
        self.add_label("Créditos", "dialogHeading")
        self.credits = self._rich(credits_html())
        donations = donations_html()
        self.donations = self._rich(donations) if donations else None
        self.licenses_button, self.close_button = self.add_buttons(("Ver licencias", False), ("Cerrar", True))
        self.licenses_button.clicked.connect(self.open_licenses)
        self.close_button.clicked.connect(self.accept)
        self.close_button.setDefault(True)

    def _rich(self, html: str) -> QLabel:
        label = self.add_label(html)
        label.setTextFormat(Qt.TextFormat.RichText)
        label.setOpenExternalLinks(True)
        return label

    def showEvent(self, event) -> None:
        """Ancho fijo y el alto que piden los textos a ese ancho (con SetMinimumSize los párrafos largos se
        cortaban: el layout calcula el alto para otro ancho)."""
        self.ensurePolished()
        width = px(WIDTH, self.u)
        self.layout().setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.setFixedSize(width, self.layout().totalHeightForWidth(width))
        super().showEvent(event)

    @staticmethod
    def open_licenses() -> None:
        """La carpeta con LICENSE, CREDITS.md y las licencias de cada componente."""
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(paths.licenses_dir())))


def show_about(parent: QWidget, u: float) -> AboutDialog:
    dialog = AboutDialog(parent, u)
    dialog.open()
    return dialog
