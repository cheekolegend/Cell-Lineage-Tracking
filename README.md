# Cell-Lineage-Tracking

## Overview
This application, developed in Python using PyQt5, assists in managing and correcting cell lineage data, primarily in image files. It offers functionalities such as viewing and navigating through images, editing cell information in CSV files, and visualizing cell lineage corrections directly on the images.

## Features
- Image and Directory Loading: Open individual images or a directory of images.
- CSV File Integration: Load and edit CSV files containing cell lineage data.
- Navigational Controls: Browse through images using forward and backward controls.
- Cell Information Editing: Modify cell IDs and parent IDs directly on the GUI.
- Visual Feedback: View changes in real-time on the images.
- Data Saving: Save your modifications back to the CSV file.
- Scalable Image Display: Images are automatically scaled to fit the window size

## Installation
To run this application, ensure you have the following prerequisites installed:

- Python 3.x
- PyQt5
- pandas

Install dependencies using:
pip install PyQt5 pandas

Editing the .ui file is made easier with the Qt designer application. Here is a tutorial on the basics
https://www.youtube.com/watch?v=h_DVfsD9PKI

## Usage
To start the application, run the main script:
python cell_lineage_correction.py

## Basic Operations
Open a directory: Use 'Open Directory' from the File menu. 
Load CSV File: After opening an image directory, load the corresponding CSV file containing cell data.
Navigate Images: Use the left and right buttons to navigate through the images.
Edit Cell Data: Select a cell from the dropdown and edit its information, such as ID and parent ID.
View Changes: The image display updates in real-time to reflect any modifications.
Save Data: Save your changes back to the CSV file using the 'Save' option.

## Limitations
The application currently supports only certain image formats (.png, .jpg, .jpeg, .bmp, .gif, .tif, .tiff).
The number of images in the directory should match the number of entries in the CSV file.
High-resolution images might affect performance due to scaling.

## Contributing
Contributions to improve the application are welcome. Please follow standard pull request procedures for contributions.
