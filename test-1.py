from PyQt5.QtWidgets import QApplication, QWidget, QSizePolicy, QTableView, QGridLayout, QVBoxLayout, QGroupBox, QComboBox, QSpinBox, QLineEdit, QRadioButton, QPushButton, QLabel
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QVariant, Qt
import sqlite3
import sys

#Класс модели для взаимодействия с БД:
class Model(QAbstractTableModel):

	def __init__(self, parent):
		super().__init__()
		self.base = sqlite3.connect(':memory:')
		self.base.row_factory = sqlite3.Row
		self.curr = self.base.cursor()
		#...
		self.curr.executescript('''
		     CREATE TABLE students (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR, sex BOOLEAN, age INTEGER, city VARCHAR);
		     INSERT INTO students (name, sex, age, city) VALUES
		     ('Semen', 1, 20, 'Saint Petersburg'),
		     ('Vasya', 1, 18, 'Moscow'),
		     ('Sveta', 0, 17, 'Moscow'),
		     ('Petya', 1, 19, 'Moscow'),
		     ('Masha', 0, 19, 'Kazan'),
		     ('Varya', 0, 20, 'Yekaterinburg'),
		     ('Kolya', 1, 17, 'Vladivostok'),
		     ('Katya', 0, 20, 'Kiev'),
		     ('Slava', 1, 18, 'Habarovsk');
		     CREATE VIEW contents AS SELECT id, name, CASE sex WHEN 0 THEN 'F' ELSE 'M' END as sex, age, city FROM students;
		''')
		self.base.commit()
		#...
		self.header = ['ID', 'Name', 'Sex', 'Age', 'City']
		#...
		self.sort_order = Qt.AscendingOrder
		self.sort_col = 0
		#...
		self.dict = dict()
		self.list = []
		self.view = parent
		self.reset()

	def updateRow(self, row, dat):
		try:
			self.curr.execute('UPDATE students SET name = ?, sex = ?, age = ?, city = ? WHERE id = ?', dat[:] + (row,))
			self.base.commit()
		except:
			print('ERROR!')
		self.reset()

	def insertRow(self, dat):
		try:
			self.curr.execute('INSERT INTO students (name, sex, age, city) VALUES (?, ?, ?, ?)', dat)
			self.base.commit()
		except:
			print('ERROR!')
		self.reset()

	def removeRow(self, row):
		try:
			self.curr.execute('DELETE FROM students WHERE id = ?', (row,))
			self.base.commit()
		except:
			print('ERROR!')
		self.reset()

	def getDataByID(self, rowid):
		if rowid in self.dict: return tuple(self.dict[rowid])
		return None

	def getRowData(self, row):
		if row >= 0 and row < len(self.list):
			return tuple(self.list[row])
		return None

	def reset(self):
		col, order = self.sort_col, self.sort_order
		col, order = (self.header[col], 'ASC' if order == Qt.AscendingOrder else 'DESC')
		self.beginRemoveRows(QModelIndex(), 0, len(self.list) - 1)
		self.endRemoveRows()
		self.curr.execute('SELECT * FROM contents ORDER BY ' + col + ' ' + order)
		self.list = self.curr.fetchall()
		self.beginInsertRows(QModelIndex(), 0, len(self.list) - 1)
		self.endInsertRows()
		self.dict = {it[0]: it for it in self.list}
		#self.view.resizeColumnsToContents()
		#self.view.resizeRowsToContents()
		self.view.reset()

	def sort(self, col, order):
		self.sort_order = order
		self.sort_col = col
		self.reset()

	def data(self, index, role):
		if role not in (Qt.DisplayRole, Qt.EditRole) or not index.isValid():
			return QVariant()
		if role == Qt.DisplayRole:
			val = self.list[index.row()][index.column()]
		else:
			val = ''
		return QVariant(val)

	def headerData(self, section, orientation, role):
		if orientation == Qt.Horizontal and  role == Qt.DisplayRole:
			return QVariant(self.header[section])
		return QVariant()

	def columnCount(self, parent):
		return len(self.header)

	def rowCount(self, parent):
		return len(self.list)

