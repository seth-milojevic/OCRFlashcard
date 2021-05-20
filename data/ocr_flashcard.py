# OCRFlashcard - Python script that utilizes tesseract to grab
# kanji from images, PDFs, etc. then defines them and creates
# flashcards formatted for the SRS program Anki.

# Imports

import sys
import os
import pdf2image
import random
from subprocess import call
import numpy as np
from PIL import Image
from cv2 import cv2
import pytesseract
import re
from lxml import etree
import radical_dict
from sudachipy import tokenizer
from sudachipy import dictionary
from code_dict import codeDict

tokenizer_obj = dictionary.Dictionary().create()
mode = tokenizer.Tokenizer.SplitMode.C

# Functions
def ocr_kanji(source, lang, fileBounds, enhance):
    # Run tesseract's OCR on the user's file
    # Enlarge the image if the user desires
    if enhance == "True":
        im = Image.open(source)
        lenX, widY = im.size
        factor = min(1, float(1024.0 / lenX))
        size = int(factor * lenX), int(factor * widY)
        im_resized = im.resize(size, Image.ANTIALIAS)
        fileName = "{}.png".format(os.getpid())
        print("tmp,a,{}".format(basePath + fileName))
        sys.stdout.flush()
        im_resized.save(fileName, dpi=(300, 300))
    # If not, create duplicate of image for processing
    else:
        im = Image.open(source)
        factor = 1
        fileName = "{}.png".format(os.getpid())
        print("tmp,a,{}".format(basePath + fileName))
        sys.stdout.flush()
        im.save(fileName, dpi=(300, 300))
    # If file has cropping boundaries, crop the image and clean it
    if fileBounds != "":
        fileBounds = fileBounds.split(",")
        fileBounds = ",".join(str(int(int(bound) * factor)) for bound in fileBounds)
        clean_image(fileBounds, basePath + fileName)
    # Extract the text from the image with tesseract
    text = pytesseract.image_to_string(Image.open(fileName), config="-l {}".format(lang))
    os.remove(fileName)
    print("tmp,d,{}".format(basePath + fileName))
    sys.stdout.flush()
    return text

# Remove special characters / punctuation from sentence
def remove_special(sentence):
    for char in special:
        if char in sentence:
            if char == '|':
                sentence = sentence.replace(char, '-')
            else:
                sentence = sentence.replace(char, '')
    return sentence

# Retrieve all of the sentences from the text retrieved from tesseract
def get_sentences(passage):
    if len(passage.split('.')) > 1:
        return (sentence.replace(' ', '') for sentence in passage.split('.'))
    else:
        return (sentence.replace(' ', '') for sentence in passage.split('。'))

# Retrieve all of the words in their base and surface from by tokenizing the sentence
def get_words(sentence):
    return [(m.dictionary_form(), m.surface()) for m in tokenizer_obj.tokenize(sentence, mode)]

# Retreive all kanji from word
def get_kanji(word):
    return (kanji for kanji in re.findall(kanjiRX, word))

