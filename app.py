import sys
from PyQt5.QtWidgets import QApplication
from GUI.main_window import MainWindow
from core.audio_manager import AudioManager
from logger import logger


def main():
    logger.info("Start app")
    import multiprocessing
    multiprocessing.set_start_method('spawn')

    try:
        audio = AudioManager.instance()
        audio.switch_to_lobby()
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logger.exception("Error while starting")
        sys.exit(1)


if __name__ == "__main__":
    main()
