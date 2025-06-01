from PyQt5.QtCore import QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QLabel,
    QGraphicsColorizeEffect
)

from core.audio_manager import AudioManager
from core.element import Element

audio = AudioManager.instance()


class TileLabel(QLabel):
    HIGHLIGHT_MS = 1000

    def __init__(self, parent, element: Element):
        super().__init__(parent)
        self.element = element
        self.row, self.col = element.x, element.y
        self._drag_origin = None
        self._dragging = False

    def _animate_glow(self):
        eff = QGraphicsColorizeEffect()
        eff.setColor(QColor("yellow"))
        self.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"strength", self)
        anim.setDuration(self.HIGHLIGHT_MS)
        anim.setKeyValueAt(0, 0)
        anim.setKeyValueAt(0.5, 0.8)
        anim.setKeyValueAt(1, 0)
        anim.setEasingCurve(QEasingCurve.InOutQuad)
        anim.finished.connect(lambda: self.setGraphicsEffect(None))
        anim.start(QPropertyAnimation.DeleteWhenStopped)

    def mousePressEvent(self, e):
        audio.play_sound("click")
        self._drag_origin = e.pos()
        self._dragging = False
        self.parent().selected_tile = self
        self._animate_glow()

    def mouseMoveEvent(self, e):
        if not self._drag_origin:
            return
        if (e.pos() - self._drag_origin).manhattanLength() > 10:
            self._dragging = True

    def mouseReleaseEvent(self, e):
        if not self._dragging:
            self._drag_origin = None
            return
        parent = self.parent()
        tgt = parent.childAt(parent.mapFromGlobal(e.globalPos()))
        if isinstance(tgt, TileLabel) and tgt is not self:
            parent.handle_swap_request(self, tgt)
        self._drag_origin = None
        self._dragging = False

    def __repr__(self):
        return (
            f"<TileLabel row={self.row} col={self.col} "
            f"color={self.element.color.name} bonus={self.element.bonus.name}>"
            f"element x={self.element.x} element y={self.element.y}>"
        )

    def __str__(self):
        return self.__repr__()