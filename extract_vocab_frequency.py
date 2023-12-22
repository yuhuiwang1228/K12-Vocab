import argparse
import glob
import logging
import json
import re
import os
import subprocess
from collections import defaultdict
import pandas as pd
import numpy as np
from itertools import Counter

from docx import Document

import nltk
nltk.data.path.append('/home/ivanfung/nltk_data')
nltk.download('punkt') #download_dir="/home/ivanfung/nltk_data/nltk_data"
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

def extract_title(args, data_file):
    logger.info("***** extracting title *****")
    grade_pat = re.compile(r'([一二三四五六七八九])+年级')
    term_pat = re.compile(r'([上下全])册?')

    grade_dict = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9}
    term_dict = {'上':'A','下':'B','全':'C'}

    grade_res = grade_pat.search(data_file)
    grade = grade_dict[grade_res.group(1)]

    term_res = term_pat.search(data_file)
    term = term_dict[term_res.group(1)]

    return grade, term, unit

def extract_pdf(args, cache_file):
    logger.info("***** extracting pdf *****")
    logger.info("Convert pdf to images")
    images = pdf2image.convert_from_path(args.data_file)

    logger.info("Convert images to txt")
    text = ''
    for image in images:
        text += pytesseract.image_to_string(image, lang='eng')

    with open(cache_file, 'w', encoding='utf-8') as file:
        file.write(text)

def extract_unit_details(filename):
    logger.info("***** extracting unit details *****")
    match = re.search(r'Unit( *\d+)(.+?)\.docx', filename)
    if match:
        unit_id = int(match.group(1).strip())
        unit_title = match.group(2).strip()
        return unit_id, unit_title
    else:
        return float('inf'), ""

def extract_unit_list(unit_file):
    logger.info("***** extracting unit list for all textbooks *****")
    df = pd.read_excel(unit_file)
    chapter_list = list(df.iloc[:,0].dropna().values)
    unit_list_all = df.iloc[:,1].dropna().values
    unit_list_all = [unit for unit in unit_list_all if unit.startswith('Unit')]
    unit_list_dict = defaultdict(list)
    index = 0
    n = len(unit_list_all)
    for chapter in chapter_list:
        for i in range(index, n):
            unit_list_dict[chapter].append(unit_list_all[i])
            if i<n-1 and unit_list_all[i+1].startswith('Unit 1 '):
                index = i+1
                break
    return unit_list_dict


def get_unit_list(args, cache_file, unit_list):

    with open(cache_file, 'r', encoding='utf-8') as file:
        text = file.read()

    true_unit_list = []
    p = 0

    skip_content = False if args.data_type == '教师用书' else True
    for i,unit in enumerate(unit_list):
        seq_len = len(unit)
        for j in range(p, len(text)-seq_len):
            candidate = text[j:j+seq_len]
            if (candidate.startswith('Unit') or candidate.startswith('第')) and fuzz.ratio(candidate,unit) > 80:
                if not skip_content:
                    skip_content = True
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
    stemmed_words = [stemmer.stem(word) for word in lemmatized_words]
    vocab = Counter(lemmatized_words)
    return vocab

def get_vocab_standard(args, cache_file, output_file, grade, term, unit_list):
    logger.info("***** getting vocabulary *****")
    with open(cache_file, 'r', encoding='utf-8') as file:
        text = file.read()

    unit_vocab_list = []
    remaining_text = text
    for i,unit in enumerate(unit_list):
        parts = re.split(re.escape(unit), remaining_text, maxsplit=1)
        logger.info(f"***** processing text {unit} *****")
        assert len(parts)==2
        if len(parts) > 1:
            unit_vocab_list.append(process_text(parts[0]))
            remaining_text = parts[1]
            if i==len(unit_list)-1:
                unit_vocab_list.append(process_text(remaining_text))

    term_vocab = process_text(text)
    term_vocab.sort()

    unit_vocab_dict = {}
    print(len(unit_list), len(unit_vocab_list))
    assert len(unit_list)==len(unit_vocab_list)-1
    for i,vocab in enumerate(unit_vocab_list):
        if i==0:
            continue
        unit_vocab_dict[f"grade_{grade}_{term}_U{i}"] = {"unit_name": unit_list[i-1],"word":vocab}

    json_set = {f"grade_{grade}_{term}":{"unit_base": unit_vocab_dict, 'term_base':term_vocab}}
    
    with open(output_file, "w") as file:
        json.dump(json_set, file)
    logger.info("saved json formatted vocabulary")
    

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--data_file",
        default=None,
        type=str,
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

    parser.add_argument(
        "--chapter",
        choices=['人教版七上', '人教版七下', '人教版八上', '人教版八下', '人教版九全'],
        default=None,
        type=str,
        required=True,
        help="The chapter of the data",
    )

    parser.add_argument(
        "--unit_file",
        default=None,
        type=str,
        required=True,
        help="The structure of the data",
    )

    parser.add_argument("--do_cache", action="store_true", help="Whether to use the cached data")
    args = parser.parse_args()

    logging.basicConfig(
        filename=f'{args.cache_dir}/{args.chapter}_logfile.log',  # Log file to write to
        filemode='w',  # Append to the log file if it exists, create if it does not
        format="%(asctime)s - %(levelname)s - %(name)s -   %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
        level=logging.INFO  # Set to log INFO and higher level messages
    )

    grade, term, _ = extract_title(args, data_file)
    cache_file = os.path.join(args.cache_dir, f"{args.data_type}_grade_{grade}_{term}.txt")
    output_file = os.path.join(args.output_dir, f"{args.data_type}_grade_{grade}_{term}.json")

    unit_list_dict = extract_unit_list(args.unit_file)
    standard_unit_list = unit_list_dict[args.chapter]
    
    if args.do_cache:
        extract_pdf(args, cache_file)

    print(standard_unit_list)
    unit_list = get_unit_list(args, cache_file, standard_unit_list)
    print(unit_list)
    get_vocab_standard(args, cache_file, output_file, grade, term, unit_list)


if __name__ == "__main__":
    main()

