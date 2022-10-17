from PIL import Image
import sys, os, webbrowser, cProfile, re
from PyQt5 import QtWebEngineWidgets
from PyQt5.QtCore import *
from functools import partial
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtWebEngineWidgets import *

class preferencesWindow(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Preferences')

        titleLabel = QLabel('Preferences',self)
        titleLabel.setFont(QFont("Times",weight=QFont.Bold))
        appSLabel = QLabel('App Style',self)

        appSBox = QComboBox(self)
        appSBox.addItem("Fusion")
        appSBox.addItem("Windows")
        appSBox.addItem("windowsvista")
        appSBox.move(50, 250)
        appSBox.activated[str].connect(self.style_choice)

        done = QPushButton("&Done")
        done.clicked.connect(self.close)

        mainLayout = QGridLayout(self)
        mainLayout.addWidget(titleLabel, 0, 0)
        mainLayout.addWidget(appSLabel, 1, 0)
        mainLayout.addWidget(appSBox, 1, 1, 1, 1)
        mainLayout.addWidget(done, 2, 0, 1, 2)

    def style_choice(self, text):
        QApplication.setStyle(QStyleFactory.create(text))

class newCanvas(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('New File')
        self.resize(250,90)

        nameLabel = QLabel('&Name',self)
        self.nameLineEdit = QLineEdit(self)
        nameLabel.setBuddy(self.nameLineEdit)

        widthLabel = QLabel('&Width',self)
        self.widthLineEdit = QSpinBox(self)
        self.widthLineEdit.setMinimum(1)
        self.widthLineEdit.setMaximum(10240)
        widthLabel.setBuddy(self.widthLineEdit)

        heightLabel = QLabel('&Height',self)
        self.heightLineEdit = QSpinBox(self)
        self.heightLineEdit.setMinimum(1)
        self.heightLineEdit.setMaximum(10240)
        heightLabel.setBuddy(self.heightLineEdit)

        self.btnOK = QPushButton('&Create')
        self.btnOK.clicked.connect(win.setupCanvas)
        btnCancel = QPushButton('&Cancel')
        btnCancel.clicked.connect(self.close)

        mainLayout = QGridLayout(self)
        mainLayout.addWidget(nameLabel,0,0)
        mainLayout.addWidget(self.nameLineEdit,0,1,1,2)

        mainLayout.addWidget(widthLabel,1,0)
        mainLayout.addWidget(self.widthLineEdit,1,1,1,2)
        
        mainLayout.addWidget(heightLabel,2,0)
        mainLayout.addWidget(self.heightLineEdit,2,1,1,2)

        mainLayout.addWidget(self.btnOK,3,1)
        mainLayout.addWidget(btnCancel,3,2)

class Window(QMainWindow):
    """Main Window."""
    def __init__(self, parent=None):
        """Initializer."""
        super().__init__(parent)

        self.topLevelFilePath = os.path.dirname(__file__)

        with open(self.topLevelFilePath + '/UI/stylesheet.qss', 'r', encoding='utf-8') as file:
            style = file.read()
        self.setStyleSheet(style)

        global drawingName
        drawingName = "Temporary File"
        self.setWindowTitle(drawingName + " - Painting v0.1pa")
        self.resize(512 + 60, 512 + 76 + 60)

        self.mainImage = QImage(512, 512, QImage.Format_RGB32)
        self.mainImage.fill(Qt.white)

        self.zoomFactor = float(1)

        self.undoIterations = []
        self.redoIterations = []
        
        self.labelImage = QLabel()
        self.labelImage.setPixmap(QPixmap.fromImage(self.mainImage))
        self.labelImage.setAlignment(Qt.AlignCenter)
        dropShadow = QGraphicsDropShadowEffect()
        dropShadow.setBlurRadius(30)
        self.labelImage.setGraphicsEffect(dropShadow)
        layout = QGridLayout()

        self.setCentralWidget(self.labelImage)

        self.undoIterations.append(QPixmap.fromImage(self.mainImage))

        self.setContextMenuPolicy(Qt.PreventContextMenu)
        self.selectionArea = QRect()
        self.selectionStarted = False
        self.drawMode = -1
        
        self.drawing = False
        self.secondaryDrawing = False

        self.brushSize = 2
        self.brushColor = Qt.black
        self.brushColorB = Qt.white
        self.primaryBrushFocused = True
        self.lastPoint = QPoint()

        self._createActions()
        self._createMenuBar()
        self._connectActions()
        self._createStatusBar()
        self._createToolBars()

    def _createActions(self):
        # Creating action using the first constructor
        self.newAction = QAction(self)
        self.newAction.setText("&New")
        self.newAction.setIcon(QIcon(self.topLevelFilePath + "/UI/images/new.svg"))
        # Creating actions using the second constructor
        self.openAction = QAction(QIcon(self.topLevelFilePath + "/UI/images/open.svg"), "&Open...", self)
        self.saveAction = QAction(QIcon(self.topLevelFilePath + "/UI/images/save.svg"), "&Save", self)
        self.settingsAction = QAction(QIcon(self.topLevelFilePath + "/UI/images/settings.svg"), "&Preferences", self)
        self.exitAction = QAction("&Exit", self)

        self.newAction.setShortcut("Ctrl+N")
        self.openAction.setShortcut("Ctrl+O")
        self.saveAction.setShortcut("Ctrl+S")

        newTip = "Create a new file"
        self.newAction.setStatusTip(newTip)
        self.newAction.setToolTip(newTip)
        openTip = "Open a file on your computer"
        self.openAction.setStatusTip(openTip)
        self.openAction.setToolTip(openTip)
        saveTip = "Save your current file"
        self.saveAction.setStatusTip(saveTip)
        self.saveAction.setToolTip(saveTip)

        self.copyAction = QAction(QIcon(self.topLevelFilePath + "/UI/images/copy.svg"), "&Copy", self)
        self.pasteAction = QAction(QIcon(self.topLevelFilePath + "/UI/images/paste.svg"), "&Paste", self)
        self.cutAction = QAction(QIcon(self.topLevelFilePath + "/UI/images/cut.svg"), "&Cut", self)
        self.clearAction = QAction(QIcon(self.topLevelFilePath + "/UI/images/clear.svg"), "&Clear", self)
        self.undoAction = QAction(QIcon(self.topLevelFilePath + "/UI/images/undo.svg"), "&Undo", self)
        self.redoAction = QAction(QIcon(self.topLevelFilePath + "/UI/images/redo.svg"), "&Redo", self)
        self.copyAction.setShortcut(QKeySequence.Copy)
        self.pasteAction.setShortcut(QKeySequence.Paste)
        self.cutAction.setShortcut(QKeySequence.Cut)
        self.clearAction.setShortcut("Ctrl+Q")
        self.undoAction.setShortcut("Ctrl+Z")
        self.redoAction.setShortcut("Ctrl+Y")

        self.profileAction = QAction("&Profile", self)
        self.profileAction.setShortcut("Ctrl+Alt+P")

        aMap = QPixmap(24,24).toImage()
        aMap.fill(Qt.black)
        for x in range(22):
            for y in range(22):
                aMap.setPixelColor(x+1,y+1, self.brushColor)
        aMap = QPixmap(24,24).fromImage(aMap)

        bMap = QPixmap(24,24).toImage()
        bMap.fill(Qt.black)
        for x in range(22):
            for y in range(22):
                bMap.setPixelColor(x+1,y+1, self.brushColorB)
        bMap = QPixmap(24,24).fromImage(bMap)

        self.colorPickerAction = QAction(QIcon(aMap), "&Color Picker", self)
        self.colorPickerActionB = QAction(QIcon(bMap), "&Secondary Color Picker", self)

        self.helpContentAction = QAction("&Help Content", self)
        self.aboutAction = QAction("&About", self)

    def populateOpenRecent(self):
        # Step 1. Remove the old options from the menu
        self.openRecentMenu.clear()
        # Step 2. Dynamically create the actions
        actions = []
        filenames = [f"File-{n}" for n in range(5)]
        for filename in filenames:
            action = QAction(filename, self)
            action.triggered.connect(partial(self.openRecentFile, filename))
            actions.append(action)
        # Step 3. Add the actions to the menu
        self.openRecentMenu.addActions(actions)

    def _createMenuBar(self):
        menuBar = QMenuBar(self)
        menuBar.setFixedHeight(24)
        fileMenu = QMenu("&File",self)
        #File Menu
        menuBar.addMenu(fileMenu)
        fileMenu.addAction(self.newAction)
        fileMenu.addAction(self.openAction)
        self.openRecentMenu = fileMenu.addMenu("Open Recent")
        fileMenu.addAction(self.saveAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.settingsAction)
        fileMenu.addSeparator()
        fileMenu.addAction(self.exitAction)
        editMenu = menuBar.addMenu("&Edit")
        editMenu.addAction(self.undoAction)
        editMenu.addAction(self.redoAction)
        editMenu.addSeparator()
        editMenu.addAction(self.copyAction)
        editMenu.addAction(self.pasteAction)
        editMenu.addAction(self.cutAction)
        editMenu.addSeparator()
        editMenu.addAction(self.clearAction)

        devMenu = menuBar.addMenu("&Developer")
        devMenu.addAction(self.profileAction)

        helpMenu = menuBar.addMenu(QIcon(self.topLevelFilePath + "/UI/images/info.svg"), "&Help")
        helpMenu.addAction(self.helpContentAction)
        helpMenu.addAction(self.aboutAction)

        
        self.setMenuBar(menuBar)

    def _createToolBars(self):
        brushManager = QButtonGroup(self)
        # Using a QToolBar object
        self.editToolBar = QToolBar("Edit", self)
        self.editToolBar.setMovable(False)

        selectButton = QToolButton()
        selectButton.setIcon(QIcon(self.topLevelFilePath + "/UI/images/select.svg"))
        selectButton.setCheckable(True)
        brushManager.addButton(selectButton)
        selectButton.toggled.connect(lambda: self.switchDrawMode(2))

        self.editToolBar.addWidget(selectButton)
        self.editToolBar.addAction(self.copyAction)
        self.editToolBar.addAction(self.pasteAction)
        self.editToolBar.addAction(self.cutAction)
        self.editToolBar.addSeparator()
        self.editToolBar.addAction(self.undoAction)
        self.editToolBar.addAction(self.redoAction)
        self.editToolBar.addSeparator()
        self.brushSizeSlider = QSlider(Qt.Horizontal)
        self.brushSizeSlider.setMaximum(100)
        self.brushSizeSlider.setMinimum(1)

        self.brushSizeLabel = QLabel("Size:\n" + str(self.brushSizeSlider.value()) + " px", self)
        self.brushSizeLabel.setAlignment(Qt.AlignCenter)

        self.brushSizeLabel.setFixedWidth(50)
        self.brushSizeLabel.setBuddy(self.brushSizeSlider)
        self.brushSizeSlider.valueChanged.connect(self.brushSliderUpdate)

        self.editToolBar.addAction(self.colorPickerAction)
        self.editToolBar.addAction(self.colorPickerActionB)

        brushButton = QToolButton()
        brushButton.setIcon(QIcon(self.topLevelFilePath + "/UI/images/brush.svg"))
        brushButton.setCheckable(True)
        brushManager.addButton(brushButton)

        fillButton = QToolButton()
        fillButton.setIcon(QIcon(self.topLevelFilePath + "/UI/images/fill.svg"))
        fillButton.setCheckable(True)
        brushManager.addButton(fillButton)

        brushButton.toggled.connect(lambda: self.switchDrawMode(0))
        fillButton.toggled.connect(lambda: self.switchDrawMode(1))

        self.editToolBar.addWidget(brushButton)
        self.editToolBar.addWidget(fillButton)
        self.editToolBar.addWidget(self.brushSizeLabel)
        self.editToolBar.addWidget(self.brushSizeSlider)

        self.editToolBar.orientationChanged.connect(lambda: self.reorientToolBar(self.editToolBar.orientation()))

        self.addToolBar(self.editToolBar)

    def reorientToolBar(self, tb):
        self.brushSizeSlider.setOrientation(tb)

    def _createStatusBar(self):
        self.statusbar = self.statusBar()
        self.statusBar().setStyleSheet("background-color: white")
        self.statusbar.showMessage("Ready", 3000)
        self.rLabel = QLabel()
        self.resolutionChange()
        self.statusbar.addPermanentWidget(self.rLabel)

        self.zLabel = QLabel(f"Zoom: {int(self.zoomFactor * 100)}%")
        self.statusbar.addPermanentWidget(self.zLabel)

        self.zSlider = QSlider(Qt.Horizontal, self)
        self.zSlider.setMaximum(16)
        self.zSlider.setMinimum(1)
        self.zSlider.setSingleStep(1)
        self.zSlider.setValue(1)
        self.zSlider.setMaximumWidth(150)
        self.zSlider.valueChanged.connect(self.zoomChange)
        self.statusbar.addPermanentWidget(self.zSlider)

    def adjustedMouse(self, pos):
        #posList = [int(int(pos.x()) - ((self.width() - self.mainImage.width()) / 2 )), int(int(pos.y()) - ((self.height()- self.mainImage.height()) / 2) - self.editToolBar.height())]
        posList = [int(pos.x() - ((self.width() - self.mainImage.width()) / 2 )), int(pos.y() - 24 - self.editToolBar.height() - (self.height() - 24 - self.editToolBar.height() - self.mainImage.height() - self.statusbar.height()) / 2)]
        return posList 

    def mousePressEvent(self, event):
        if(self.labelImage.underMouse()):
            if(self.drawMode == -1):
                self.statusbar.showMessage("Please select a mode to start painting", 3000)
            if(self.drawMode == 0):
                # if left mouse button is pressed
                if (event.button() == Qt.LeftButton) | (event.button() == Qt.RightButton):
                    # make drawing flag true
                    self.primaryBrushFocused = (event.button() == Qt.LeftButton)
                    self.drawing = True
                    # make last point to the point of cursor

                    self.brushSize = self.brushSizeSlider.value()

                    if event.button() == Qt.LeftButton:
                        painter = QPainter(self.mainImage)
                    
                        painter.setPen(QPen(self.brushColor, self.brushSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                        painter.drawPoint(self.adjustedMouse(event.localPos())[0], self.adjustedMouse(event.localPos())[1])

                        self.lastPoint = QPoint(self.adjustedMouse(event.localPos())[0], self.adjustedMouse(event.localPos())[1])
                        self.updateImage()

                    if event.button() == Qt.RightButton:
                        painter = QPainter(self.mainImage)
                    
                        painter.setPen(QPen(self.brushColorB, self.brushSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                        painter.drawPoint(self.adjustedMouse(event.localPos())[0], self.adjustedMouse(event.localPos())[1])

                        self.lastPoint = QPoint(self.adjustedMouse(event.localPos())[0], self.adjustedMouse(event.localPos())[1])
                        self.updateImage()

                    self.lastPoint = QPoint(self.adjustedMouse(event.localPos())[0], self.adjustedMouse(event.localPos())[1])

            elif(self.drawMode == 1):
                image = self.mainImage
                w, h = image.width(), image.height()
                s = image.bits().asstring(w * h * 4)
                
                def get_pixel(x, y):
                    i = (x + (y * w)) * 4
                    return s[i:i+3]


                x, y = int(self.adjustedMouse(event.localPos())[0]), int(self.adjustedMouse(event.localPos())[1])
                literal_color = image.pixelColor(x, y)
                target_color = get_pixel(x,y)

                def get_cardinal_points(just_seen, center_pos):
                    points = []
                    cx, cy = center_pos
                    for x, y in [(1, 0), (0, 1), (-1, 0), (0, -1)]:
                        xx, yy = cx + x, cy + y
                        if((xx, yy) in just_seen):
                            have_seen.add((xx,yy))
                            just_seen.remove((xx,yy))

                        if (xx >= 0 and xx < w and
                            yy >= 0 and yy < h and
                            (xx, yy) not in have_seen and
                            (xx, yy) not in just_seen):

                            points.append((xx, yy))
                            just_seen.add((xx, yy))

                    return points

                if (event.button() == Qt.LeftButton) and literal_color != self.brushColor:
                    p = QPainter(self.mainImage)
                    p.setPen(QPen(self.brushColor))

                    have_seen = set()
                    just_seen = set()
                    queue = [(x, y)]

                    while queue:
                        x, y = queue.pop()
                        if get_pixel(x, y) == target_color:
                            p.drawPoint(QPoint(x, y))
                            queue.extend(get_cardinal_points(just_seen, (x, y)))

                    self.addUndoItem()

                elif (event.button() == Qt.RightButton) and literal_color != self.brushColorB:
                    p = QPainter(self.mainImage)
                    p.setPen(QPen(self.brushColorB))

                    have_seen = set()
                    just_seen = set()
                    queue = [(x, y)]

                    while queue:
                        x, y = queue.pop()
                        if get_pixel(x, y) == target_color:
                            p.drawPoint(QPoint(x, y))
                            queue.extend(get_cardinal_points(just_seen, (x, y)))

                    self.addUndoItem()

            elif(self.drawMode == 2):
                if(event.button() == Qt.LeftButton):
                    self.selectionStarted = True
                    self.selectionArea.setTopLeft(event.pos())

            self.updateImage()
        
    def mouseMoveEvent(self, event):
        if(self.labelImage.underMouse()):
            if(self.drawMode == 0):
                if (event.buttons() & Qt.LeftButton) & self.drawing & self.primaryBrushFocused:
                    # creating painter object
                    painter = QPainter(self.mainImage)
                    
                    # set the pen of the painter
                    painter.setPen(QPen(self.brushColor, self.brushSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                    
                    # draw line from the last point of cursor to the current point
                    # this will draw only one step

                    painter.drawLine(self.lastPoint, QPoint(self.adjustedMouse(event.localPos())[0], self.adjustedMouse(event.localPos())[1]))

                    # change the last point
                    self.lastPoint = QPoint(self.adjustedMouse(event.localPos())[0], self.adjustedMouse(event.localPos())[1])
                    # update
                    self.updateImage()

                elif (event.buttons() & Qt.RightButton) & self.drawing & self.primaryBrushFocused != True:
                    # creating painter object
                    painter = QPainter(self.mainImage)
                    
                    # set the pen of the painter
                    painter.setPen(QPen(self.brushColorB, self.brushSize, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
                    
                    # draw line from the last point of cursor to the current point
                    # this will draw only one step

                    painter.drawLine(self.lastPoint, QPoint(self.adjustedMouse(event.localPos())[0], self.adjustedMouse(event.localPos())[1]))

                    # change the last point
                    self.lastPoint = QPoint(self.adjustedMouse(event.localPos())[0], self.adjustedMouse(event.localPos())[1])
                    # update
                    self.updateImage()

    def mouseReleaseEvent(self, event):
        if(self.drawMode == 0):
            if ((event.button() == Qt.LeftButton) | (event.button() == Qt.RightButton)) & self.drawing:
                # make drawing flag false
                self.addUndoItem()
                self.updateImage()
                self.drawing = False

    def paintEvent(self, event):
        canvasPainter = QPainter(self)
        #canvasPainter.drawImage(self.rect(), self.mainImage, self.mainImage.rect())

    def colorPicker(self):
        color = QColorDialog.getColor()
        if(color.isValid()):
            self.brushColor = color
            aMap = QPixmap(24,24).toImage()
            aMap.fill(Qt.black)
            for x in range(22):
                for y in range(22):
                    aMap.setPixelColor(x+1,y+1, self.brushColor)
            aMap = QPixmap(24,24).fromImage(aMap)
            self.colorPickerAction.setIcon(QIcon(aMap))

    def colorPickerB(self):
        color = QColorDialog.getColor()
        if(color.isValid()):
            self.brushColorB = color
            bMap = QPixmap(24,24).toImage()
            bMap.fill(Qt.black)
            for x in range(22):
                for y in range(22):
                    bMap.setPixelColor(x+1,y+1, self.brushColorB)
            bMap = QPixmap(24,24).fromImage(bMap)
            self.colorPickerActionB.setIcon(QIcon(bMap))

    def newFile(self):
        self.newFileDialog = newCanvas()
        self.newFileDialog.show()

    def setupCanvas(self):
        drawingName = self.newFileDialog.nameLineEdit.text()
        self.setWindowTitle(drawingName + " - Painting v0.1pa")
        self.mainImage = QImage(self.newFileDialog.widthLineEdit.value(), self.newFileDialog.heightLineEdit.value(), QImage.Format_RGB32)
        self.mainImage.fill(Qt.white)
        self.updateImage()
        self.resolutionChange()
        self.addUndoItem()
        self.newFileDialog.close()

    def openFile(self):
        filters = "All Image files (*.jpg *.png *.jpeg);;Portable Network Graphic (*.png);; JPEG Image (*.jpg *jpeg)"
        name = QFileDialog.getOpenFileName(self, 'Open File',"C:\\", filters, "All Image files (*.jpg *.png *.jpeg)")[0]
        if(name != ""):
            file = Image.open(name)
            self.mainImage.load(name, file.format)
            self.updateImage()
            drawingName = os.path.basename(name)
            self.setWindowTitle(drawingName + " - Painting v0.1pa")
            self.addUndoItem()
            self.resolutionChange()

    def openRecentFile(self, filename):
        # Logic for opening a recent file goes here...
        return 0

    def saveFile(self):
        filters = "All Image files (*.jpg *.png *.jpeg);;Portable Network Graphic (*.png);; JPEG Image (*.jpg *jpeg)"
        name = QFileDialog.getSaveFileName(self, 'Save File', "C:\\", filters, "Portable Network Graphic (*.png)")
        if(name[0] != ""):
            fCheck = os.path.splitext(name[0])
            fCheck = fCheck[1]
            feCheck = fCheck[1:].upper()
            print(feCheck)
            self.mainImage.save(name[0], feCheck)
            drawingName = os.path.basename(name[0])
            self.setWindowTitle(drawingName + " - Painting v0.1pa")

    def selectionPainter(self):
        p = QPainter(self.mainImage)
        p.setPen(QPen(QBrush(QColor(0,0,0,180),1,Qt.DashLine)))
        p.setBrush(QBrush(QColor(255,255,255,120)))

        p.drawRect(self.selectionArea)

    def copyContent(self):
        # Logic for copying content goes here...
        return 0

    def pasteContent(self):
        self.addUndoItem()
        return 0

    def cutContent(self):
        # Logic for cutting content goes here...
        return 0

    def clearContent(self):
        self.mainImage.fill(Qt.white)
        self.addUndoItem()
        self.updateImage()

    def addUndoItem(self):
        self.undoIterations.append(QPixmap.fromImage(self.mainImage))
        if(len(self.undoIterations) >= 50):
            self.undoIterations.pop(0)
        self.redoIterations = []

    def undoContent(self):
        if(len(self.undoIterations) > 1):
            self.redoIterations.append(self.undoIterations.pop())
            p = QPainter(self.mainImage)
            p.drawPixmap(0, 0, self.mainImage.width(), self.mainImage.height(), self.undoIterations[-1])
            p.end()
            self.updateImage()
        else:
            self.statusbar.showMessage("Cannot Undo Any Further", 1000)

    def redoContent(self):
        if(len(self.redoIterations) > 0):
            p = QPainter(self.mainImage)
            p.drawPixmap(0, 0, self.mainImage.width(), self.mainImage.height(), self.redoIterations[-1])
            self.undoIterations.append(self.redoIterations.pop())
            p.end()
            self.updateImage()
        else:
            self.statusbar.showMessage("Cannot Redo Any Further", 1000)

    def helpContent(self):
        self.browser = QWebEngineView()
        self.browser.load(QUrl().fromLocalFile(os.path.dirname(__file__) + "/index.html"))
        self.browser.setWindowTitle("Help Content")
        self.browser.show()

    def about(self):
        webbrowser.open("https://python.org")

    def resolutionChange(self):
        self.rLabel.setText(f"{self.mainImage.width()} x {self.mainImage.height()} px")
    
    def zoomChange(self):
        self.zoomFactor = self.zSlider.value()
        self.zLabel.setText(f"Zoom: {int(self.zoomFactor * 100)}%")

    def brushSliderUpdate(self):
        self.brushSizeLabel.setText(f"Size:\n{self.brushSizeSlider.value()} px")

    def switchDrawMode(self, mode):
        self.drawMode = mode
        print("Drawmode switched to DrawMode" + str(mode) + ".")

    def preferences(self):
        self.pWindow = preferencesWindow()
        self.pWindow.show()

    def updateImage(self):
        self.labelImage.setPixmap(QPixmap.fromImage(self.mainImage))
        self.update()

    def profileProgram(self):
        cProfile.run('re.compile("foo|bar")')

    def _connectActions(self):
        # Connect File actions
        self.newAction.triggered.connect(self.newFile)
        self.openAction.triggered.connect(self.openFile)
        self.saveAction.triggered.connect(self.saveFile)
        self.settingsAction.triggered.connect(self.preferences)
        self.exitAction.triggered.connect(self.close)
        # Connect Edit actions
        self.copyAction.triggered.connect(self.copyContent)
        self.pasteAction.triggered.connect(self.pasteContent)
        self.cutAction.triggered.connect(self.cutContent)
        self.clearAction.triggered.connect(self.clearContent)
        self.undoAction.triggered.connect(self.undoContent)
        self.redoAction.triggered.connect(self.redoContent)
        # Connect Help actions
        self.helpContentAction.triggered.connect(self.helpContent)
        self.aboutAction.triggered.connect(self.about)
        self.openRecentMenu.aboutToShow.connect(self.populateOpenRecent)
        # Connect Miscellaneous actions
        self.colorPickerAction.triggered.connect(self.colorPicker)
        self.colorPickerActionB.triggered.connect(self.colorPickerB)
        self.profileAction.triggered.connect(self.profileProgram)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    sys.exit(app.exec_())
