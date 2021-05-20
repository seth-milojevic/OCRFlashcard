# **OCRFlashcard**

Automatic flashcards from your favorite media

## Table of Contents

- [Description](#Description)
- [Installation](#Installation)
- [Usage](#Usage)
    - [GUI Usage](#GUI-Usage)
    - [Command Line Usage](#Command-Line-Usage)
    - [Importing Flashcards into Anki](#Importing-Flashcards-into-Anki)
- [Credits](#Credits)
- [License](#License)

## Description

OCRFlashcard is an application designed to create [Anki](https://apps.ankiweb.net/) flashcards out of images, PDFs, and text files containing Japanese text by utilizing pytesseract. 

## Installation

First, the repository must be downloaded and a working python installation added to the user's PATH (version 3.9+). Once the repository is downloaded, navigate to it using the console. Once inside the directory, run the following command:

    pip install -r requirements.txt

After running the command, navigate to the data folder within the directory. From here, simply run

    python ocr_flashcard_gui

to open the GUI version of the program, or

    python ocr_flashcard

along with the appropriate arguments for the command line version.

## Usage

### GUI Usage

Utilizing the GUI is the recommended way to use this application.

#### Starting the Program

To start the program, simply run:

    python ocr_flashcard_gui.py

Make sure you have a working python version added to your path!

#### Adding Files

Users can add files by pressing the "Add Files" button. This will open the file explorer where users can select one or more files to add to the file queue.

#### Removing Files

Users may remove files by pressing the "Remove Files" button. This button will remove all files in the file queue that are selected. Users can select files in the file queue by clicking on them. Pressing the "Remove Files" button while no files are selected will do nothing.

#### Changing OCR Options

OCR options change the way that the files are processed for their text. Users may target every file in the file queue at once by selecting the "For all files" radio button. Alternatively, users may select the "For selected file(s)" button to target only the selected files in the file queue.

##### Swapping Text Direction

By default, added files are set with a horizontal text direction (Left -> Right). Should Users want to change this, Users may press the "Swap Text Direction" button. This will set the text direction to vertical (Up -> Down).

##### Setting a Boundary Box

Users may draw a boundary box around their image files so that the application can better detect and extract the text from the source. 

*Image File Types (.jpg, .png, .ttf)* - Image file types can have individual borders per image. Simply select the desired images from the queue and press the "Swap  Boundary Box" button. Once the image opens, users can click and drag the mouse to draw a box around the target text.

*PDF Files* - PDF files will have the same boundary box applied to all of their pages. Users can select which page Users draw the bounding box on after pressing the "Set Boundary Box" button. Currently, setting a boundary box on each page of a PDF is not supported. If this is something the user would like to do, it is recommended that the user transforms the PDF into images first.

No other file types will allow boundaries to be drawn on them, and will be read as is.

If the user decides they would like to stop drawing boundary boxes early, they can press Control + X while the image is open. Once the user closes that current image, the process will not open the rest of the images for drawing.

##### Using a Template

Users have the option to utilize one of the files within the file queue as a template for the other selected files. The file to be used as a template can be selected from the drop down menu. The boundary drawn on the template file will be applied to all selected files from the file queue.

#### Changing Flashcard Options

What flashcards get created is determined by the options the user selects. There are sets of options for each of the three types of flashcards: Kanji, Word, and Sentence.

##### Kanji Flashcard Options

- Recall + Recognition -> Create a recognition and a recall flashcard for each kanji.
- Recognition -> Create only a recognition flashcard for each kanji.
- None -> Do not create kanji flashcards

##### Word Flashcard Options

- Recall + Recognition : Create a recognition and a recall flashcard for each word.
- Recognition : Create only a recognition flashcard for each word.
- None : Do not create word flashcards

- Allow duplicate words in separate sentences : When checked, the program will only look for duplicate words in each sentence and not in the overall text.

  	Ex: "There was a dog. The dog was big like my dog."

  	Cards created when option is disabled:

  		There, was, a, dog, The, big, like, my

  	Cards created when option is enabled:

  		There, was, a, dog, The, dog, was, big, like, my

  This option is potentially useful when wanting to see words in different contexts, however, it does create many more flashcards.

##### Sentence Flashcard Options

- [  ] Random words : Creates cloze deletion flashcards for some amount of random words within the sentence. The amount of words by default is 3, but can be changed by the user.
- Each word : Creates a cloze deletion flashcard for each word in the sentence.
- None : Do not create cloze deletion flashcards.

#### Starting the Application

Under the word *Status*, there will be a button labeled *Start*. Once the user presses it, all inputs will be disabled and the only remaining button will be *Stop*. The program will now begin processing the user's files with the selected options.

#### Viewing the Application's Progress

The user can see the applications progress via the boxes under the *Progress* label. The program will keep the user updated about what file the application is currently working on, how many files are remaining, and the number of sentence, word, and kanji flashcards created.

#### Stopping the Application

The user may stop the application by pressing the *Stop* button after they have pressed *Start*. This will stop the application and remove any temporary files the application will have created. The user will end up an incomplete flashcard file and have the current file that the application was working on removed from the queue. Any files still in the queue will remain with their settings in tact.

### Command Line Usage

Although GUI usage is recommended, the application may still be launched through the command line. The application can be run with the following format:

```
python ocr_flashcard.py pathToFile--languageType--boundaryBox kanjiOptions, wordOptions, clozeAmount, enhance
```

Note: The following file commands must be connected using "--" and can be repeated as many times as the user wishes for all the files they wish to process.

#### File Arguments

**pathToFile** : This is the path to the file the user wishes to extract text from.

**languageType** : This is the language type of the file. If the file's text is horizontal (Left -> Right), the user will enter "jpn" for the language option. If the file's text is vertical (Top -> Bottom), the user will enter "jpn_vert" for their language.

**boundaryBox** : This is the crop boundary the user wishes to apply to their file. If the user does not wish to apply a boundary, they will write "None". If the user wishes to apply a boundary, they will write four comma separated numbers. These numbers will represent the amount in pixels they wish to crop in the respective directions. 

​	Ex: Left, Top, Right, Bottom -> 50, 500, 50, 20

​	This will crop 50 pixels off of the left, 500 pixels off of the top, 50 pixels off of the right, and 20 pixels off 	of the bottom.

#### Other Options

**kanjiOptions** : There are three options for kanjiOptions - 0, 1, or 2. 

0 - No flashcards created.

1 - Recognition flashcards created.

2 - Recall + Recognition flashcards created.

**wordOptions** : The wordOptions argument should be 2 characters long. The first of the two characters follows the same rules as the kanjiOptions argument.

0 - No flashcards created.

1 - Recognition flashcards created.

2 - Recall + Recognition flashcards created.

The second part of the argument will be a 1 or 0 and determines whether or not duplicate words will be kept track of     on a sentence-by-sentence basis or throughout the file.

0 - Keep track of duplicate words throughout the files. (No duplicate word cards)

1 - Keep track of duplicate words on a sentence-by-sentence basis. (Duplicate word cards will be made if the words appear within different sentences)

**clozeAmount** : This determines how many cloze flashcards will be created per sentence. This argument starts with a 2, 1 or 0.

0 - No cloze flashcards will be created.

1 - A cloze flashcard will be created for each word.

2 - A cloze flashcard will be created for __ random words. The amount of random flashcards is determined by the number entered after the number 2. Ex: 24 will pick 4 random words in the sentence to make cloze flashcards out of.

**enhance** : This option determines whether or not the user's images will be doubled in size before the image is processed for text. This option will be a 0 or a 1.

0 - The image will not be enhanced.

1 - The image will be enhanced.

## Importing Flashcards into Anki

The flashcards created by the program will be output into a file named flashcards.txt one directory above the python script. To import these files into Anki:

Open Anki and click "Import..." in the top left.

Locate the "flashcards.txt" file and select it.

Change the "Fields separated by:" field to a tab. You can do this by entering \t into the box.

Check the "Allow HTML in fields" checkbox.

Your field mapping should now show the following for the fields:

    Field 1 of file is:	mapped to Front

    Field 2 of file is:	mapped to Back

    Field 3 of file is:	mapped to Tags

After confirming that everything is correct, just click Import!

## Credits

Resources were used from the following projects to make this possible:

[Fred's Imagemagick Scripts](http://www.fmwconcepts.com/imagemagick/textcleaner/index.php)

[KanjiVG](https://github.com/KanjiVG/kanjivg)

[KANJIDIC Project](https://www.edrdg.org/wiki/index.php/KANJIDIC_Project)

## License

This project is licensed under the MIT license.

