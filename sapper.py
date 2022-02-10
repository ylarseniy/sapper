from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QInputDialog, qApp
from PyQt5.QtWidgets import QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtWidgets, QtMultimedia
from PyQt5.QtGui import QPixmap, QFont, QIcon, QColor, QPainter, QPicture
from random import randint, choice
from itertools import cycle
import numpy as np
import sqlite3
import sys


class Sapper(QMainWindow):
    EXIT_CODE_RESTART = 2147283647

    def __init__(self):
        super().__init__()
        self.time = 0
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.on_time)
        self.mines_position = set()
        self.iter_mines = None
        self.mine_timer = QtCore.QTimer()
        self.mine_timer.timeout.connect(self.mine_on_time)
        self.cell_sounds_isPlaced = False
        self.field_x, self.field_y = 0, 0
        self.gameOver = False
        self.firstStep = True
        self.player_name = 'Unknown'
        self.initSize()
        self.getPlayername()
        self.openedCells = 0
        self.canDraw = False
        self.number_of_mines = round(self.field_x * self.field_y * 0.15)
        self.matrix = list()
        self.textColors = {1: '#0008ff', 2: '#22ff00', 3: '#ff002a', 4: '#e600ff',
                           5: '#ff9100', 6: '#00f7ff', 7: '#e1ff00', 8: 'black', 0: 'white'}
        self.grass_light = 'background-color: #9ecc41;'
        self.grass_dark = 'background-color: #7faf21;'
        self.field_light = 'background-color: #e5c29f;'
        self.field_dark = 'background-color: #d7b899;'
        
        self.loadImages()
        
        self.loadSounds()
        self.initUI()
        self.initField()

        self.audioPlayers = []
        self.audioPlayers_for_cells = []
        for i in range(3):
            audioplayer = QtMultimedia.QMediaPlayer()
            self.audioPlayers.append(audioplayer)
            audioplayer = QtMultimedia.QMediaPlayer()
            audioplayer.setMedia(self.cell_sounds[i])
            self.audioPlayers_for_cells.append(audioplayer)
        self.audioPlayers = cycle(self.audioPlayers)

        self.matrix = np.asarray(self.matrix).reshape(self.field_y, self.field_x)
        self.con = sqlite3.connect('results.db')
        self.resultsTable = MyTableWidget(self)

    def loadImages(self):
        self.flag_pic = QPixmap('images\\flag.png')
        self.watch_pic = QPixmap('images\\watch.png')
        self.lose_pic = QPixmap('images\\lose_screen.png')
        self.win_pic = QPixmap('images\\win_screen.png')
        self.db_pic = QPixmap('images\\db.png')
        self.restart_pic = QPixmap('images\\restart.png')

    def loadSounds(self):
        self.cell_sounds = []
        self.cell_sounds.append(QtMultimedia.QMediaContent(
                                QtCore.QUrl.fromLocalFile('sounds\\cell.mp3')))
        self.cell_sounds.append(QtMultimedia.QMediaContent(
                                QtCore.QUrl.fromLocalFile('sounds\\cell_2.mp3')))
        self.cell_sounds.append(QtMultimedia.QMediaContent(
                                QtCore.QUrl.fromLocalFile('sounds\\cell_3.mp3')))

        self.bomb_sounds = []
        self.bomb_sounds.append(QtMultimedia.QMediaContent(
                                QtCore.QUrl.fromLocalFile('sounds\\bomb.mp3')))
        self.bomb_sounds.append(QtMultimedia.QMediaContent(
                                QtCore.QUrl.fromLocalFile('sounds\\bomb_2.mp3')))
        self.bomb_sounds.append(QtMultimedia.QMediaContent(
                                QtCore.QUrl.fromLocalFile('sounds\\bomb_3.mp3')))
        self.bomb_sounds.append(QtMultimedia.QMediaContent(
                                QtCore.QUrl.fromLocalFile('sounds\\bomb_4.mp3')))

        self.flag_placed_sound = QtMultimedia.QMediaContent(
                                    QtCore.QUrl.fromLocalFile('sounds\\flag_placed.mp3'))

        self.flag_removed_sound = QtMultimedia.QMediaContent(
                                    QtCore.QUrl.fromLocalFile('sounds\\flag_removed.mp3'))

        self.defeat_sound = QtMultimedia.QMediaContent(
                                        QtCore.QUrl.fromLocalFile('sounds\\defeat.mp3'))
        self.victory_sound = QtMultimedia.QMediaContent(
                                        QtCore.QUrl.fromLocalFile('sounds\\victory.mp3'))

    def initUI(self):
        self.setWindowTitle('Сапёр')
        self.setWindowIcon(QIcon(self.flag_pic))
        self.setMaximumSize(self.field_x * 40, self.field_y * 40 + 40)
        self.setMinimumSize(self.field_x * 40, self.field_y * 40 + 40)

        self.bottom_background_label = QLabel(self)
        self.bottom_background_label.resize(self.field_x * 40, 40)
        self.bottom_background_label.move(0, int(self.field_y * 40))
        self.bottom_background_label.setStyleSheet('background-color: #176f33')

        self.flags_left_image = QLabel(self)
        self.flags_left_image.setPixmap(self.flag_pic)
        self.flags_left_image.move(10, int(self.field_y * 40 + 5))

        self.watch_image = QLabel(self)
        self.watch_image.resize(30, 36)
        self.watch_image.setPixmap(self.watch_pic)
        self.watch_image.move(120, int(self.field_y * 40 + 3))

        self.universal_font = QFont('Source Serif Pro Black')
        self.universal_font.setPointSize(18)

        self.gameTimer = QLabel(self)
        self.gameTimer.setFont(self.universal_font)
        self.gameTimer.setText('0')
        self.gameTimer.setStyleSheet('color: white')
        self.gameTimer.move(160, int(self.field_y * 40 + 5))

        self.flags_count = self.number_of_mines
        self.flags_left_count = QLabel(self)
        self.flags_left_count.setFont(self.universal_font)
        self.flags_left_count.setText(str(self.flags_count))
        self.flags_left_count.setStyleSheet('color: white')
        self.flags_left_count.move(45, int(self.field_y * 40 + 5))

        self.results_screen_label = QLabel(self)

        self.time_label_layout = QtWidgets.QHBoxLayout(self.results_screen_label)
        self.time_label_layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.time_label = QLabel(self.results_screen_label)
        self.time_label.hide()
        self.time_label.setFont(self.universal_font)
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet('color: white')
        self.time_label.move(int(85 - self.time_label.width() / 2), 90)

        self.best_time_label_layout = QtWidgets.QHBoxLayout(self.results_screen_label)
        self.best_time_label_layout.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.best_time_label = QLabel(self.results_screen_label)
        self.best_time_label.hide()
        self.best_time_label.setFont(self.universal_font)
        self.best_time_label.setAlignment(Qt.AlignCenter)
        self.best_time_label.setStyleSheet('color: white')
        self.best_time_label.move(int(216 - self.best_time_label.width() / 2), 90)

        self.db_label = QLabel(self)
        self.db_label.resize(30, 34)
        self.db_label.setPixmap(self.db_pic)
        self.db_label.move(int(self.field_x * 40 - 36), int(self.field_y * 40 + 3))

        self.restart_label = QLabel(self)
        self.restart_label.resize(30, 30)
        self.restart_label.setPixmap(self.restart_pic)
        self.restart_label.move(int(self.field_x * 40 - 76), int(self.field_y * 40 + 5))

    def mousePressEvent(self, event):
        x, y, btn = event.x(), event.y(), event.button()
        if x in range(self.field_x * 40 + 1) and y in range(self.field_y * 40 + 1):
            if not self.gameOver:
                cell = self.matrix[y // 40][x // 40]
                if btn == 2 and not cell.isOpen:
                    self.updateFlags(cell)
                elif btn == 1 and not cell.pixmap():
                    if self.firstStep:
                        self.firstStep = False
                        while len(self.mines_position) < self.number_of_mines:
                            mine_x = randint(0, self.field_x - 1)
                            mine_y = randint(0, self.field_y - 1)
                            target = self.matrix[mine_y][mine_x]
                            if target not in self.mines_position and target != cell:
                                self.mines_position.add(target)
                                target.isMine = True
                        self.timer.start(1000)
                    self.doStep(cell)

        elif x in range(self.db_label.x(), self.db_label.x() + 34) and (
                    y in range(self.db_label.y(), self.db_label.y() + 30)):
            self.showDatabase()

        elif x in range(self.restart_label.x(), self.restart_label.x() + 30) and (
                    y in range(self.restart_label.y(), self.restart_label.y() + 30)):
            self.con.close()
            for i in range(10):
                next(self.audioPlayers).stop()
            self.resultsTable.close()
            qApp.exit(self.EXIT_CODE_RESTART)

    def showDatabase(self):
        self.resultsTable.loadTable()
        self.resultsTable.show()

    def on_time(self):
        self.time += 1
        self.gameTimer.setText(str(self.time))

    def mine_on_time(self):
        self.show_mines()

    def updateFlags(self, cell):
        if cell.pixmap():
            cell.clear()
            self.flags_count += 1
            self.flags_left_count.setText(str(self.flags_count))
            self.playAudio(self.flag_removed_sound)
        elif self.flags_count:
            cell.setPixmap(self.flag_pic)
            self.flags_count -= 1
            self.flags_left_count.setText(str(self.flags_count))
            self.playAudio(self.flag_placed_sound)

    def playAudio(self, audio, is_cell=False):
        if is_cell:
            audioplayer = choice(self.audioPlayers_for_cells)
            audioplayer.play()
        else:
            audioplayer = next(self.audioPlayers)
            audioplayer.setMedia(choice(audio) if type(audio) == list else audio)
            audioplayer.play()

    def doStep(self, cell, checked=None):
        if not cell.isOpen:
            if cell.pixmap():
                cell.clear()
                self.flags_count += 1
                self.flags_left_count.setText(str(self.flags_count))
            if cell.isMine:
                self.timer.stop()
                self.gameOver = True
                self.show_mines(cell)
            else:
                if not checked:
                    checked = []
                mines_around = 0
                neighbors = set()
                x, y = cell.X, cell.Y
                for Y in range(y - 1 if y else y, y + 2 if y + 1 < self.field_y else y + 1):
                    for X in range(x - 1 if x else x, x + 2 if x + 1 < self.field_x else x + 1):
                            if self.matrix[Y][X].isMine:
                                mines_around += 1
                            else:
                                if self.matrix[Y][X] not in checked:
                                    if x == X and y == Y:
                                        continue
                                    else:
                                        neighbors.add(self.matrix[Y][X])
                if mines_around:
                    self.playAudio(self.cell_sounds, is_cell=True)
                    self.openedCells += 1
                    cell.isOpen = True
                    cell.setText(str(mines_around))
                    cell.setFont(self.universal_font)
                    self.paintCell(cell, mines_around)
                else:
                    self.openedCells += 1
                    cell.isOpen = True
                    self.paintCell(cell, mines_around)
                    for element in neighbors:
                        if element not in checked:
                            checked.append(element)
                            self.doStep(element, checked)

        if not self.gameOver and self.field_x * self.field_y ==\
                self.openedCells + self.number_of_mines:
            self.timer.stop()
            self.gameOver = True
            self.results_screen(True)
            self.resultsTable.loadTable()

    def drawMine(self, cell):
        r, g, b = randint(0, 255), randint(0, 255), randint(0, 255)
        center_color = QColor(int(r * 0.7), int(g * 0.7), int(b * 0.7))
        cell.setStyleSheet(F'background-color: {QColor(r, g, b).name()}')
        self.canDraw = True
        self.paintEvent(cell, center_color)

    def show_mines(self, cell=None):
        if not self.iter_mines:
            self.mine_timer.start(200)
            self.mines_position.remove(cell)
            lst = list(self.mines_position)
            self.iter_mines = iter(lst)
            self.drawMine(cell)
            self.playAudio(self.bomb_sounds)
        else:
            try:
                self.drawMine(next(self.iter_mines))
                self.playAudio(self.bomb_sounds)
            except StopIteration:
                self.mine_timer.stop()
                self.results_screen(False)

    def paintEvent(self, cell, center_color=0):
        if self.canDraw:
            picture = QPicture()
            painter = QPainter()
            painter.begin(picture)
            painter.setBrush(center_color)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(0, 0, 20, 20)
            painter.end()
            cell.setPicture(picture)
            self.canDraw = False

    def paintCell(self, cell, mines_around):
        field_color = self.field_light if '#9ecc41' in cell.styleSheet() else self.field_dark
        cell.setStyleSheet(F'color: {self.textColors[mines_around]}; {field_color}')

    def initSize(self):
        while True:
            text, okBtnPressed = QInputDialog.getText(self, "Выбор размера",
                                                      'Введите размер поля в формате "X Y"\n'
                                                      "Не меньше, чем 8")
            if not okBtnPressed:
                sys.exit()
            try:
                size = text.split()
                x, y = size[0].strip(), size[1].strip()
                if int(x) >= 8 and int(y) >= 8:
                    self.field_x = int(x)
                    self.field_y = int(y)
                    break
            except Exception as e:
                pass
        self.resize(self.field_x * 40, self.field_y * 40)

    def getPlayername(self):
        player_name = QInputDialog.getText(self, "Ввод имени", 'Введите Ваше имя')
        if player_name[0]:
            self.player_name = player_name[0]

    def initField(self):
        for y in range(self.field_y):
            for x in range(self.field_x):
                label = QtWidgets.QLabel(self)
                label.setMinimumSize(40, 40)
                label.setMaximumSize(40, 40)
                label.setText("")
                label.setObjectName(F"label_{x}_{y}")
                label.setAlignment(QtCore.Qt.AlignCenter)
                label.move(int(40 * x), int(40 * y))
                label.setStyleSheet(self.grass_light if (x % 2 and y % 2) or
                                                        (not x % 2 and not y % 2)
                                    else self.grass_dark)
                label.isOpen = False
                label.isMine = False
                label.X = x
                label.Y = y
                self.matrix.append(label)

    def results_screen(self, result=True):
        if result:
            audioplayer = next(self.audioPlayers)
            playlist = QtMultimedia.QMediaPlaylist(audioplayer)
            playlist.addMedia(self.victory_sound)
            playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.Loop)
            audioplayer.setPlaylist(playlist)
            audioplayer.play()

            self.results_screen_label.resize(self.win_pic.size())
            self.results_screen_label.setPixmap(self.win_pic)

            self.time_label.show()
            self.time_label.setText(str(self.time))

            self.best_time_label.show()

            cur = self.con.cursor()
            if (self.player_name,) in cur.execute('SELECT player FROM results').fetchall():
                queue = F"""SELECT field_width, field_height FROM results
                            WHERE player = '{self.player_name}'"""
                if (self.field_x, self.field_y) in cur.execute(queue):
                    conditions = F""" WHERE player = '{self.player_name}'
                                 and field_width = {self.field_x}
                                 and field_height = {self.field_y}"""
                    queue = F"""UPDATE results
                                SET last_time = {self.time}""" + conditions
                    cur.execute(queue)
                    best_time = min(self.time, cur.execute(F"""SELECT best_time FROM results""" +
                                                           conditions).fetchall()[0][0])
                    queue = F"""UPDATE results
                                SET best_time = {best_time}""" + conditions
                    self.best_time_label.setText(str(best_time))
                else:
                    queue = F"""INSERT INTO results('player', 'last_time', 'best_time',
                                                    'field_width', 'field_height')
                                VALUES{self.player_name, self.time, self.time,
                                       self.field_x, self.field_y}"""
                    self.best_time_label.setText(str(self.time))
            else:
                queue = F"""INSERT INTO results('player', 'last_time', 'best_time',
                                                'field_width', 'field_height')
                            VALUES{self.player_name, self.time, self.time,
                                   self.field_x, self.field_y}"""
                self.best_time_label.setText(str(self.time))
            cur.execute(queue)
            cur.close()
            self.con.commit()
        else:
            audioplayer = next(self.audioPlayers)
            playlist = QtMultimedia.QMediaPlaylist(audioplayer)
            playlist.addMedia(self.defeat_sound)
            playlist.setPlaybackMode(QtMultimedia.QMediaPlaylist.Loop)
            audioplayer.setPlaylist(playlist)
            audioplayer.play()

            self.results_screen_label.resize(self.lose_pic.size())
            self.results_screen_label.setPixmap(self.lose_pic)
        screen_x, screen_y = self.results_screen_label.width(), self.results_screen_label.height()
        self.results_screen_label.move(int(self.field_x * 40 / 2 - screen_x / 2),
                                       int(self.field_y * 40 / 2 - screen_y / 2))
        self.results_screen_label.raise_()

    def closeEvent(self, event):
        self.con.close()
        event.accept()