# Create kanji flashcards given the specified kanji,
# its entry in the dictionary, the radical parts that
# make it up, the xpath for the kanji, and the flashcard
# specifications received from the user
def create_kanji_cards(kanji, entry, parts, kanjiPath, kanjiOptions):
    # Retrieve meanings from entries
    meanings = [meaning.text for meaning in entry.xpath(meaningXPATH)]
    kanjiMeaning = ", ".join(meanings)
    # Retrieve onyomi readings from entries
    onreadings = [onreading.text for onreading in entry.xpath(onreadingXPATH)]
    on = " / ".join(onreadings)
    # Retrieve kunyomi readings from entries
    kunreadings = [kunreading.text for kunreading in entry.xpath(kunreadingXPATH)]
    kun = " / ".join(kunreadings)
    # Attempt to get the JLPT data of the kanji
    try:
        jlpt = entry.xpath(kanjiPath + jlptXPATH)[0].text
    except:
        jlpt = "N/A"
    # Retrieve the radical info of the kanji
    radInfo = radical_dict.dictionary[entry.xpath(radicalXPATH)[0].text].split(',')
    kanjiFile = open(basePath + "./kanji/{}.svg".format(hex(ord(kanji)).replace('x','')))
    svgText = kanjiFile.read()
    kanjiFile.close()
    # Retrieve the stroke information about the kanji
    strokesText = ''
    strokes = [stroke.replace('<!--', '').replace('-->', '') for stroke in re.findall(commentRX, svgText)]
    for i in range(len(strokes)):
        svgText = svgText.replace("<!--{}-->".format(strokes[i]), strokes[i])
        strokesText += svgText
    # Retrieve the parts list of the kanji
    partList = ['<span style="margin: 2\% 12\% 2\% 12\%">{}</span>'.format(part) for part in parts]
    partText = "".join(partList)
    # Finalize the flashcard
    front = '<div style="width: 34%; float: left; height: 200px; margin: 0px; padding: 0px;"><p style="font-size: 150px; vertical-align: top; margin: 0px; padding: 0px;">{}</p></div><div style="width: 33%; float: right; height: 200px;"><p style="font-weight: bold;">Parts</p><div style="display: flex; flex-wrap: wrap; text-align: center;">{}</div></div><div style="width: 33%; float: right; height: 200px; margin: 0px; padding: 0px;"><p style="font-weight: bold;">Radical</p><p>{}</p><p style="font-weight: bold;">JLPT</p><p>{}</p></div><div>{}</div>'.format(kanji, partText, radInfo[0], jlpt, strokesText)
    back = "Kanji Meaning: {}<br/> Onyomi Reading: {}<br/> Kunyomi Reading: {}<br/><br/> Radical Meaning ({}): {}".format(kanjiMeaning, on, kun, radInfo[0], radInfo[1])
    # Return more flashcards based off of the user specified option
    if kanjiOptions == "2":
        return front + '	' + back + '	Kanji Recall\n' + back + '	' + front + '	Kanji Recognition'
    else:
        return front + '	' + back + '	Kanji Recall'

# Create word flaschards based on the sentence, word, dictionary
# entries for the word and the options given by the user.
def create_word_flashcard(sentence, word, entries, wordOptions):
    # Highlight the target word in the sentence
    highlightBase = "<font color=\"#ffaaff\">{}</font>".format(word[0])
    highlightRaw = "<font color=\"#ffaaff\">{}</font>".format(word[1])
    sentence = sentence.replace(word[1], highlightRaw)
    card = "<div>{}</div><div>{}</div>	<div>{}</div>".format(highlightBase, sentence, highlightBase)
    # Place all entries onto the flashcard
    for entry in entries:
        reading = entry[0]
        definitions = entry[1]
        pos = entry[2]
        for i in range(len(definitions)):
            card += "<div><b>{}</b></div><div style=\"text-align: left;\">".format(reading.replace('(P)', '').replace(";", " | "))
            card += "<div><font color=\"#bdbdbd\">{}</font></div><div>{}. {}</div>".format(verbosify(pos[i]), i+1, definitions[i])
            card += "</div>"
    # Create Recall card if user has specified to do so
    if wordOptions == "2":
        recallBack = "	<div>{}</div>".format(highlightBase)
        recallFront = ""
        for entry in entries:
            definitions = entry[1]
            pos = entry[2]
            for i in range(len(definitions)):
                recallFront += "<div style=\"text-align: left;\">"
                recallFront += "<div><font color=\"#bdbdbd\">{}</font></div><div>{}. {}</div>".format(verbosify(pos[i]), i+1, definitions[i])
                recallFront += "</div>"
        return card + "	Word Recognition\n" + recallFront + recallBack + "	Word Recall"
    else:
        return card + "	Word Recognition"