#Класс представления:
class View(QTableView):

	def __init__(self, parent):
		super().__init__(parent)
		self.horizontalHeader().setSortIndicatorShown(True)
		self.setSortingEnabled(True)
		self.model = Model(self)
		self.setModel(self.model)

	def getDataByID(self, rowid):
		return self.model.getDataByID(rowid)

	def getRowData(self, row):
		return self.model.getRowData(row)

	def updateRow(self, row, dat):
		self.model.updateRow(row, dat)

	def insertRow(self, dat):
		self.model.insertRow(dat)

	def removeRow(self, row):
		self.model.removeRow(row)

#Класс основного окна:
class MyWindow(QWidget):

	def __init__(self):

		super().__init__()

		Fixed = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
		#...
		self.updateButton = QPushButton('Set')
		self.updateButton.clicked.connect(self.OnUpdate)	#Связываем сигнал со слотом;
		self.updateButton.setEnabled(False)
		#...
		self.insertButton = QPushButton('Add')
		self.insertButton.clicked.connect(self.OnInsert)
		#...
		self.deleteButton = QPushButton('Del')
		self.deleteButton.clicked.connect(self.OnDelete)
		#...
		self.spinRowID = QSpinBox()
		self.spinRowID.lineEdit().setReadOnly(True)
		self.spinRowID.valueChanged.connect(self.OnRowChanged)
		self.spinRowID.setSizePolicy(Fixed)
		#...
		self.editName = QLineEdit()
		#...
		self.vbox = QVBoxLayout()
		self.is_female = QRadioButton('FEMALE');
		self.is_male = QRadioButton('MALE');
		self.is_male.click()
		self.vbox.addWidget(self.is_female)
		self.vbox.addWidget(self.is_male)
		self.vbox.setDirection(QVBoxLayout.LeftToRight) #Задаем направление компоновки;
		self.chckSex = QGroupBox()
		self.chckSex.setLayout(self.vbox)
		#...
		self.listAge = QComboBox()
		self.listAge.setSizePolicy(Fixed) #Устанавливаем фиксированный размер виджета;
		for i in range(16, 31): self.listAge.addItem(str(i), i)
		#...
		self.editCity = QLineEdit()
		#...
		self.view = View(self)
		self.view.clicked.connect(self.OnViewClicked)
		self.view.sortByColumn(0, Qt.AscendingOrder)

		#Используем компоновщики для позиционирования виджетов:
		self.lay2 = QGridLayout()
		self.lay2.addWidget(self.updateButton, 0, 0)
		self.lay2.addWidget(self.insertButton, 1, 0)
		self.lay2.addWidget(self.deleteButton, 2, 0)
		self.lay2.addWidget(self.spinRowID, 0, 1)
		self.lay2.addWidget(self.editName, 0, 2)
		self.lay2.addWidget(self.listAge, 0, 3)
		self.lay2.addWidget(self.chckSex, 0, 4)
		self.lay2.addWidget(self.editCity, 0, 5)
		#...
		self.lay1 = QGridLayout(self)
		self.lay1.addLayout(self.lay2, 0, 0)
		self.lay1.addWidget(self.view, 1, 0)

		self.setGeometry(0, 0, 800, 500)
		self.setWindowTitle('Test Application')
		self.show()

	def update(self):
		temp = self.view.getDataByID(self.spinRowID.value())
		if not temp:
			self.updateButton.setEnabled(False)
			return
		self.updateButton.setEnabled(True)
		self.editName.setText(temp[1])
		if temp[2] == 'F':
			self.is_female.click()
		else:
			self.is_male.click()
		self.listAge.setCurrentText(str(temp[3]))
		self.editCity.setText(temp[4])
		self.repaint()

	def record(self):
		rec = [self.editName.text()]
		rec.append(1 if self.is_male.isChecked() else 0)
		rec.append(int(self.listAge.currentText()))
		rec.append(self.editCity.text())
		return tuple(rec)

	def OnViewClicked(self, index):
		temp = self.view.getRowData(index.row())
		self.spinRowID.setValue(temp[0])

	def OnRowChanged(self, rowid):
		self.update()

	def OnUpdate(self):
		rec = self.record()
		self.view.updateRow(self.spinRowID.value(), rec)
		self.update()

	def OnInsert(self):
		rec = self.record()
		self.view.insertRow(rec)
		self.update()

	def OnDelete(self):
		self.view.removeRow(self.spinRowID.value())
		self.update()

if __name__ == '__main__':

	app = QApplication(sys.argv)
	win = MyWindow()
	sys.exit(app.exec_())
