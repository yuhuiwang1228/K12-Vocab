# sudo apt-get install -y poppler-utils
# sudo apt-get install tesseract-ocr

# pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# python extract_vocab_frequency.py \
#     --data_file "./人教版电子课本/高中/人教版高中英语必修2.pdf" \
#     --cache_dir "./cache" \
#     --output_dir "./output" \
#     --unit_file "./content.xlsx" \
#     --do_cache

# python extract_vocab_frequency.py \
#     --data_file "./人教版电子课本/初中/人教版九年级英语全册.PDF" \
#     --cache_dir "./cache" \
#     --output_dir "./output"

python extract_vocab_frequency.py \
    --data_file "./人教版电子课本/小学/人教新起点英语1A电子课本.pdf" \
    --cache_dir "./cache" \
    --output_dir "./output" 

# data_file="${ebook_folder}/人教版Go for it英语七年级上册高清电子课本（清晰PDF）.pdf"
# cache_dir="${ebook_folder}/电子课本/cache"
# output_dir="${ebook_folder}/电子课本/output"

# python extract_vocab_v2.py \
#     --data_type '电子课本' \
#     --file_type 'pdf' \
#     --data_file $data_file \
#     --cache_dir $cache_dir \
#     --output_dir $output_dir \
#     --chapter '人教版七上' \
#     --unit_file './Snow.xlsx' \
#     --do_cache
