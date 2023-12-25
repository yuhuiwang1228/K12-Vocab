import argparse
import glob
import logging
import json
import re
import os
import subprocess
from collections import defaultdict,Counter
import pandas as pd
import numpy as np
import PyPDF2

from docx import Document

import nltk
nltk.data.path.append('/home/ivanfung/nltk_data')
nltk.download('punkt') # download_dir="/home/ivanfung/data"
nltk.download('words')
nltk.download('stopwords')
nltk.download('wordnet')
from nltk.corpus import words, stopwords
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize

import pytesseract
from PIL import Image
import pdf2image

from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)

standard_english_vocab = set(words.words())
stop_english_vocab = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()

def extract_title(data_file):
    logger.info("***** extracting title *****")
    primary_pat = re.compile(r"(\d)([A-C])")
    junior_pat = re.compile(r'([一二三四五六七八九])+年级英语([上下全])册?')
    senior_pat = re.compile(r'(必修|选修)(\d)?')

    grade_dict = {'一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9', '必修':'R','选修':'E'}
    term_dict = {'上':'A','下':'B','全':'C', '1':'A','2':'B','3':'C','4':'D'}

    res = primary_pat.search(data_file)
    if res==None:
        res = junior_pat.search(data_file)
        if res==None:
            res = senior_pat.search(data_file)
        grade = grade_dict[res.group(1)]
        term = term_dict[res.group(2)]
    else:
        grade = res.group(1)
        term = res.group(2)

    return grade,term

# def extract_pdf(args, cache_file):
#     logger.info("***** extracting pdf *****")
#     with open(args.data_file, 'rb') as file:
#         pdf_reader = PyPDF2.PdfReader(file)

#     with open(cache_file, 'w') as text_file:
#         for page_num in range(len(pdf_reader.pages)):
#             page = pdf_reader.pages(page_num)
#             text = page.extractText()
#             text_file.write(text)

def extract_pdf(args, cache_file):
    logger.info("***** extracting pdf *****")
    logger.info("Convert pdf to images")
    images = pdf2image.convert_from_path(args.data_file)

    logger.info("Convert images to txt")
    text = ''
    for image in images:
        text += pytesseract.image_to_string(image, lang='eng+chi_sim') #lang='eng+chi_sim'

    with open(cache_file, 'w', encoding='utf-8') as file:
        file.write(text)

def extract_unit_list(unit_file):
    logger.info("***** extracting unit list for all textbooks *****")
    df = pd.read_excel(unit_file)
    term_list = list(df.iloc[:,0].dropna().values)
    unit_list_all = df.iloc[:,1].dropna().values
    unit_list_all = [unit for unit in unit_list_all if unit.startswith('Unit')]
    unit_list_dict = defaultdict(list)
    index = 0
    n = len(unit_list_all)
    for term in term_list:
        for i in range(index, n):
            unit_list_dict[term].append(unit_list_all[i])
            if i<n-1 and unit_list_all[i+1].startswith('Unit 1 '):
                index = i+1
                break
    return unit_list_dict


def get_unit_list(args, cache_file, unit_list):

    with open(cache_file, 'r', encoding='utf-8') as file:
        text = file.read()

    true_unit_list = []
    p = 0

    # skip_content = False if args.data_type == '教师用书' else True
    ignore_content = args.ignore_content
    for i,unit in enumerate(unit_list):
        seq_len = len(unit)
        unit = unit.lower()
        for j in range(p, len(text)-seq_len):
            candidate = text[j:j+seq_len]
            candidate = candidate.replace('\n',' ').lower()
            if candidate.startswith('unit') and fuzz.ratio(candidate,unit) > 80:
                if not ignore_content and i==0:
                    ignore_content = True
                    continue
                true_unit_list.append(text[j:j+seq_len])
                p = j
                break

    return true_unit_list

def process_text(text):
    english_words = word_tokenize(text)
    english_words = [word.lower() for word in english_words if word.isalpha()]
    standard_english_words = [word for word in english_words if word in standard_english_vocab and len(word)>1]
    lemmatized_words = [lemmatizer.lemmatize(word) for word in standard_english_words]
    # stemmed_words = [stemmer.stem(word) for word in lemmatized_words]
    vocab = Counter(lemmatized_words)
    vocab = list(vocab.items())
    vocab.sort()
    return vocab

