"""Arte de la interfaz de la partida (blender/generar_interfaz.py): los PNG de assets/ajedrez/interfaz/ y sus
medidas (interfaz.json). Lo carga ArtLibrary junto con el resto del arte del ajedrez (nunca el inicio).

Medidas en px de cada PNG, desde arriba a la izquierda: `objeto` = caja del objeto apoyado en la mesa; `visible` =
caja de lo que se ve (alfa >= 50 %); además, para cada objeto, sus rectángulos útiles (papel y renglones de la
planilla, cara de las placas, fieltro de la bandeja, luces del reloj, texto de la tarjeta)."""
import json
from pathlib import Path

from PyQt6.QtGui import QImage

Box = tuple[float, float, float, float]


class InterfaceArt:
    def __init__(self, folder: Path, image_format: QImage.Format):
        data = json.loads((folder / "interfaz.json").read_text(encoding="utf-8"))
        self.info: dict[str, dict] = data["sprites"]
        self.visible: dict[str, Box] = {name: tuple(r["visible"]) for name, r in data["revision"].items()
                                         if "visible" in r}
        self._images: dict[str, QImage] = {}
        for path in sorted(folder.glob("*.png")):
            image = QImage(str(path))
            if image.isNull():
                raise FileNotFoundError(f"No se pudo leer {path}")
            self._images[path.name] = image.convertToFormat(image_format)

    def image(self, name: str) -> QImage:
        return self._images[name if name.endswith(".png") else f"{name}.png"]

    def box(self, key: str, field: str = "objeto") -> Box:
        return tuple(self.info[key][field])

    def __len__(self) -> int:
        return len(self._images)
