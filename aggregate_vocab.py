import os
import json
import re

def extract_title(data_file):
    pat = re.compile(r"textbook_grade(\w)_term([ABCD]).json")
    res = pat.search(data_file)
    grade = res.group(1)
    term = res.group(2)

    return grade,term

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def extract_unique_words(folder_path):
    all_words = set()
    unique_words_per_file = {}

    for file_name in sorted(os.listdir(folder_path)):
        if file_name.endswith('.json'):
            grade,term = extract_title(file_name)
            file_path = os.path.join(folder_path, file_name)
            data = read_json_file(file_path)

            # Extract words from 'term_base'
            current_words = set(word for word, _ in data.get(f'grade_{grade}_term{term}', {}).get('term_base', []))

            # Find words that are unique to this file
            unique_words = current_words - all_words
            unique_words_per_file[grade+term] = sorted(list(unique_words))

            # Update the set of all words
            all_words.update(current_words)

    return unique_words_per_file

def create_word_to_term_map(unique_words):
    word_to_term = {}
    for term, words in unique_words.items():
        for word in words:
            if word not in word_to_term:
                word_to_term[word] = term
    return word_to_term


folder_path = './output'
unique_words = extract_unique_words(folder_path)

word_to_term_map = create_word_to_term_map(unique_words)

with open('./unique_words.json', 'w') as file:
    json.dump(unique_words, file, indent=4)

with open('./word_to_term_map.json', 'w') as file:
    json.dump(word_to_term_map, file, indent=4)
