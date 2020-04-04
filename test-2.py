from PyQt5.QtWidgets import QApplication, QWidget, QSizePolicy, QTableView, QGridLayout, QVBoxLayout, QGroupBox, QComboBox, QSpinBox, QLineEdit, QRadioButton, QPushButton, QLabel
from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QVariant, Qt
from PyQt5 import QtSql
import sys

#Класс модели для взаимодействия с БД:
class Model(QtSql.QSqlTableModel):

	def __init__(self, parent):

		self.base = QtSql.QSqlDatabase.addDatabase('QSQLITE')
		self.base.setDatabaseName(':memory:')

		if not self.base.open():
			print('Can\'t open database!')
			exit(-1)

		self.curr = QtSql.QSqlQuery()
		self.base.transaction()
		self.curr.exec_('''
		     CREATE TABLE students (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR, sex BOOLEAN, age INTEGER, city VARCHAR);
		''')
		self.curr.exec_('''
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
		''')
		self.curr.exec_('''
		     CREATE VIEW contents AS SELECT id, name, CASE sex WHEN 0 THEN 'F' ELSE 'M' END as sex, age, city FROM students;
		''')
		self.base.commit()

		super().__init__()

		self.setTable(
		'students'
		)

	def __rowIndexByID(self, ind):
		for i in range(self.rowCount()):
			if self.record(i).value("id") == ind: return i
		return None

	def selectItemByID(self, ind):
		return self.selectItem(self.__rowIndexByID(ind))

	def updateItemByID(self, ind, dat):
		return self.updateItem(self.__rowIndexByID(ind), dat)

	def removeItemByID(self, ind):
		self.removeItem(self.__rowIndexByID(ind))

	def selectItem(self, row):
		if row is None: return None
		if 0 <= row < self.rowCount():
			data = []
			data += [self.data(self.index(row, 0))]
			data += [self.data(self.index(row, 1))]
			data += [self.data(self.index(row, 2))]
			data += [self.data(self.index(row, 3))]
			data += [self.data(self.index(row, 4))]
			return tuple(data)
		return None

	def updateItem(self, row, dat):
		if row is None: return
		self.setData(self.index(row, 1), dat[0])
		self.setData(self.index(row, 2), dat[1])
		self.setData(self.index(row, 3), dat[2])
		self.setData(self.index(row, 4), dat[3])
		self.submitAll()
		self.select()

	def removeItem(self, row):
		if row is None: return
		self.removeRows(row, 1)
		self.submitAll()
		self.select()

	def insertItem(self, dat):
		row = self.rowCount() - 1
		self.insertRows(row, 1)
		self.setData(self.index(row, 1), dat[0])
		self.setData(self.index(row, 2), dat[1])
		self.setData(self.index(row, 3), dat[2])
		self.setData(self.index(row, 4), dat[3])
		self.submitAll()
		self.select()

#Класс представления:
class View(QTableView):

	def __init__(self, parent):
		super().__init__(parent)
		self.horizontalHeader().setSortIndicatorShown(True)
		self.setSortingEnabled(True)
		self.model = Model(self)
		self.setModel(self.model)

	def selectItemByID(self, ind):
		return self.model.selectItemByID(ind)

	def updateItemByID(self, ind, dat):
		self.model.updateItemByID(ind, dat)

	def removeItemByID(self, ind):
		self.model.removeItemByID(ind)

	def selectItem(self, row):
		return self.model.selectItem(row)

	def updateItem(self, row, dat):
		self.model.updateItem(row, dat)

	def removeItem(self, row):
		self.model.removeItem(row)

	def insertItem(self, dat):
		self.model.insertItem(dat)

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
		temp = self.view.selectItemByID(self.spinRowID.value())
		if not temp:
			self.updateButton.setEnabled(False)
			return
		self.updateButton.setEnabled(True)
		self.editName.setText(temp[1])
		if not temp[2]:
			self.is_female.click()
		else:
			self.is_male.click()
		self.listAge.setCurrentText(str(temp[3]))
		self.editCity.setText(temp[4])
		self.repaint()

	def record(self):
		dat = [self.editName.text()]
		dat.append(1 if self.is_male.isChecked() else 0)
		dat.append(int(self.listAge.currentText()))
		dat.append(self.editCity.text())
		return tuple(dat)

	def OnViewClicked(self, index):
		temp = self.view.selectItem(index.row())
		if temp is None: return
		self.spinRowID.setValue(temp[0])

	def OnRowChanged(self, ind):
		self.update()

	def OnUpdate(self):
		dat = self.record()
		self.view.updateItemByID(self.spinRowID.value(), dat)
		self.update()

	def OnInsert(self):
		dat = self.record()
		self.view.insertItem(dat)
		self.update()

	def OnDelete(self):
		self.view.removeItemByID(self.spinRowID.value())
		self.update()

if __name__ == '__main__':

	app = QApplication(sys.argv)
	win = MyWindow()
	sys.exit(app.exec_())
