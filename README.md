# K12_vocab_frequency

## Setup
```
sudo apt-get install -y poppler-utils
sudo apt-get install tesseract-ocr
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```
- [ ] [NLTK及nltk_data安装教程](https://www.jianshu.com/p/3cee73895eff)

## Support
For any inquiries or assistance, feel free to reach out via email: yuhui3661@gmail.com

## Extract Vocabulary
This tool is designed to extract and compile a frequency table of English words from each unit in a K-12 textbook.

### Execution
Execute the script using the provided shell command. Ensure to replace the file name in the script's arguments prior to running. 
```
sh run.sh
```
The processed text files and logs are saved in './cache' and the JSON formatted output files which contain the word frequency tables are saved in './output'.

### Issues
The quality of textbook scans, specifically the proportion of images and the sharpness of the text, can significantly impact the accuracy of unit positioning and word extraction.

## Match Term
This function allows you to input a paragraph of text and receive a list of terms, indicating the first appearance of each word in the textbooks. Ensure that the word_to_term_map.json file is downloaded and placed in the appropriate directory. Follow the on-screen instructions to input your text and receive the output.
```
python match_term.py
```
