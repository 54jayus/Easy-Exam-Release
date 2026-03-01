import os
import sys

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from ui.main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1200, 800)
    w.show()

    def sample(label):
        hp = w.help_page
        item = hp.toc_tree.currentItem()
        title = item.text(0) if item else ""
        sb = hp.content_view.verticalScrollBar()
        print(label, {"toc": title, "scroll": sb.value(), "max": sb.maximum()})

    def after_switch():
        sample("after_switch")
        hp = w.help_page
        sb = hp.content_view.verticalScrollBar()
        sb.setValue(int(sb.maximum() * 0.5))
        app.processEvents()
        sample("scroll_mid")
        sb.setValue(sb.maximum())
        app.processEvents()
        sample("scroll_bottom")
        QTimer.singleShot(200, app.quit)

    def switch_to_help():
        w.switch_page(4)
        QTimer.singleShot(1200, after_switch)

    QTimer.singleShot(400, switch_to_help)
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

