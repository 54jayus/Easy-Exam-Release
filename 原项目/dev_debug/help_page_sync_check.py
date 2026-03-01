import os
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ui.page.help_page import HelpPage


def main():
    app = QApplication(sys.argv)
    w = HelpPage()
    w.resize(1200, 800)
    w.show()

    def sample(label):
        item = w.toc_tree.currentItem()
        title = item.text(0) if item else ""
        sb = w.content_view.verticalScrollBar()
        print(label, {"toc": title, "scroll": sb.value(), "max": sb.maximum()})

    def run_checks():
        sb = w.content_view.verticalScrollBar()
        sample("initial")
        sb.setValue(0)
        app.processEvents()
        sample("scroll_top")
        sb.setValue(int(sb.maximum() * 0.5))
        app.processEvents()
        sample("scroll_mid")
        sb.setValue(sb.maximum())
        app.processEvents()
        sample("scroll_bottom")
        QTimer.singleShot(200, app.quit)

    QTimer.singleShot(800, run_checks)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

