import sys
import os
import pdf2image
import PIL
from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtGui import QImage, QPainter, QKeySequence
from PyQt5.QtCore import Qt, QRect, QProcess

basePath = os.path.abspath(os.path.dirname(__file__)) + "/"

# Class to draw bounding box on image
class boundaryDraw(QtWidgets.QLabel):
    # Initialize the drawing canvas for the boundary
    def __init__(self, path):
        super().__init__()
        self.image = QImage(path)
        self.startPos = None
        self.rect = QRect()
        self.drawing = False
        self.show()

    # Handle mouse press event to begin drawing boundary
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and not self.drawing:
            self.startPos = event.pos()
            self.rect = QRect(self.startPos, self.startPos)
            self.drawing = True
            self.update()

    # Handle mouse move event to draw boundary
    def mouseMoveEvent(self, event):
        if self.drawing == True:
            self.rect = QRect(self.startPos, event.pos())
            self.update()

    # Handle mouse release event to stop drawing rectangle
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = False

    # Handle painting event to draw the rectangle
    def paintEvent(self, event):
        pen = QtGui.QPen()
        pen.setWidth(3)
        pen.setColor(QtGui.QColor(255, 0, 0))

        brush = QtGui.QBrush()
        brush.setColor(QtGui.QColor(255, 0, 0))
        brush.setStyle(Qt.NoBrush)

        painter = QPainter(self)
        painter.drawImage(0, 0, self.image)
        painter.setBrush(brush)
        painter.setPen(pen)
        if not self.rect.isNull():
            painter.drawRect(self.rect)
        painter.end()

    # Get coordinates of the drawn rectangle for cropping purposes
    def get_coords(self, height_percent = 0):
        coordArr = [
            self.rect.topLeft(),
            self.rect.topRight(),
            self.rect.bottomRight(),
            self.rect.bottomLeft(),
        ]
        for coord in coordArr:
            if "-" in str(coord):
                return ["None"]
        rawCoord = ["(" + str(int(coord.x() + (coord.x() * height_percent))) + "," + str(int(coord.y() + (coord.y() * height_percent))) + ")" for coord in coordArr]
        adjustedCoords = []
        for i in range(4):
            # left
            if i == 0:
                adjustedCoords.append(rawCoord[i].split(",")[0][1:])
            # top
            elif i == 1:
                adjustedCoords.append(rawCoord[i].split(",")[1][:-1])
            # right
            elif i == 2:
                adjustedCoords.append(str(self.image.width() - int(rawCoord[i].split(",")[0][1:])))
            # bottom
            else:
                adjustedCoords.append(str(self.image.height() - int(rawCoord[i].split(",")[1][:-1])))
        return adjustedCoords

# Class for popup dialog to draw boundary box on image
class boundaryDialog(QtWidgets.QDialog):
    def __init__(self, path, gui):
        super(boundaryDialog, self).__init__()
        if gui.firstTime:
            gui.firstTime = False
            msg = QtWidgets.QMessageBox()
            msg.setWindowTitle("How To Use")
            msg.setText("Close the image window or press ESCAPE\nto save your boundary and move on to \nthe next file.\n\nPress CTRL + X to exit after current image.")
            msg.exec_()
        self.exitEarly = QtWidgets.QShortcut(QKeySequence("Ctrl+X"), self)
        self.exitEarly.activated.connect(gui.set_early)
        self._scene = QtWidgets.QGraphicsScene(self)
        self._view = QtWidgets.QGraphicsView(self._scene)
        self.scroll_area = QtWidgets.QScrollArea(widgetResizable=True)
        self.draw_widget = boundaryDraw(path)
        self.draw_widget.setMinimumWidth(self.draw_widget.image.width())
        self.draw_widget.setMinimumHeight(self.draw_widget.image.height())
        self.scroll_area.setWidget(self.draw_widget)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.lay = QtWidgets.QVBoxLayout(self)
        self.lay.addWidget(self.scroll_area)
        self.resize(self.draw_widget.image.width(), self.draw_widget.image.height())
        self.setWindowTitle(path.split("/")[-1])

