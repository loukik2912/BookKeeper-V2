import PyQt5.QtWidgets as qtw
from PyQt5.QtCore import Qt
import sqlite3
from datetime import datetime as dt

class MainWindow(qtw.QWidget):
    def __init__(self, dbConn):
        super().__init__()

        self.setWindowTitle("TBR Tracker")

        vLayout = qtw.QVBoxLayout()
        fLayout = qtw.QFormLayout()

        self.inputWidgets = {}
        self.infoWidgets = {}
        
        self.inputWidgets["Add"] = qtw.QPushButton("Add", clicked = lambda : self.add_data(dbConn))
        self.inputWidgets["Clear"] = qtw.QPushButton("Clear", clicked = lambda : self.clear_all_data())
        fLayout.addRow(self.inputWidgets["Add"], self.inputWidgets["Clear"])

        self.inputWidgets["Name"] = qtw.QLineEdit()
        fLayout.addRow("Name:", self.inputWidgets["Name"])
        
        conn = sqlite3.connect(dbConn.dbPath, detect_types=sqlite3.PARSE_DECLTYPES)
        dbCursor = conn.cursor()
        typesData = dbCursor.execute("SELECT * FROM book_types")
        self.types = map(lambda x : x[0], typesData.fetchall()) #["Series", "Non-fiction", "Standalone", "Duology", "Trilogy", "Collection", "Misc"]
        dbCursor.close()
        conn.close()
        
        self.inputWidgets["Type"] = qtw.QComboBox()
        self.inputWidgets["Type"].addItems(self.types)
        fLayout.addRow("Type:", self.inputWidgets["Type"])
        
        conn = sqlite3.connect(dbConn.dbPath, detect_types=sqlite3.PARSE_DECLTYPES)
        dbCursor = conn.cursor()
        authorsData = dbCursor.execute("SELECT DISTINCT Author FROM tracking_tbr ORDER BY Author")
        self.authors = map(lambda x : x[0], authorsData.fetchall()) #["Series", "Non-fiction", "Standalone", "Duology", "Trilogy", "Collection", "Misc"]
        dbCursor.close()
        conn.close()
        
        self.inputWidgets["Author"] = qtw.QComboBox(editable=True,insertPolicy=qtw.QComboBox.InsertAlphabetically)
        self.inputWidgets["Author"].addItems(self.authors)
        fLayout.addRow("Author:", self.inputWidgets["Author"])

        self.inputWidgets["Rating"] = qtw.QSlider(Qt.Horizontal)
        self.inputWidgets["Rating"].setRange(1,10)
        self.inputWidgets["Rating"].setValue(10)
        fLayout.addRow("Rating:", self.inputWidgets["Rating"])
        
        self.infoWidgets["Numeric Rating"] = qtw.QLabel() #qtw.QLineEdit()
        self.infoWidgets["Numeric Rating"].setText(str(self.inputWidgets["Rating"].value())) # self.infoWidgets["Numeric Rating"].setText(self.ratingComboBox.currentText())
        fLayout.addRow("Numeric rating:", self.infoWidgets["Numeric Rating"])
        self.inputWidgets["Rating"].valueChanged.connect(lambda:self.update_numeric_rating()) # self.ratingComboBox.currentTextChanged.connect(lambda:self.update_numeric_rating())

        self.inputWidgets["Remarks"] = qtw.QLineEdit()
        fLayout.addRow("Remarks:", self.inputWidgets["Remarks"])

        vLayout.addLayout(fLayout)

        hLayout = qtw.QHBoxLayout()
        self.statusStr = "Available"
        self.inputWidgets["Status"] = {}
        for option in ["DLed_or_Exist","Ongoing","Unavailable","DNF"]:
            hLayout.addWidget(qtw.QLabel(option))
            self.inputWidgets["Status"][option] = qtw.QCheckBox()
            self.inputWidgets["Status"][option].stateChanged.connect(lambda:self.calculate_status())
            hLayout.addWidget(self.inputWidgets["Status"][option])
        vLayout.addLayout(hLayout)

        fLayout2 = qtw.QFormLayout()
        self.infoWidgets["Status Text"] = qtw.QLabel()
        fLayout2.addRow("Status:", self.infoWidgets["Status Text"])
        self.infoWidgets["Status Text"].setText("Available")
        vLayout.addLayout(fLayout2)

        self.infoWidgets["Record Info"] = qtw.QPlainTextEdit()
        vLayout.addWidget(self.infoWidgets["Record Info"])

        
        self.setLayout(vLayout)

        #self.show()


    def add_data(self, dbConn):
        recordInfoText = ""
        argsDict = {}

        for field in ["Name", "Remarks"]:
            argsDict[field] = self.inputWidgets[field].text().strip() if self.inputWidgets[field].text().strip() else None
        for field in ["Type", "Author"]:
            argsDict[field] = self.inputWidgets[field].currentText()
        for field in self.inputWidgets["Status"].keys():
            argsDict[field] = self.inputWidgets["Status"][field].isChecked()

        argsDict["Status"] = self.statusStr
        argsDict["Rating"] = self.inputWidgets["Rating"].value()
        argsDict["Created_at"] = dt.now()
        argsDict["Last_Modified"] = dt.now()

        recordInfoText = ""
        for k,v in argsDict.items():
                recordInfoText += f"{k}: {v}\n"

        # print(recordInfoText)
        self.set_display_text(recordInfoText)
        
        self.insert_data(dbConn=dbConn, inputData=argsDict)

    def insert_data(self, dbConn, inputData):
        conn = sqlite3.connect(dbConn.dbPath, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        dbCursor = conn.cursor()

        insertQuery = """INSERT INTO tracking_tbr
        (Name, Type, Author, Rating, Remarks, Status, DLed_or_Exist, Ongoing, Unavailable, DNF, Created_at, Last_Modified)
        VALUES (:Name, :Type, :Author, :Rating, :Remarks, :Status, :DLed_or_Exist, :Ongoing, :Unavailable, :DNF, :Created_at, :Last_Modified);"""

        try:
            dbCursor.execute(insertQuery, inputData)
            conn.commit()
            print("Record inserted into database!!")
            self.set_display_text(self.infoWidgets["Record Info"].toPlainText() + "\nRecord inserted into database!")
        except sqlite3.Error as e:
            print(f"ERROR: {e}")
            self.set_display_text(f"ERROR: {e}")
            
        
        dbCursor.close()
        conn.close()


    def calculate_status(self):
        if self.inputWidgets["Status"]["DNF"].isChecked():
            self.statusStr = "DNF"
        elif self.inputWidgets["Status"]["Ongoing"].isChecked():
            self.statusStr = "Ongoing"
        elif self.inputWidgets["Status"]["DLed_or_Exist"].isChecked():
            self.statusStr = "DLed_or_Exist"
        elif self.inputWidgets["Status"]["Unavailable"].isChecked():
            self.statusStr = "Unavailable"
        else:
            self.statusStr = "Available"

        self.infoWidgets["Status Text"].setText(self.statusStr)

    def clear_all_data(self):
        self.set_display_text("Cleared data!")

        for field in ["Name", "Remarks"]:
            self.inputWidgets[field].clear()
        for field in ["Type", "Author"]:
            self.inputWidgets[field].clearEditText()
        for field in self.inputWidgets["Status"].keys():
            self.inputWidgets["Status"][field].setCheckState(False)

        self.inputWidgets["Rating"].setValue(10) # self.ratingComboBox.clearEditText()

    def update_numeric_rating(self):
        self.infoWidgets["Numeric Rating"].setText(str(self.inputWidgets["Rating"].value())) # self.infoWidgets["Numeric Rating"].setText(self.ratingComboBox.currentText())

    def set_display_text(self, msg):
        self.infoWidgets["Record Info"].setPlainText(msg)


class DBConn():
    def __init__(self, dbPath=""):
        self.dbPath = dbPath


if __name__ == "__main__":
    app = qtw.QApplication([])
    dbConn = DBConn(dbPath="C:\\sqlite\\Databases\\books_db.db")
    mainWindow = MainWindow(dbConn=dbConn)
    mainWindow.show()

    app.exec_()
