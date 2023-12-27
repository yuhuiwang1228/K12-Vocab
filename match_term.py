import json
import re
from collections import Counter

import nltk
# nltk.data.path.append('/home/ivanfung/nltk_data')
# nltk.download('words')
from nltk.corpus import words, stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

standard_english_vocab = set(words.words())
lemmatizer = WordNetLemmatizer()

def load_json(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)

def process_text(text):
    english_words = word_tokenize(text)
    english_words = [word.lower() for word in english_words if word.isalpha()]
    # for word in english_words:
    #     if word not in standard_english_vocab:
    #         raise ValueError(f"Non-English word detected: {word}")
    lemmatized_words = [lemmatizer.lemmatize(word) for word in english_words]
    return lemmatized_words

def text_to_terms(text, word_to_term_map):
    processed_words = process_text(text)
    return processed_words, [word_to_term_map.get(word, '-1') for word in processed_words]


json_file = './word_to_term_map.json'
word_to_term_map = load_json(json_file)

input_text = input("Enter your text: ")
output_words, output_terms = text_to_terms(input_text, word_to_term_map)

print("Processed words: ", output_words)
print("Corresponding terms", output_terms)

