from PyQt6 import QtWidgets 
import sys
import pyautogui
pyautogui.FAILSAFE = False
from gui import Ui_Buscador

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Buscador = QtWidgets.QWidget()
    ui = Ui_Buscador()
    ui.setupUi(Buscador)
    Buscador.show()
    sys.exit(app.exec())