import streamlit as st
from collections import Counter
import json
from pathlib import Path

def load_words(file_path):
    with open(file_path, 'r') as f:
        word_freq = json.load(f)
        return [word.lower() for word in word_freq.keys() if word.isalpha()], word_freq

def filter_words(word_list, pattern, wrong_letters):
    filtered = []
    for word in word_list:
        if len(word) != len(pattern):
            continue
        match = True
        for i, ch in enumerate(pattern):
            if ch != '_' and word[i] != ch:
                match = False
                break
            if ch == '_' and word[i] in wrong_letters:
                match = False
                break
        if match and all(l not in word for l in wrong_letters):
            filtered.append(word)
    return filtered

def rank_words(word_list, word_freq):
    return sorted(word_list, key=lambda x: word_freq.get(x, 0), reverse=True)

def rank_letters(word_list, guessed_letters, word_freq):
    letter_scores = Counter()
    for word in word_list:
        # Use the word's commonality score as weight
        score = word_freq.get(word, 0)  # Default to 0 if word not found
        for ch in set(word):
            if ch not in guessed_letters:
                # Accumulate scores weighted by word commonality
                letter_scores[ch] += score
    return letter_scores.most_common()

# UI
st.title("Hangman Helper")

# Get directories
current_dir = Path(__file__).parent
data_dir = current_dir.parent / 'data'

# Load dictionary with commonality data
words, word_freq = load_words(data_dir / 'words_with_frequency.json')

# User inputs
word_length = st.number_input("Enter word length:", min_value=1, step=1, value=5, max_value=31)

if word_length:
    # Known letters
    st.markdown("### Known Letters")
    known = []
    if word_length > 16:
        # Split into two lines if word length is too long
        cols1 = st.columns(16)
        cols2 = st.columns(word_length - 16)
        for i in range(word_length):
            if i < 16:
                ch = cols1[i].text_input(f"**{i+1}**", max_chars=1)
            else:
                ch = cols2[i-16].text_input(f"**{i+1}**", max_chars=1)
            known.append(ch.lower() if ch else '_')
    else:
        cols = st.columns(word_length)
        for i in range(word_length):
            label = f"{i+1}" if word_length > 17 else (f"L {i+1}" if word_length > 13 else (f"Let {i+1}" if word_length > 9 else f"Letter {i+1}"))
            ch = cols[i].text_input(f"**{label}**", max_chars=1)
            known.append(ch.lower() if ch else '_')

    # Display the list in a colored box
    st.markdown(
        f'<div style="background-color: #265811; padding: 10px; border-radius: 5px; margin: 10px 0; text-align: center; font-size: 20px;">'
        f'{"&nbsp;&nbsp;".join([l.upper() for l in known])}'
        f'</div>',
        unsafe_allow_html=True
    )

    # Wrong letters
    st.markdown("### Wrong Letters")

    # Initialize session state
    if "wrong_letters" not in st.session_state:
        st.session_state.wrong_letters = [""]

    # Ensure theres always one empty box at the end
    def sync_boxes():
        # Remove empty entries except the last one
        non_empty = [l for l in st.session_state.wrong_letters if l.strip()]
        st.session_state.wrong_letters = non_empty + [""]

    sync_boxes()
    num_boxes = len(st.session_state.wrong_letters)
    cols = st.columns(num_boxes)

    # Track whether any value changed
    for i in range(num_boxes):
        old_val = st.session_state.wrong_letters[i]
        label = f"Let {i+1}" if num_boxes > 9 else f"Letter {i+1}"
        new_val = cols[i].text_input(label,
                                    value=old_val,
                                    max_chars=1,
                                    key=f"wrong_letter_{i}")
        if new_val != old_val:
            st.session_state.wrong_letters[i] = new_val.lower()
            # Trigger rerun immediately to show new box or remove cleared one
            st.rerun()

    # Clean again in case the last box is now filled
    sync_boxes()

    # Final wrong_letters list (for use elsewhere)
    wrong_letters = [l for l in st.session_state.wrong_letters if l.strip()]

    # Display the list in a colored box
    st.markdown(
        f'<div style="background-color: #783317; padding: 10px; border-radius: 5px; margin: 10px 0;">'
        f'<strong>Wrong Letters:</strong> {", ".join([l.upper() for l in wrong_letters])}'
        f'</div>',
        unsafe_allow_html=True
    )

    pattern = "".join(known)
    possible_words = filter_words(words, pattern, wrong_letters)
    ranked_words = rank_words(possible_words, word_freq)
    ranked_letters = rank_letters(possible_words, known + wrong_letters, word_freq)

    # Create two columns for side-by-side display
    col1, col2 = st.columns(2)

    with col1:
        # Possible words
        st.markdown(f"### {len(ranked_words)} possible words:")
        
        if 'words_to_show' not in st.session_state:
            st.session_state.words_to_show = 5
        
        # Show current batch of words with commonality scores
        for i, word in enumerate(ranked_words[:st.session_state.words_to_show]):
            if i < 3:  # Top 3 words get different shades of green
                opacity = 1 - (i * 0.4)  # Decrease opacity by 0.4 for each
                st.markdown(
                    f'<div style="background-color: rgba(38, 88, 17, {opacity}); padding: 6px; border-radius: 3px; margin: 2px 0; display: flex; justify-content: space-between; padding-left: 10px; padding-right: 10px;">'
                    f'<span>{word}</span> <span>{word_freq.get(word, 0):.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div style="padding: 6px; border-radius: 3px; margin: 2px 0; display: flex; justify-content: space-between; padding-left: 10px; padding-right: 10px;">'
                    f'<span>{word}</span> <span>{word_freq.get(word, 0):.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        if st.session_state.words_to_show < len(ranked_words):
            if st.button("Show More Words"):
                st.session_state.words_to_show += 10
                st.rerun()

    with col2:
        # Suggested next letters
        st.markdown("### Suggested letters:")
        
        if 'letters_to_show' not in st.session_state:
            st.session_state.letters_to_show = 5
        
        # Show current batch of letters with weighted scores
        for i, (letter, score) in enumerate(ranked_letters[:st.session_state.letters_to_show]):
            if i < 3:  # Top 3 letters get different shades of green
                opacity = 1 - (i * 0.4)  # Decrease opacity by 0.4 for each
                st.markdown(
                    f'<div style="background-color: rgba(38, 88, 17, {opacity}); padding: 6px; border-radius: 3px; margin: 2px 0; display: flex; justify-content: space-between; padding-left: 10px; padding-right: 10px;">'
                    f'<span>{letter.upper()}</span> <span>{score:.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    f'<div style="padding: 6px; border-radius: 3px; margin: 2px 0; display: flex; justify-content: space-between; padding-left: 10px; padding-right: 10px;">'
                    f'<span>{letter.upper()}</span> <span>{score:.0f}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        
        if st.session_state.letters_to_show < len(ranked_letters):
            if st.button("Show More Letters"):
                st.session_state.letters_to_show += 10
                st.rerun()