class MyTableWidget(QMainWindow):
    def __init__(self, parent=None):
        super(MyTableWidget, self).__init__(parent)
        self.initUI()
        self.sapper = parent

    def initUI(self):
        self.resize(640, 400)
        self.setWindowTitle('Результаты')
        self.centralwidget = QtWidgets.QWidget(self)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.tableWidget = QtWidgets.QTableWidget(self.centralwidget)
        self.tableWidget.setColumnCount(6)
        self.verticalLayout.addWidget(self.tableWidget)
        self.setCentralWidget(self.centralwidget)

        self.tableWidget.setHorizontalHeaderItem(0, QTableWidgetItem('id'))
        self.tableWidget.setHorizontalHeaderItem(1, QTableWidgetItem('player'))
        self.tableWidget.setHorizontalHeaderItem(2, QTableWidgetItem('last_time'))
        self.tableWidget.setHorizontalHeaderItem(3, QTableWidgetItem('best_time'))
        self.tableWidget.setHorizontalHeaderItem(4, QTableWidgetItem('field_width'))
        self.tableWidget.setHorizontalHeaderItem(5, QTableWidgetItem('field_height'))
        self.tableWidget.horizontalHeader().setStretchLastSection(True)

    def loadTable(self):
        results = self.sapper.con.cursor().execute("SELECT * FROM results").fetchall()
        if results:
            self.tableWidget.setRowCount(len(results))
            for y in range(len(results)):
                for x in range(6):
                    element = results[y][x]
                    item = QTableWidgetItem()
                    item.setData(Qt.EditRole, element)
                    self.tableWidget.setItem(y, x, item)


def excepthook(exctype, value, traceback):
    sys.__excepthook__(exctype, value, traceback)


if __name__ == "__main__":
    sys.excepthook = excepthook
    currentExitCode = Sapper.EXIT_CODE_RESTART
    while currentExitCode == Sapper.EXIT_CODE_RESTART:
        app = QApplication(sys.argv)
        ex = Sapper()
        ex.show()
        currentExitCode = app.exec()
        app = None