def get_vocab_standard(args, cache_file, output_file, grade, term, unit_list):
    logger.info("***** getting vocabulary *****")
    with open(cache_file, 'r', encoding='utf-8') as file:
        text = file.read()

    unit_vocab_list = []
    remaining_text = text
    ignore_content = args.ignore_content
    for i,unit in enumerate(unit_list):
        if not ignore_content and i==0:
            ignore_content = True
            parts = re.split(re.escape(unit), remaining_text, maxsplit=2)
            assert len(parts)==3
        else:
            parts = re.split(re.escape(unit), remaining_text, maxsplit=1)
            assert len(parts)==2
        
        logger.info(f"***** processing text {unit} *****")
        
        if len(parts) > 1:
            unit_vocab_list.append(process_text(parts[-2]))
            remaining_text = parts[-1]
            if i==len(unit_list)-1:
                unit_vocab_list.append(process_text(remaining_text))

    term_vocab = process_text(text)

    unit_vocab_dict = {}
    print(len(unit_list), len(unit_vocab_list))
    assert len(unit_list)==len(unit_vocab_list)-1
    for i,vocab in enumerate(unit_vocab_list):
        if i==0:
            continue
        unit_vocab_dict[f"grade{grade}_term{term}_U{i}"] = {"unit_name": unit_list[i-1],"word":vocab}

    json_set = {f"grade{grade}_term{term}":{"unit_base": unit_vocab_dict, 'term_base':term_vocab}}
    
    with open(output_file, "w") as file:
        json.dump(json_set, file)
    logger.info("saved json formatted vocabulary")

def get_vocab(args, cache_file, output_file, grade, term):
    logger.info("***** getting vocabulary *****")
    with open(cache_file, 'r', encoding='utf-8') as file:
        text = file.read()

    term_vocab = process_text(text)

    json_set = {f"grade_{grade}_term{term}":{"unit_base": [], 'term_base':term_vocab}}
    with open(output_file, "w") as outfile:
        json.dump(json_set, outfile)
    logger.info("saved json formatted vocabulary")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data_file",
        default=None,
        type=str,
        required=True,
        help="The data file for vocabulary extraction",
    )

    parser.add_argument(
        "--cache_dir",
        default=None,
        type=str,
        required=True,
        help="The output directory where the txt files will be written",
    )

    parser.add_argument(
        "--output_dir",
        default=None,
        type=str,
        required=True,
        help="The output directory where the json files will be written",
    )

    parser.add_argument("--unit_file", default=None, type=str, help="The structure of the data")
    parser.add_argument("--do_cache", action="store_true", help="Whether to use the cached data")
    parser.add_argument("--do_unit", action="store_true", help="Whether to extract unit based vocabulary")
    parser.add_argument("--ignore_content", action="store_true", help="Whether to ignore the content when splitting the text")
    args = parser.parse_args()

    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)
    if not os.path.exists(args.cache_dir):
        os.makedirs(args.cache_dir)

    grade, term = extract_title(args.data_file)
    cache_file = os.path.join(args.cache_dir, f"textbook_grade{grade}_term{term}.txt")
    output_file = os.path.join(args.output_dir, f"textbook_grade{grade}_term{term}.json")

    logging.basicConfig(
        filename=f'{args.cache_dir}/{grade}{term}_logfile.log',  # Log file to write to
        filemode='w',  # Append to the log file if it exists, create if it does not
        format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO  # Set to log INFO and higher level messages
    )

    
    if args.do_cache:
        extract_pdf(args, cache_file)

    if args.do_unit:
        unit_list_dict = extract_unit_list(args.unit_file)
        standard_unit_list = unit_list_dict[grade+term]
        print(standard_unit_list)

        unit_list = get_unit_list(args, cache_file, standard_unit_list)
        print(unit_list)

        get_vocab_standard(args, cache_file, output_file, grade, term, unit_list)
    else:
        get_vocab(args, cache_file, output_file, grade, term)


if __name__ == "__main__":
    main()