# Class to handle PDF page selection dialog
class PDFDialog(QtWidgets.QDialog):
    def __init__(self, pages):
        super(PDFDialog, self).__init__()
        self.pageNum = QtWidgets.QComboBox()
        for i in range(len(pages)):
            self.pageNum.addItem(str(i+1))
        self.button_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)
        self.button_box.accepted.connect(self.accept)
        layout = QtWidgets.QFormLayout()
        layout.setFieldGrowthPolicy(QtWidgets.QFormLayout.AllNonFixedFieldsGrow)
        layout.addRow('Page', self.pageNum)
        layout.addWidget(self.button_box)

        self.setLayout(layout)
        self.setWindowTitle("Select Page")
        self.setMinimumWidth(350)

# Main Ui class
class Ui(QtWidgets.QDockWidget):
    # Set Ui default variables
    selectedFiles = {}
    early = False
    IMAGE_TYPES = {"jpg", "png", "ttf", "pdf"}
    firstTime = True
    temporaries = []

    # Initialize Ui
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('menu.ui', self)
        self.show()

    # Retrieve paths of currently selected files
    def retrieve_paths(self):
        return [value[0] for value in self.selectedFiles.values()]

    # Retrieve files based on radio button selected
    def get_file_selection(self):
        # Return all files if all files radio button is checked
        if self.allFilesRadiobutton.isChecked():
            return [self.fileList.item(i) for i in range(self.fileList.count())]
        # Otherwise, return only selected files
        else:
            return self.fileList.selectedItems()

    # Add files to the file queue
    def add_files(self):
        dialog = QtWidgets.QFileDialog()
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFiles)
        # If the user did not cancel the dialog window, attempt to add files
        if dialog.exec():
            filePaths = dialog.selectedFiles()
            for filePath in filePaths:
                # If the file path is not already in the file queue...
                if filePath not in self.retrieve_paths():
                    # ...step backwards through the path and add the shortest
                    # possible string to the file queue so there is no duplicate
                    # Ex: File Queue
                    # my_book.pdf
                    # /old/my_book.pdf
                    splitPath = filePath.split('/')
                    for split in range(len(splitPath) + 1):
                        split += 1
                        fileName = '/'.join(splitPath[-split:])
                        if fileName not in self.selectedFiles.keys():
                            # Add file to file queue with default language and boundary
                            self.selectedFiles[fileName] = [filePath, "jpn", "None"]
                            self.fileList.addItem(fileName + " / Horizontal / None")
                            if fileName.split('.')[1] in self.IMAGE_TYPES:
                                self.templateSelection.addItem(fileName)
                            break

    # Remove files from the file queue
    def remove_files(self):
        curFiles = self.fileList.selectedItems()
        for item in curFiles:
            if item.text().split(' ')[0] in self.selectedFiles:
                del self.selectedFiles[item.text().split(' ')[0]]
                self.fileList.takeItem(self.fileList.row(item))
                index = self.templateSelection.findText(item.text().split(' ')[0])
                # If removed file was template, reset template option
                if index != -1:
                    self.templateSelection.setCurrentIndex(0)
                    self.templateSelection.removeItem(index)

    # Swap the text direction of the selected files
    def swap_text_direction(self):
        curFiles = self.get_file_selection()
        for item in curFiles:
            itemInfo = item.text().split(' / ')
            # If horizontal, set to vertical
            if itemInfo[1] == 'Horizontal':
                self.selectedFiles[itemInfo[0]][1] = self.selectedFiles[itemInfo[0]][1].replace('jpn', 'jpn_vert')
                item.setText(item.text().replace('Horizontal', 'Vertical'))
            # If vertical, set to horizontal
            else:
                self.selectedFiles[itemInfo[0]][1] = self.selectedFiles[itemInfo[0]][1].replace('jpn_vert', 'jpn')
                item.setText(item.text().replace('Vertical', 'Horizontal'))

    # Set the crop boundary of the selected files
    def set_crop_boundary(self):
        curFiles = self.get_file_selection()
        # If a template image is selected, only open the template for drawing
        if self.templateSelection.currentText() != "None":
            self.boundaryWindow = boundaryDialog(self.selectedFiles[self.templateSelection.currentText()][0], self)
            self.boundaryWindow.exec_()
            coords = ", ".join(self.boundaryWindow.draw_widget.get_coords())
            for item in curFiles:
                itemInfo = item.text().split(' / ')
                # Set boundary for all selected files based on template
                if self.selectedFiles[itemInfo[0]][0].split('.')[1] in self.IMAGE_TYPES:
                    self.selectedFiles[itemInfo[0]][2] = coords
                    item.setText(item.text().replace(itemInfo[-1], coords))
        # Else, if no template, draw a boundary on each file
        else:
            for item in curFiles:
                # Detect if the user requested early exiting for drawing bounds
                if self.early:
                    self.early = False
                    self.exitEarly = QtWidgets.QShortcut(QKeySequence(), self)
                    break
                # Set a height percent for boundary scaling
                self.height_percent = 0
                fileName = ""
                itemInfo = item.text().split(' / ')
                path = self.selectedFiles[itemInfo[0]][0]
                # Convert specified PDF page into an image for drawing
                if path.split('.')[1] in self.IMAGE_TYPES:
                    if path.split('.')[1] == "pdf":
                        pages = pdf2image.convert_from_path(path, dpi=200)
                        pageSelect = PDFDialog(pages)
                        pageSelect.exec_()
                        fileName = "{}.png".format(os.getpid())
                        pages[int(pageSelect.pageNum.currentText())-1].save(fileName, dpi=(300, 300))
                        fixed_height = 1080
                        image = PIL.Image.open(fileName)
                        # If the image is too large, scale it down
                        if image.size[1] > fixed_height:
                            self.height_percent = (fixed_height / float(image.size[1]))
                            width_size = int((float(image.size[0]) * float(self.height_percent)))
                            image = image.resize((width_size, fixed_height), PIL.Image.NEAREST)
                            image.save(fileName)
                            path = basePath + fileName
                    self.boundaryWindow = boundaryDialog(path, self)
                    self.boundaryWindow.exec_()
                    # Remove temporary file if one was created
                    if fileName != "":
                        os.remove(fileName)
                    coords = ", ".join(self.boundaryWindow.draw_widget.get_coords(self.height_percent))
                    self.selectedFiles[itemInfo[0]][2] = coords
                    item.setText(item.text().replace(itemInfo[-1], coords))

    # Find checked radio button
    def find_checked(self, radioGroup):
        for item in radioGroup.buttons():
            if item.isChecked():
                return item.text()

    # Toggle all inputs from enabled to disabled and vice versa
    def toggle(self):
        for item in self.allInputs:
            if item.isEnabled():
                item.setEnabled(False)
            else:
                item.setEnabled(True)

    # Set exit early attribute to true
    def set_early(self):
        self.early = True

    # Run ocr_flashcard.py on user's files
    def make_flashcards(self):
        # Reset progress displays
        for display in self.displays:
            display.setText("")

        # Get options
        options = [
            self.find_checked(self.kanjiFlashcardOptionsGroup),
            self.find_checked(self.wordFlashcardOptionsGroup),
            self.find_checked(self.sentenceFlashcardOptionsGroup)
        ]

        # Setup options into argumets to be passed
        for option in range(len(options)):
            if options[option] == "Recall + Recognition" or options[option].find("Random") > 0:
                options[option] = "2"
            elif options[option] == "Recognition" or options[option] == "Each word":
                options[option] = "1"
            elif options[option] == "None":
                options[option] = "0"
                if option == 0:
                    self.flashCreatedKanjiDisplayLabel.setText("None")
                elif option == 1:
                    self.flashCreatedWordDisplayLabel.setText("None")
                else:
                    self.flashCreatedSentenceDisplayLabel.setText("None")

        if self.allowDupesCheckbox.isChecked():
            options[1] += "1"
        else:
            options[1] += "0"
        if options[2].find("Random"):
            options[2] += self.randomNumInput.text()

        # Begin creation of process to run script
        self.process = QProcess()
        self.process.setProgram("python")
        args = [basePath + "ocr_flashcard.py"]
        for file in self.selectedFiles.values():
            args.append(file[0] + "--" + file[1] + "--" + "".join(file[2].split(' ')))
        for option in options:
            args.append(option)
        args.append(str(self.enhanceCheckbox.isChecked()))
        self.process.setArguments(args)
        # Setup output reading for real-time progress reporting
        self.process.readyReadStandardError.connect(self.on_readyReadStandardError)
        self.process.readyReadStandardOutput.connect(self.on_readyReadStandardOutput)
        self.toggle()
        self.curStatusLabel.setText("Working...")
        self.process.start()

    # Read output from ocr_flashcard and set as update text
    def on_readyReadStandardOutput(self):
        out = self.process.readAllStandardOutput().data().decode().strip()
        infoList = out.split("\n")
        for info in infoList:
            info = info.split(",")
            if info[0] == "kanji":
                self.flashCreatedKanjiDisplayLabel.setText(str(info[1]))
            elif info[0] == "word":
                self.flashCreatedWordDisplayLabel.setText(info[1])
            elif info[0] == "sentence":
                self.flashCreatedSentenceDisplayLabel.setText(info[1])
            elif info[0] == "name":
                self.curWorkingFileDisplay.setText(info[1].split("/")[-1].split("--")[0])
            elif info[0] == "file":
                self.numFileRemDisplay.setText(info[1])
                cur = self.fileList.takeItem(0)
                del self.selectedFiles[cur.text().split(" / ")[0]]
                index = self.templateSelection.findText(cur.text().split(" / ")[0])
                self.templateSelection.removeItem(index)
            elif info[0] == "tmp":
                if info[1] == "a":
                    self.temporaries.append(info[2])
                elif info[1] == "d":
                    self.temporaries.remove(info[2])
            elif info[0] == "Done!":
                self.toggle()
                self.curStatusLabel.setText("Idle")
            # If output was unexpected, print it to console
            else:
                print("OUT: " + out)

    # Read errors from ocr_flashcard
    def on_readyReadStandardError(self):
        err = self.process.readAllStandardError().data().decode().strip()
        self.curWorkingFileDisplay.setText(err)
        print(err)

    # Clean up files if process is stopped via "Stop" button
    def cleanup(self):
        self.curStatusLabel.setText("Stopping...")
        self.process.terminate()
        for item in self.temporaries:
            print(item)
            try:
                os.remove(item)
            except IOError:
                continue
        for display in self.displays:
            display.setText("")
        self.toggle()
        self.curStatusLabel.setText("Idle")

# Initialize applcation
app = QtWidgets.QApplication(sys.argv)
window = Ui()
# Setup all inputs variable
window.allInputs = list(window.findChildren(QtWidgets.QAbstractButton))
window.allInputs.append(window.randomNumInput)
window.allInputs.append(window.templateSelection)
# Setup displays variable
window.displays = [
    window.flashCreatedKanjiDisplayLabel,
    window.flashCreatedWordDisplayLabel,
    window.flashCreatedSentenceDisplayLabel,
    window.curWorkingFileDisplay,
    window.numFileRemDisplay
]
# Connect buttons to respective functions
window.addFileButton.clicked.connect(window.add_files)
window.removeFileButton.clicked.connect(window.remove_files)
window.swapTextDirectionButton.clicked.connect(window.swap_text_direction)
window.setCropBoundaryButton.clicked.connect(window.set_crop_boundary)
window.startButton.clicked.connect(window.make_flashcards)
# Disable stop button until start is pressed
window.stopButton.setEnabled(False)
# Add default template item
window.templateSelection.addItem("None")
# Attatch stop button to function
window.stopButton.clicked.connect(window.cleanup)
# Execute and exit app
sys.exit(app.exec_())