# Create a sentence flashcard from the current sentence and word
def create_sentence_flashcard(sentence, word):
    # Remove word from sentence
    blankSentence = sentence.replace(word[1], ("<font color=\"#ffaaff\">___</font>"))
    return "<br/><div>{}</div><br/>	<br/><div>{}</div><br/><div>{}</div><div><font color=\"#90ee90\">{}</font></div><br/><div>{}</div><div><font color=\"#ffaaff\">{}</font></div>	Sentence".format(blankSentence, sentence.replace(word[1], "<font color=\"#ffaaff\">{}</font>".format(word[1])), "Dictionary Form:", word[0], "In-Sentence Form (Answer):", word[1])

# Remove excess information from the definition
# and return a cleaner definition
def format_definition(text):
    defList = []
    codeList = []
    reading = re.findall(readingRX, text)
    if reading:
        reading = reading[0]
    else:
        reading = ""
    multiDef = re.findall(posDefRX, text)
    # Determine if Kanji has multiple meanings
    if (len(multiDef) > 0):
        for posDef in re.findall(posDefRX, text):
            tmp, codes = clean_codes(text.split(posDef)[0])
            defList.append(posDef[4:-1])
            try:
                # Append code if one was returned
                codeList.append([codes[-1]])
            except IndexError:
                # Otherwise, append an empty string
                codeList.append('')
    else:
        # Starting text for definition
        definition = re.findall(r'/.*/', text)[0]
        definition, codes = clean_codes(definition)
        # Append the cleaned definition to the list
        defList.append(definition[1:-1])
        codeList.append(codes)
    return reading, defList, codeList

# Verbosify the given codes from the dictionary entry
# Ex: (n/n-suf) -> [ Noun, Noun-Suffix ]
# Ex: (m-sl) -> [ Manga Slang ]
def verbosify(codes):
    verboseCodes = []
    # For each code that applies to the definition
    for code in codes:
        # Split the code on all ,'s so each can be addressed i.e. (n,n-suf)
        subCodes = code.split(',')
        # For each subCode created by the split
        for subCode in subCodes:
            # Split the codes on a space so they can be handled separately i.e. (n) (m-sl)
            multiCodes = subCode.split(' ')
            # For each multiCode created by the split
            for multiCode in multiCodes:
                # Append the verbosified codes into an output array
                verboseCodes.append(codeDict.get(multiCode.replace('(', '').replace(')', '')))
    return verboseCodes

# Remove codes from definition and return their verbosified form
def clean_codes(definition):
    newDef = definition
    codeList = []
    # Remove any codes present in the definition
    for match in re.findall(r'\(.*?\)', definition):
        potentialCode = match
        # Determine if multiple codes may be present together (n,adj)
        # If so, separate the first of the codes
        if ',' in match:
            potentialCode = match.split(',')[0] + ")"
        # Determine if the match is actually a code
        # If so, remove it from the definition
        if potentialCode[1:-1] in codeDict:
            # Check for multiple code    
            # [\u4e00-\u9faf]s matching one definition i.e. (n) (n-suf)
            if (len(codeList)):
                multiStr = r'(?<=(\({}\) ))\({}\)'.format(codeList[-1][1:-1], match[1:-1])
                multiPos = re.findall(multiStr, definition)
                # If it matches, edit the previous code to include both codes
                if (len(multiPos)):
                    codeList[-1] = codeList[-1] + " " + match
                # If not, append code normally
                else:
                    codeList.append(match)
            else:
                codeList.append(match)
            # Replace codes in definition with whitespace
            newDef = newDef.replace(match + " ", "")
            entryDetail = re.findall(r'EntL.*/', definition)
            # Determine if any more codes are at the end of the definition
            # If so, remove them as well.
            if len(re.findall(r'(\(.\)/)', definition)):
                entryDetail.append(re.findall(r'(\(.\)/)', definition)[0])
            for detail in entryDetail:
                newDef = newDef.replace(detail, "")
    return newDef, codeList

# Clean image for better text processing with Fred's Imagemagick script
# http://www.fmwconcepts.com/imagemagick/textcleaner/index.php
def clean_image(boundary, image):
    call(basePath + "../scripts/textcleaner -l l -c {} -g -e normalize -s 5 {} {}".format(boundary, image, image), shell=True)

# Variable declarations

