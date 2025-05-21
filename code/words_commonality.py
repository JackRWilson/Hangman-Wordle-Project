from wordfreq import word_frequency
import json
from pathlib import Path

# Get directories
current_dir = Path(__file__).parent
data_dir = current_dir.parent / 'data'

# Load original JSON
with open(data_dir / 'words_dictionary.json') as f:
    word_dict = json.load(f)

# Create a new dictionary with frequency scores
updated_dict = {
    word: word_frequency(word, 'en') * 100000000
    for word in word_dict
}

# Save the updated dictionary
output_path = data_dir / 'words_with_frequency.json'
with open(output_path, 'w') as f:
    json.dump(updated_dict, f, indent=2)
