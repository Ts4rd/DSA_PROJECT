#  KAYAOT SA IM NGAYAN CHARD!!!
# MAS YAUT KAW RALD !!!

import sqlite3 as sql
import PyQt5.QtWidgets as qtw
import sys
from login import LoginWindow
from register import RegisterWindow
from home import HomePage


class MainWindow:
  def __init__(self):
    self.home_page = None
    self.register_page = None
    self.login_page = None
    self.stack_widget = None
    self.main_window = None

    if self.create_database():
      self.setup_window()

  def setup_window(self):
    self.main_window = qtw.QMainWindow()
    self.main_window.setWindowTitle("Binoang na Window")
    self.main_window.setStyleSheet("background-color: #131621; color: white")
    WIDTH, HEIGHT = 900, 470
    self.main_window.setGeometry(0, 0, WIDTH, HEIGHT)

    self.stack_widget = qtw.QStackedWidget()
    self.login_page = LoginWindow(self.stack_widget).display()
    self.register_page = RegisterWindow(self.stack_widget).display()
    self.home_page = HomePage(self.stack_widget).display()

    # Amo ini an pagkasunod nan mga window, index zero an una mo
    self.stack_widget.addWidget(self.home_page)  # index 2
    # respawn na page pag run ng program
    self.stack_widget.addWidget(self.login_page)  # index 0
    self.stack_widget.addWidget(self.register_page)  # index 1

    self.main_window.setCentralWidget(self.stack_widget)

    self.center_window()
    self.main_window.show()

  def center_window(self):
    # Get the geometry of the main window
    window_geometry = self.main_window.frameGeometry()

    # Get the center point of the screen
    screen_center = qtw.QDesktopWidget().availableGeometry().center()

    # Move the window's top-left point to the correct position
    window_geometry.moveCenter(screen_center)
    self.main_window.move(window_geometry.topLeft())

  @staticmethod
  def create_database():
    database_path = "auth/user_accounts.db"
    conn = sql.connect(database_path)
    cursor = conn.cursor()
    try:
      cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')

      # Commit the transaction and close the connection
      conn.commit()
      return True
    except Exception as e:
      print(e)
      return False
    finally:
      cursor.close()
      conn.close()


def main():
  app = qtw.QApplication(sys.argv)
  root = MainWindow()
  sys.exit(app.exec_())


if __name__ == "__main__":
  main()