imageTypes = {"jpg", "png", "ttf"}
validLanguage = {"jpn", "jpn_vert"}
special = ['.', ',', '、', '+', '*', '?', '^', '$', '(', ')', '[', ']', '{', '}', '「', '」', '|', chr(92)]
kanjiSet = set()
wordSet = set()
basePath = os.path.abspath(os.path.dirname(__file__)) + "/"

# Regex Compilations

fileNameRX = re.compile(r'.+?(?=\.).')
kanjiRX = re.compile(r'[\u4e00-\u9faf]')
readingRX = re.compile(r'\[.*\]')
posDefRX = re.compile(r'\([0-9]\).*?/')
pathRX = re.compile(r'(<path.*?)>')
commentRX = re.compile(r'<!--.*?-->')

# XPath Strings

meaningXPATH = "./reading_meaning/rmgroup/meaning[not(@*)]"
onreadingXPATH = "./reading_meaning/rmgroup/reading[@r_type=\"ja_on\"]"
kunreadingXPATH = "./reading_meaning/rmgroup/reading[@r_type=\"ja_kun\"]"
jlptXPATH = "./misc/jlpt"
radicalXPATH = "./radical/rad_value[@rad_type=\"classical\"]"

# Implementation

def main(files, kanjiOptions, wordOptions, clozeAmount, enhance):
    # Declare initial source text value
    sourceText = ""

    # Determine cloze flashcard options
    if clozeAmount[0] == "2":
        clozeAmount = int(clozeAmount[1:])
    elif clozeAmount[0] == "1":
        clozeAmount = -1
    else:
        clozeAmount = 0

    # Update variables

    kanjiCreated = 0
    wordsCreated = 0
    sentencesCreated = 0
    remainingFiles = 0

    # Process each file
    for i in range(len(files)):
        # If the language is invalid, continue to next file
        try:
            languageType = files[i].split("--")[1]
        except IndexError:
            continue
        # Return progress information for files left and name of file
        print("file,{}".format(len(files) - (i + 1)))
        sys.stdout.flush()
        print("name,{}".format(files[i]))
        sys.stdout.flush()

        # Determine language is in acceptable types
        if languageType in validLanguage:
            targetFile = files[i].split("--")[0]

            # Deteermine if crop boundaries were set
            if files[i].split("--")[2] != "None":
                fileBounds = "".join(files[i].split("--")[2].split(" "))
            else:
                fileBounds = ""

            # Obtain the file name and its extension
            extension = str(targetFile)

            # Extract file name and leave only extension
            fileName = re.match(fileNameRX, extension)
            extension = extension.replace(fileName.group(0), '').split('.')[-1]

            if extension in imageTypes:
                # Handle Images
                sourceText += ocr_kanji(targetFile, languageType, fileBounds, enhance)

            elif extension == "pdf":
                # Handle PDFs
                # Turn pdf into images and process accordingly
                targetFile = pdf2image.convert_from_path(targetFile, dpi=200)
                for file in targetFile:
                    tmp = "{}.jpg".format(os.getpid())
                    print("tmp,a,{}".format(basePath + tmp))
                    sys.stdout.flush()
                    file.save(tmp)
                    sourceText += ocr_kanji(tmp, languageType, fileBounds, enhance)
                    os.remove(tmp)
                    print("tmp,d,{}".format(basePath + tmp))
                    sys.stdout.flush()

            elif extension == "txt":
                # Handle TXT file
                with open(targetFile, 'r') as file:
                    sourceText += file.read()

            elif extension == "py":
                # main.py handling
                continue

            else:
                # Default case
                print("Unsupported input type: {}".format(extension))

            sourceText = sourceText.replace('\n', '')
            # Open word dictionary
            wordDict = open(basePath + "./edict2", "r", encoding="utf8")
            wordDictText = wordDict.read()
            # Open kanji dictionary
            kanjiTree = etree.parse(basePath + "./kanjidic2.xml")
            # Open radical dictionary
            partsDict = open(basePath + "./kradfile-u", "r", encoding="utf8")
            partsDictText = partsDict.read()

            # Open output file for flashcard output
            flashOutput = open(basePath + "../flashcards.txt", "a+")

            # Process each sentence
            sentence_gen = get_sentences(sourceText)
            for sentence in sentence_gen:
                # Remove special characters from sentence and pass to get_words
                word_gen = get_words(remove_special(sentence))
                # Enforce cloze options
                if clozeAmount == -1:
                    clozeNum = list(range(len(word_gen)))
                elif clozeAmount == 0:
                    clozeNum = []
                else:
                    try:
                        clozeNum = random.sample(range(len(word_gen)-1), clozeAmount)
                    except ValueError:
                        clozeNum = list(range(len(word_gen)))
                # Counter for cloze words
                curNum = 0
                # If duplicate words in separate sentences is enabled, clear the word set
                if wordOptions[1] == "1":
                    wordSet.clear()
                # Process each word
                for word in word_gen:
                    # If curNum is within clozeNum, create a cloze flashcard
                    if curNum in clozeNum:
                        flashOutput.write("{}\n".format(create_sentence_flashcard(sentence, word)))
                        sentencesCreated += 1
                        # Update via stdout
                        print("sentence,{}".format(sentencesCreated))
                        sys.stdout.flush()
                    curNum += 1
                    # Setup entries variable
                    wordEntries = []
                    # Process word if it has not already been processed
                    if word[0] not in wordSet:
                        wordSet.add(word[0])
                        # Create word flashcards if user has requested
                        if wordOptions[0] != "0":
                            # Get all word hits from dictionary
                            hitREGEX = re.compile(r"^.*{}.*".format(word[0]), re.MULTILINE)
                            wordHits = re.findall(hitREGEX, wordDictText)
                            wordPattern = re.compile(r"^{}\b.*|(?<=;|\[){}(?=\(|;|\]).*".format(word[0], word[0]))
                            # Process retrieved hits
                            for hit in wordHits:
                                result = re.findall(wordPattern, hit)
                                if result:
                                    wordEntries.append(format_definition(hit))
                            # Process hits confirmed as entries for the word
                            if len(wordEntries):
                                flashOutput.write("{}\n".format(create_word_flashcard(sentence, word, wordEntries, wordOptions[0])))
                                wordsCreated += 1
                                # Update via stdout
                                print("word,{}".format(wordsCreated))
                                sys.stdout.flush()
                        # Handle all kanji within word
                        kanji_gen = get_kanji(word[0])
                        # Create kanji flashcards if user has requested
                        if kanjiOptions != "0":
                            for kanji in kanji_gen:
                                # If kanji has not been processed already, create flashcard
                                if kanji not in kanjiSet:
                                    kanjiSet.add(kanji)
                                    # Locate kanji and its entries
                                    kanjiPath = "//text()[contains(.,'{}')]/../..".format(kanji)
                                    entry = kanjiTree.xpath(kanjiPath)[0]
                                    entry.getparent().remove(entry)
                                    # Format regex to find kanji's parts
                                    partsRX = "{} : .*".format(kanji)
                                    # Attempt to get parts of kanji
                                    try:
                                        parts = re.findall(partsRX, partsDictText)[0][4:].replace(' ', '')
                                    except:
                                        print("Error obtaining parts for following kanji: " + kanji)
                                    # Write kanji flashcards to file
                                    flashOutput.write("{}\n".format(create_kanji_cards(kanji, entry, parts, kanjiPath, kanjiOptions)))
                                    kanjiCreated += 1
                                    # Update via stdout
                                    print("kanji,{}".format(kanjiCreated))
                                    sys.stdout.flush()
            # Close output file
            flashOutput.close()
        else:
            # Invalid language output
            print("Please enter a valid language type as the last argument. (jpn or jpn_vert)")

    # Completion output
    print("Done!")

# Allow program to be run as process
if __name__ == "__main__":
    main(sys.argv[:-4], sys.argv[-4], sys.argv[-3], sys.argv[-2], sys.argv[-1])
