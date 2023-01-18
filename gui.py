import sys
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QHBoxLayout,QVBoxLayout,QLabel,QPushButton,QWidget,QTabWidget
from PyQt5.QtGui import QIcon


class BasicMenubar(QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)        
        
        self.initMainWindow()
    
    def initMenu(self):
        exitAction = QAction('&Exit', self)        
        exitAction.setShortcut('Ctrl+Q')
        exitAction.setStatusTip('Exit application')
        exitAction.triggered.connect(qApp.quit)

        setAction = QAction('&Setting', self)        
        setAction.setShortcut('Ctrl+E')
        setAction.setStatusTip('Exit application')

        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')
        fileMenu.addAction(exitAction)
        fileMenu.addAction(setAction)

        setMenu = menubar.addMenu('&Help')
    
    def inittest(self):
        ############主窗口控件####################
        # 全局布局
        alllayout = QHBoxLayout()

        # 局部布局
        # 右垂直布局
        vlayout1 = QVBoxLayout()

        v1_hlayout1 = QHBoxLayout()  ##右上水平布局
        v1_h1_hlayout1 = QVBoxLayout()  ###右上右垂直布局
        v1_h1_hlayout2 = QVBoxLayout()  ###右上左垂直布局

        v1_hlayout2 = QHBoxLayout()  ##右下水平布局
        # 左垂直布局
        vlayout2 = QVBoxLayout()
        self.lab1 = QLabel('1区')
        self.lab1.setFixedSize(800, 600)
        self.lab1.setStyleSheet("QLabel{background:yellow;}")
        self.btn1 = QPushButton("测试11")
        self.btn2 = QPushButton("测试12")
        self.btn3 = QPushButton("测试13")
        self.btn4 = QPushButton("测试14")
        self.lab2 = QLabel('2区')
        self.lab2.setFixedSize(300, 20)
        self.lab2.setStyleSheet("QLabel{background:yellow;}")
        self.btn5 = QPushButton("测试21")
        self.btn6 = QPushButton("测试22")
        self.btn7 = QPushButton("测试23")
        self.btn8 = QPushButton("测试24")
        self.lab3 = QLabel('3区')
        self.lab3.setFixedSize(100, 100)
        self.lab3.setStyleSheet("QLabel{background:yellow;}")
        self.btn9 = QPushButton("测试31")
        self.btn10 = QPushButton("测试32")
        self.btn11 = QPushButton("测试33")
        self.btn12 = QPushButton("测试34")
        self.lab4 = QLabel('4区')
        self.lab4.setFixedHeight(20)
        self.lab4.setStyleSheet("QLabel{background:yellow;}")
        self.btn13 = QPushButton("测试41")
        self.btn14 = QPushButton("测试42")
        self.btn15 = QPushButton("测试43")
        self.btn16 = QPushButton("测试44")
        
        # 在局部布局中添加控件
        v1_h1_hlayout1.addWidget(self.lab2)
        v1_h1_hlayout1.addWidget(self.btn5)
        v1_h1_hlayout1.addWidget(self.btn6)
        v1_h1_hlayout1.addWidget(self.btn7)
        v1_h1_hlayout1.addWidget(self.btn8)
        v1_h1_hlayout1.addStretch(0)

        v1_h1_hlayout2.addWidget(self.lab1)
        v1_h1_hlayout2.addWidget(self.btn1)
        v1_h1_hlayout2.addWidget(self.btn2)
        v1_h1_hlayout2.addWidget(self.btn3)
        v1_h1_hlayout2.addWidget(self.btn4)
        v1_h1_hlayout2.addStretch(0)

        v1_hlayout2.addWidget(self.lab3)
        v1_hlayout2.addWidget(self.btn9)
        v1_hlayout2.addWidget(self.btn10)
        v1_hlayout2.addWidget(self.btn11)
        v1_hlayout2.addWidget(self.btn12)

        vlayout2.addWidget(self.lab4)
        vlayout2.addWidget(self.btn13)
        vlayout2.addWidget(self.btn14)
        vlayout2.addWidget(self.btn15)
        vlayout2.addWidget(self.btn16)

        vlayout2.addStretch(0)
        v1_hlayout1.addLayout(v1_h1_hlayout1)
        v1_hlayout1.addLayout(v1_h1_hlayout2)

        vlayout1.addLayout(v1_hlayout1)
        vlayout1.addLayout(v1_hlayout2)

        # 局部布局添加到全局布局
        alllayout.addLayout(vlayout1)
        alllayout.addLayout(vlayout2)

        widget = QWidget()
        widget.setLayout(alllayout)
        self.setCentralWidget(widget)

    def initCentrolWindow(self):
        aaaTab = QWidget()
        bbbTab = QWidget()
        cccTab = QWidget()

        tabWidget = QTabWidget()
        tabWidget.addTab(aaaTab, "aaa")
        tabWidget.addTab(bbbTab, "bbb")
        tabWidget.addTab(cccTab, "ccc")
        self.setCentralWidget(tabWidget)
        

    def initMainWindow(self):    
        self.resize(512,512)
        self.initMenu()
        self.initCentrolWindow()
        self.setWindowTitle('PyQt5 Basic Menubar')    
        self.show()
        
        
# if __name__ == '__main__':
    
    # app = QApplication(sys.argv)
    # ex = basicMenubar()
    # sys.exit(app.exec_())