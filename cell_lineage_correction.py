import os
import pandas as pd
import json
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui

from PyQt5.QtCore import Qt, pyqtSignal, QPoint
from PyQt5.QtGui import QPainter, QFont, QColor

# This is for the action of adding a cell. It is not currently useful.
# In a nutshell, it is a label that emits a signal when clicked
# The signal contains the position of the click
# The position can then be used to add a cell at that location
class ClickableLabel(QLabel):
    clicked = pyqtSignal(QPoint)  # Signal to emit when the label is clicked
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton:
            self.clicked.emit(event.pos())

# This is the main window class
class CellLineageCorrection(QMainWindow):

    # This is the constructor for the class
    def __init__(self):
        super(CellLineageCorrection, self).__init__()
        uic.loadUi('Cell_Lineage_Correction.ui', self)  # This loads the promoted ClickableLabel
        self.show() # This shows the window
        self.Image_Container.clicked.connect(self.image_clicked) # This connects the signal to the slot

        self.current_file = "default.png" # This is the default image to load on startup, its just a black screen
        pixmap = QtGui.QPixmap(self.current_file) # Load the current image
        pixmap = pixmap.scaled(self.width(), self.height()) # Scale it to the new window size
        self.Image_Container.setPixmap(pixmap) # Set the image to the container
        self.Image_Container.setMinimumSize(1, 1) # Set the minimum size of the container to 1x1 pixels

        # These are the variables that will be used to keep track of the data
        self.file_list = None # This is the list of files in the directory that you choose
        self.file_counter = None # This is the index of the current file in the file_list
        self.image_num = None # This is the size of the file_list
        self.current_csv = None # This is the path to the current csv file
        self.csv_data = None # This is the data from the current csv file in a pandas dataframe
        self.step_map = None # This is a dictionary that maps the step number to the index of the row in the csv file. Check step_map.json for an example of what it looks like
        self.chosen_cell = None # This is the cell that is currently selected in the Choose_Cell combobox

        # These connect the buttons in the file tab to their respective functions
        self.actionOpen_Image.triggered.connect(self.open_image) # Currently, it is better to open a Directory as connecting to a CSV file requires a CSV with the same numhber of images as cells in the CSV. Adding a random image might cause the program to crash.
        self.actionOpen_Directory.triggered.connect(self.open_directory)
        self.actionOpen_CSV.triggered.connect(self.open_csv)
        self.actionSave.triggered.connect(self.save_csv)

        # These connect the buttons to their respective functions
        self.Right_Button.clicked.connect(self.next_image)
        self.Left_Button.clicked.connect(self.previous_image)
        self.Choose_Cell.currentIndexChanged.connect(self.update_chosen_cell)
        self.Change_Cell_Info.clicked.connect(self.change_cell_info)
        self.IsolateCell.stateChanged.connect(self.redraw_image)
        
        # This is the default um_per_pixel value for the images
        self.um_per_pixel = 0.144

    # This function is called when the window is resized
    def resizeEvent(self, event):
        try:
            pixmap = QtGui.QPixmap(self.current_file)  # Load the current image
            self.Image_Container.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio))  # Scale it to the new window size
            self.draw_cell_ids() # Redraw the cell IDs
            return
        except:
            pixmap = QtGui.QPixmap("default.png")
    
    # This function is called for opening a singular image (do not recommend using this for now)
    def open_image(self):
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Image Files (*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff)", options=options)
        
        if filename != "":
            self.current_file = filename
            pixmap = QtGui.QPixmap(self.current_file)
            pixmap = pixmap.scaled(self.width(), self.height())
            self.Image_Container.setPixmap(pixmap)
        else:
            print("No file selected")

    # This function is called for opening a directory of images
    def open_directory(self):
        directory = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if directory != "":
            self.file_list = [directory + "/" + f for f in os.listdir(directory) if f.endswith(".png") or f.endswith(".jpg") or f.endswith(".jpeg") or f.endswith(".bmp") or f.endswith(".gif") or f.endswith(".tif") or f.endswith(".tiff")]
            self.image_num = len(self.file_list) # This is the number of images in the directory
            self.file_counter = 0 # This is the index of the current image in the file_list
            self.update_step_label() # This updates the step label to the current step number
            self.current_file = self.file_list[self.file_counter] # This sets the current image the first image in the file_list
            pixmap = QtGui.QPixmap(self.current_file) # This loads the current image
            self.Image_Container.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio)) # This scales the image to the window size
        else:
            print("No directory selected")

    # This function is called for opening a CSV file that links to the directory selected
    def open_csv(self):
        if self.file_list is None:
            print("Please open an image directory first")
            return

        # Opens a dialog box to select a CSV file
        options = QFileDialog.Options()
        filename, _ = QFileDialog.getOpenFileName(self, "Open CSV", "", "CSV Files (*.csv)", options=options)

        # If the user cancels the dialog box, filename will be an empty string
        if filename != "":
            temp_data = pd.read_csv(filename)
            value = temp_data.iloc[-1, 0] # This is the number of images in the CSV file
            
            # This checks if the number of images in the CSV file matches the number of images in the directory
            if value != self.image_num:
                print("CSV file does not match the number of images in the directory, please choose the correct directory or CSV file")
                return
            
            # This creates a dictionary that maps the step number to the index of the row in the csv file
            temp_map = {}
            for i in range(temp_data.shape[0]):
                step_num = temp_data.iloc[i, temp_data.columns.get_loc("stepNum")]
                cell_id = temp_data.iloc[i, temp_data.columns.get_loc("id")]
                parent_id = temp_data.iloc[i, temp_data.columns.get_loc("parent_id")]
                pos = temp_data.iloc[i, temp_data.columns.get_loc("pos")]

                if step_num not in temp_map:
                    temp_map[step_num] = {
                        "index": i,
                        "cell_ids": {cell_id: {"index": i, "parent_id": parent_id, "pos": pos}}
                    }
                else:
                    temp_map[step_num]["cell_ids"][cell_id] = {"index": i, "parent_id": parent_id, "pos": pos}
        else:
            print("No CSV file selected")
            return

        self.current_csv = filename
        self.csv_data = temp_data
        self.step_map = temp_map

        self.update_cell_list()
        self.draw_cell_ids()

    # This function updates the chosen_cell variable to the current selection in the Choose_Cell combobox
    def update_chosen_cell(self):
        # Get the current selection in the combobox
        self.chosen_cell = self.Choose_Cell.currentText()
        self.Cell_ID.setText(self.chosen_cell)

        # Update the Cell_Parent widget
        if self.chosen_cell:  # Check if self.chosen_cell is not an empty string
            try:
                chosen_cell_as_int = int(self.chosen_cell)  # Attempt to convert to int
                parent_id_info = self.step_map[self.file_counter + 1]["cell_ids"][chosen_cell_as_int]["parent_id"]
                self.Cell_Parent.setText(str(parent_id_info))  # Ensure it's converted to a string
                # print(self.chosen_cell)
            except (ValueError, KeyError):
                # Handle the case where chosen_cell cannot be converted to an integer
                # or when the converted int is not a key in the dictionary
                print(f"Invalid cell id: {self.chosen_cell}")
                self.Cell_Parent.clear()  # Clear the text if there's an invalid or no selection
        else:
            # If chosen_cell is an empty string, clear the Cell_ID and Cell_Parent widgets
            self.Cell_ID.clear()
            self.Cell_Parent.clear()

    # This function updates the step label to the current step number
    def update_step_label(self):
        new_text = "Step #" + str(self.file_counter + 1)
        self.Step_Num.setText(new_text) # This updates the label to the current step number

    # This function updates the Choose_Cell combobox to the current cells in the step_map
    def update_cell_list(self):
        if self.step_map is not None:
            # Get the cell IDs for the current step
            cell_index = self.step_map[self.file_counter + 1]
            cell_ids = [str(cell_id) for cell_id in cell_index["cell_ids"].keys()]  # Convert each cell_id to a string
            
            # Sort the cell IDs in ascending order
            cell_ids.sort(key=int)  
            
            # Save the current chosen_cell
            temp_chosen_cell = self.chosen_cell

            # Update the Choose_Cell combobox
            self.Choose_Cell.clear()
            self.Choose_Cell.addItems(cell_ids)

            # Update the chosen_cell variable to the previous one to keep the last cell selected, otherwise, set it to the first index
            if temp_chosen_cell in cell_ids:
                self.Choose_Cell.setCurrentText(temp_chosen_cell)
            else:
                self.Choose_Cell.setCurrentIndex(0)
                self.chosen_cell = self.Choose_Cell.currentText() # Update chosen_cell to the first item in the list

    # This function is called when the user clicks the right arrow button
    def next_image(self):
        if self.file_counter is not None and self.file_list is not None:
            self.file_counter += 1
            if self.file_counter >= len(self.file_list):
                self.file_counter = 0  # Reset to the first image if we've reached the end
            self.update_step_label()  # Update the label text
            self.update_cell_list()
            self.current_file = self.file_list[self.file_counter]
            pixmap = QtGui.QPixmap(self.current_file)
            self.Image_Container.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio))
            self.draw_cell_ids()
    
    # This function is called when the user clicks the left arrow button
    def previous_image(self):
        if self.file_counter is not None and self.file_list is not None:
            self.file_counter -= 1
            if self.file_counter < 0:
                self.file_counter = len(self.file_list) - 1  # Wrap around to the last image
            self.update_step_label()  # Update the label text
            self.update_cell_list()
            self.current_file = self.file_list[self.file_counter]
            pixmap = QtGui.QPixmap(self.current_file)
            self.Image_Container.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio))
            self.draw_cell_ids()

    # This function draws the cell IDs on the image
    def draw_cell_ids(self):
        if self.file_counter is not None and self.step_map:
            pixmap = QtGui.QPixmap(self.current_file)
            painter = QPainter(pixmap)
            painter.setPen(QColor(255, 255, 255))  # Set the color of the pen to white
            painter.setFont(QFont('Arial', 5))  # Set the font size

            # If the IsolateCell checkbox is checked, draw only the chosen cell
            if self.IsolateCell.isChecked() and self.chosen_cell:
                try:
                    chosen_cell_as_int = int(self.chosen_cell)
                    if chosen_cell_as_int in self.step_map[self.file_counter + 1]["cell_ids"]:
                        cell_data = self.step_map[self.file_counter + 1]["cell_ids"][chosen_cell_as_int]
                        pos = cell_data["pos"].strip('[]').split(', ')
                        x = int(round(float(pos[0]) / self.um_per_pixel))
                        y = int(round(float(pos[1]) / self.um_per_pixel))
                        painter.drawText(x, y, str(chosen_cell_as_int))
                except ValueError:
                    # Handle the case where chosen_cell is not an integer
                    pass
            else:
                # If the checkbox is not checked, draw all cell IDs
                for cell_id, cell_data in self.step_map[self.file_counter + 1]["cell_ids"].items():
                    pos = cell_data["pos"].strip('[]').split(', ')
                    x = int(round(float(pos[0]) / self.um_per_pixel))
                    y = int(round(float(pos[1]) / self.um_per_pixel))
                    painter.drawText(x, y, str(cell_id))

            painter.end()
            self.Image_Container.setPixmap(pixmap.scaled(self.width(), self.height(), Qt.KeepAspectRatio))

    # This function is called when the image is clicked, uninportant for now
    def image_clicked(self, pos):
        self.collect_cell_info(pos)
        position = [pos.x() * self.um_per_pixel, pos.y() * self.um_per_pixel]
        position = str(position)
        print(position)

    # This function is called when the user clicks on the image to add a cell
    def collect_cell_info(self, pos):
        cell_id, okPressed_id = QInputDialog.getText(self, "Cell ID","Enter Cell ID:", QLineEdit.Normal, "")
        if okPressed_id and cell_id:
            parent_id, okPressed_parent = QInputDialog.getText(self, "Parent ID","Enter Parent ID (default 0):", QLineEdit.Normal, "0")
            if not okPressed_parent:  # If the user cancels the parent_id dialog, we set it to 0 by default
                parent_id = "0"
            # Save the data
            self.save_cell_info(int(cell_id), int(parent_id), pos)

    # This function saves the cell information to the step_map and csv_data, also unimportant for now
    def save_cell_info(self, cell_id, parent_id, pos):
        position = [pos.x() * self.um_per_pixel, pos.y() * self.um_per_pixel]
        position = str(position)
        print(position)
        
        # Update step_map
        step_num = self.file_counter + 1
        # if step_num not in self.step_map:
        #     self.step_map[step_num] = {"index": len(self.step_map) + 1, "cell_ids": {}}
        
        self.step_map[step_num]["cell_ids"][cell_id] = {
            "index": len(self.step_map[step_num]["cell_ids"]) + 1, # This is problematic for csv insertion. We need to find a way to keep track of the index for all of the cells that proceed this one. Currently unused so lets keep it as is.
            "parent_id": str(parent_id),
            "pos": position
        }

        # Update csv_data - create a new row with the new cell information
        # new_row = {
        #     'Step_Num': step_num,
        #     'Cell_ID': cell_id,
        #     'Parent_ID': parent_id,
        #     'Position': position  # formatted as needed for CSV
        # }
        # self.csv_data = self.csv_data.append(new_row, ignore_index=True)

        # Redraw the image with the new cell
        print(self.step_map[step_num])
        self.draw_cell_ids()

        #save the new csv_data to file
        # self.csv_data.to_csv(self.current_csv, index=False)

    # This function is called when the user clicks the Change Cell Info button
    def change_cell_info(self):
        # Check if a cell is selected
        if not self.chosen_cell:
            QMessageBox.warning(self, "No Cell Selected", "Please select a cell to change.")
            return
        
        new_cell_id = self.Cell_ID.text()
        new_parent_id = self.Cell_Parent.text()
        
        # Convert inputs to proper types
        try:
            new_cell_id = int(new_cell_id)
        except ValueError:
            QMessageBox.warning(self, "Invalid Cell ID", "Please enter a valid cell ID.")
            return

        try:
            new_parent_id = int(new_parent_id)
        except ValueError:
            QMessageBox.warning(self, "Invalid Parent ID", "Please enter a valid parent ID.")
            return
        
        current_step = self.file_counter + 1
        old_cell_id = int(self.chosen_cell)

        # Update step_map 
        if new_cell_id != old_cell_id:
            print("cell_id changed")
            for step, step_data in self.step_map.items():
                # Edits only current step and future steps
                if step < current_step:
                    continue
                cell_ids = list(step_data["cell_ids"].keys())  # Create a list of keys to iterate over
                for cell_id in cell_ids:
                    if cell_id == old_cell_id:
                        # Change all cell_IDs that are equal to the incorrect cell you are correcting, changes to the new_cell_id
                        step_data["cell_ids"][new_cell_id] = step_data["cell_ids"].pop(old_cell_id)

                    elif step_data["cell_ids"][cell_id]["parent_id"] == old_cell_id:
                        # Because you change the old_cell_id to the new_cell_id, you need to change the parent for all of its children
                        step_data["cell_ids"][cell_id]["parent_id"] = new_cell_id
                        
        if new_parent_id != self.step_map[current_step]["cell_ids"][new_cell_id]["parent_id"]:
            print("parent_id changed")
            # Change the parent ID for all cells with the same cell ID
            for step, step_data in self.step_map.items():
                # Edits only current step and future steps
                if step < current_step:
                    continue
                cell_ids = list(step_data["cell_ids"].keys())
                for cell_id in cell_ids:
                    if cell_id == new_cell_id:
                        step_data["cell_ids"][cell_id]["parent_id"] = new_parent_id

        # Redraw the image with updated cell IDs
        self.draw_cell_ids()

        # Update the UI components to reflect the changes
        self.update_cell_list()
        self.Choose_Cell.setCurrentIndex(self.Choose_Cell.findText(str(new_cell_id)))
        # self.update_chosen_cell()

    # This function is called when the IsolateCell checkbox is checked or unchecked
    def redraw_image(self):
        self.draw_cell_ids()

    # This function is called when the user clicks the Save button
    def save_csv(self):
        if self.step_map is None or self.csv_data is None:
            QMessageBox.warning(self, "No Data", "There is no data to save.")
            return

        # Iterate through each step in step_map and update csv_data
        for step_num, step_info in self.step_map.items():
            for cell_id, cell_info in step_info['cell_ids'].items():
                index = cell_info['index']  # Get the index of the row in the csv_data
                # Update the csv_data DataFrame at the specified index
                self.csv_data.iloc[index, self.csv_data.columns.get_loc("id")] = cell_id
                self.csv_data.iloc[index, self.csv_data.columns.get_loc("parent_id")] = cell_info['parent_id']

        # print("csv_data: ", self.csv_data, sep="\n")
        # Use a file dialog to get the location and name of the file to save
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self, "Save CSV", "", "CSV Files (*.csv)", options=options)
        if fileName:
            # Save the updated DataFrame to a new CSV file
            self.csv_data.to_csv(fileName, index=False)
            QMessageBox.information(self, "Save Successful", f"File saved to {fileName}")


# This is the main function that runs the program
def main():
    app = QApplication([])
    window = CellLineageCorrection()
    app.exec_()

if __name__ == '__main__':
    main()