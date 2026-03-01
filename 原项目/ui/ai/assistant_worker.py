from PyQt5.QtCore import QObject, pyqtSignal


class AssistantWorker(QObject):
    finished = pyqtSignal(str)
    failed = pyqtSignal(str)

    def __init__(self, engine, user_text, attachments, history, ui_context_text=None):
        super().__init__()
        self._engine = engine
        self._user_text = user_text
        self._attachments = attachments
        self._history = history
        self._ui_context_text = ui_context_text

    def run(self):
        try:
            reply = self._engine.generate_reply(
                self._user_text,
                self._attachments,
                self._history,
                ui_context_text=self._ui_context_text,
            )
            self.finished.emit(reply)
        except Exception as e:
            self.failed.emit(str(e))
