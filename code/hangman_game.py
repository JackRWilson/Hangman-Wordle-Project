import streamlit as st
import random
import json
from pathlib import Path

# --- Helper Functions ---
def load_words_with_freq(file_path):
    with open(file_path, 'r') as f:
        word_freq = json.load(f)
    return word_freq

def weighted_random_word(word_freq, min_length=4, max_length=12):
    # Add a small constant so even zero-frequency words have a tiny chance
    epsilon = 1e-6
    words = [w for w in word_freq if min_length <= len(w) <= max_length and w.isalpha()]
    weights = [word_freq[w] + epsilon for w in words]
    total = sum(weights)
    weights = [w/total for w in weights]
    return random.choices(words, weights=weights, k=1)[0]

def display_word(word, guessed_letters):
    return " ".join([ch.upper() if ch in guessed_letters else '_' for ch in word])

def draw_hangman(wrong_guesses):
    # 0-6 wrong guesses
    hangman_stages = [
        """
         +---+
         |   |
             |
             |
             |
             |
        =========
        """,
        """
         +---+
         |   |
         O   |
             |
             |
             |
        =========
        """,
        """
         +---+
         |   |
         O   |
         |   |
             |
             |
        =========
        """,
        """
         +---+
         |   |
         O   |
        /|   |
             |
             |
        =========
        """,
        """
         +---+
         |   |
         O   |
        /|\  |
             |
             |
        =========
        """,
        """
         +---+
         |   |
         O   |
        /|\  |
        /    |
             |
        =========
        """,
        """
         +---+
         |   |
         O   |
        /|\  |
        / \  |
             |
        =========
        """
    ]
    idx = min(wrong_guesses, len(hangman_stages)-1)
    st.text(hangman_stages[idx])

# --- Streamlit App ---
st.set_page_config(page_title="Hangman Game", layout="centered")
st.title("🎲 Hangman Game (with Frequency-Weighted Words)")

# Paths
data_dir = Path(__file__).parent.parent / 'data'
words_file = data_dir / 'words_with_frequency.json'

# Load word frequencies (cache for performance)
@st.cache_data
def get_word_freq():
    return load_words_with_freq(words_file)

word_freq = get_word_freq()

# --- Session State Initialization ---
if 'game_active' not in st.session_state:
    st.session_state.game_active = False
if 'chosen_word' not in st.session_state:
    st.session_state.chosen_word = ''
if 'guessed_letters' not in st.session_state:
    st.session_state.guessed_letters = set()
if 'wrong_letters' not in st.session_state:
    st.session_state.wrong_letters = set()
if 'max_wrong' not in st.session_state:
    st.session_state.max_wrong = 6
if 'game_result' not in st.session_state:
    st.session_state.game_result = ''

# --- Start New Game ---
def start_new_game():
    word = weighted_random_word(word_freq)
    st.session_state.chosen_word = word
    st.session_state.guessed_letters = set()
    st.session_state.wrong_letters = set()
    st.session_state.game_active = True
    st.session_state.game_result = ''

if st.button("Start New Game") or not st.session_state.game_active:
    start_new_game()

chosen_word = st.session_state.chosen_word
max_wrong = st.session_state.max_wrong

guessed_letters = st.session_state.guessed_letters
wrong_letters = st.session_state.wrong_letters

# --- Game UI ---
st.subheader("Word to Guess:")
st.markdown(f"<div style='font-size:2em; letter-spacing:0.2em;'>{display_word(chosen_word, guessed_letters)}</div>", unsafe_allow_html=True)

draw_hangman(len(wrong_letters))

st.markdown(f"**Wrong guesses:** {' '.join(sorted([l.upper() for l in wrong_letters])) if wrong_letters else 'None'}")

# --- Guess Input ---
if st.session_state.game_result == '':
    guess = st.text_input("Guess a letter:", max_chars=1, key='guess_input').lower()
    if st.button("Submit Guess"):
        if not guess.isalpha() or len(guess) != 1:
            st.warning("Please enter a single letter.")
        elif guess in guessed_letters or guess in wrong_letters:
            st.info("You already guessed that letter.")
        else:
            if guess in chosen_word:
                guessed_letters.add(guess)
                # Check for win
                if all(ch in guessed_letters for ch in set(chosen_word)):
                    st.session_state.game_result = 'win'
                    st.session_state.game_active = False
            else:
                wrong_letters.add(guess)
                # Check for loss
                if len(wrong_letters) >= max_wrong:
                    st.session_state.game_result = 'lose'
                    st.session_state.game_active = False
            st.rerun()

# --- Game Result ---
if st.session_state.game_result == 'win':
    st.success(f"🎉 Congratulations! You guessed the word: {chosen_word.upper()}")
elif st.session_state.game_result == 'lose':
    st.error(f"💀 Game Over! The word was: {chosen_word.upper()}")

st.caption("Words are chosen with probability proportional to their frequency, but all words have a chance!") 