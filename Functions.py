import re
import math
import numpy as np
from numpy.fft import rfft, irfft
from pydub import AudioSegment, effects
from pydub.generators import WhiteNoise
from pydub.silence import split_on_silence
import parselmouth
import logging
from utils import resource_path
from db import get_syllable_audio_path, populate_syllable_db
from Constants.abbreviations import abbrevs
from Constants.acronyms import acr
from Constants.symbols import symbols_to_remove, symbols_to_expand

# აბრევიატურების გაშლა
def expand_abbreviations(text):
    """Expands abbreviations in the text using the abbrevs dictionary."""
    for abbrev, expansion in abbrevs.items():
        pattern = re.escape(abbrev)  # Escape to handle dots and special chars
        text = re.sub(pattern, expansion, text)
    return text

# აკრონიმების გაშლა
def expand_acronyms(text):
    """Expands acronyms in the text using the acr dictionary."""
    for word in text.split():
        if word in acr:
            text = re.sub(rf'\b{re.escape(word)}\b', acr[word], text)
    return text

# სიმბოლოების გაშლა
def expand_symbols(text):
    for symbol, replacement in symbols_to_expand.items():
        text = text.replace(symbol, f' {replacement} ')
    return text


def remove_symbols_and_tags(text):
    text = re.sub(r'(?<!\d)-\s*([a-zA-Z0-9]+)', r'\1', text)
    text = re.sub(r'(?<!\d)-', '', text)
    
    text = re.sub(r'\s*([.,!?;:])\s*', r'\1 ', text)
    text = re.sub(r'\s+', ' ', text)

    text = re.sub(r'[{}]'.format("".join(symbols_to_remove)), '', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()

def expand_numbers(text):
    def replace_ordinal_suffix(match):
        number = int(match.group(1))
        word = convert_numbers_to_words(number)
        if word:
            return word[:-1] + "ე"
        else:
            return str(number) + "-ე"

    def replace_decimal(match):
        decimal = match.group(1)
        suffix = match.group(2) or ""

        if decimal.startswith("."):
            int_part = 0
            frac_part = decimal[1:]
        else:
            int_part, frac_part = decimal.split(".")

        int_word = convert_numbers_to_words(int(int_part))
        frac_word = convert_numbers_to_words(int(frac_part))
        return f"{int_word} მთელი {frac_word}{suffix}"

    def replace_plain_number(match):
        word = convert_numbers_to_words(int(match.group()))
        return word if word else str(match.group())

    text = re.sub(r'(?<=\d),(?=\d{3}\b)', '', text)
    text = re.sub(r'\b(\d+)-ე\b', lambda m: str(replace_ordinal_suffix(m)), text)
    text = re.sub(r'\b(\d*\.\d+)([%\w\-]*)', lambda m: str(replace_decimal(m)), text)
    text = re.sub(r'\b\d+\b', lambda m: str(replace_plain_number(m)), text)

    return text

# რიცხვების სიტყვებად გარდაქმნა
def convert_numbers_to_words(number):
    units = [
        "ნულ", "ერთ", "ორ", "სამ", "ოთხ", "ხუთ", "ექვს", "შვიდ", "რვა", "ცხრა",
        "ათ", "თერთმეტ", "თორმეტ", "ცამეტ", "თოთხმეტ", "თხუთმეტ", "თექვსმეტ",
        "ჩვიდმეტ", "თვრამეტ", "ცხრამეტ", "ოც"
    ]
    tens = ["ოც", "ორმოც", "სამოც", "ოთხმოც"]
    if number < 21:
        if units[number].endswith("ა"):
            return units[number] + ""
        else:
            return units[number] + "ი"
    elif number < 100:
        a = number // 20
        b = number - a * 20
        if b != 0:
            prefix = tens[a-1] + "და" + units[b]
            if units[b].endswith("ა"):
                return  prefix  
            else:
                return prefix + "ი"
        else:
            return tens[a-1] + "ი"
    elif number < 1_000:
        a = number // 100
        if a == 1:
            prefix = "ას"
        else:
            prefix = units[a] + "ას"
            
        if number % 100 == 0:
            return prefix + "ი"
        else:
            rest = convert_numbers_to_words(number - a * 100)
            return prefix + " " + rest if rest else prefix

    elif number < 1_000_000:
        a = number // 1_000
        if a == 1:
            prefix = "ათას"
        else:
            prefix = convert_numbers_to_words(a) + " ათას"
        if number % 1_000 == 0:
            return prefix + "ი"
        else:
            rest = convert_numbers_to_words(number - a * 1000)
            return prefix + " " + rest if rest else prefix
        
    elif number < 1_000_000_000:
        a = number // 1_000_000
        prefix = convert_numbers_to_words(a) + " მილიონ"
        if number % 1_000_000 == 0:
            return prefix + "ი"
        else:
            rest = convert_numbers_to_words(number - a * 1_000_000)
            return prefix + " " + rest if rest else prefix
        
    elif number < 1_000_000_000_000:
        a = number // 1_000_000_000
        prefix = convert_numbers_to_words(a) + " მილიარდ"
        if number % 1_000_000_000 == 0:
            return prefix + "ი"
        else:
            rest = convert_numbers_to_words(number - a * 1_000_000_000)
            return prefix + " " + rest if rest else prefix
    else:
        return str(number)

# გრაფემი ფონემში
def grapheme_to_phoneme(text):
    return list(text)

# დამარცვლა
def syllabify_georgian(word):
    vowels = set("აეიოუ")

    harmonic_clusters = [
        "ფხ", "თხ", "ცხ", "ჩხ", "ბღ", "დღ", "ზღ", "ჯღ",
        "პყ", "ტყ", "წყ", "ჭყ"
    ]
    
    vowel_idxs = [i for i, ch in enumerate(word) if ch in vowels]
    if not vowel_idxs:
        result = [word]
        with open("syllabify_debug.log", "a", encoding="utf-8") as log:
            log.write(f"[DEBUG] Word '{word}' was broken into syllables: {result}\n")
        return result
    
    syllables = []
    start = 0

    for vi, vj in zip(vowel_idxs, vowel_idxs[1:]):
        inter = word[vi+1:vj]
        boundary = vi + 1

        if len(inter) == 0:
            boundary = vi + 1
        elif len(inter) == 1:
            boundary = vi + 1
        else:
            if inter[:2] in harmonic_clusters:
                boundary = vi + 3
            else:
                boundary = vi + 2

        syllables.append(word[start:boundary])
        start = boundary

    syllables.append(word[start:])
    syllables = [syl.strip() for syl in syllables if syl.strip()]
    syllables = [syl.replace(" ", "") for syl in syllables if syl.strip()]
    return syllables

def unique_syllables(syllables):
    return set(syllables)

def normalize_text(text):

    text = expand_symbols(text)
    text = expand_abbreviations(text)
    text = expand_acronyms(text)

    text = re.sub(r'([a-zA-Z]+)-([a-zA-Z]+)', r'\1\2', text)
    text = expand_numbers(text)
    text = remove_symbols_and_tags(text)



    return text.strip()



def preprocess_and_syllabify(text):
    text = normalize_text(text)
    words = text.split()
    all_syllables = []
    
    for word in words:
        # Check if word ends with end-of-sentence punctuation
        has_eos = bool(re.search(r'[.!?]$', word))
        
        # Remove punctuation from word before syllabification
        word_clean = re.sub(r'[.,!?;:"„"–]', '', word)
        
        if not word_clean:
            continue
            
        # Syllabify the cleaned word
        sylls = syllabify_georgian(word_clean)
        all_syllables.extend(sylls)
        
        # Add appropriate separator token
        if has_eos:
            all_syllables.append("<eos>")
        else:
            all_syllables.append("<s>")
    
    return all_syllables

# def preprocess_and_syllabify(text):
#     text = normalize_text(text)
#     words = text.split()
#     all_syllables = []
#     for word in words:
#         # Remove punctuation from word before syllabification
#         word_clean = re.sub(r'[.,!?;:"„“–]', '', word)
#         # lets separate these if end of sentece symobls are present add 
#         if not word_clean:
#             continue
#         sylls = syllabify_georgian(word_clean)
#         all_syllables.extend(sylls)
#         all_syllables.append("<s>")
#     return all_syllables


# def synthesize_speech(syllables, db_path=None):
#     if db_path is None:
#         db_path = resource_path("tts_syllables.db")
#     from pydub import AudioSegment, effects
#     from pydub.silence import split_on_silence

#     def prepare_segment(path):
#         seg = AudioSegment.from_wav(path)
#         # normalize volume
#         seg = effects.normalize(seg)
#         # trim leading/trailing silence
#         chunks = split_on_silence(seg, min_silence_len=20, silence_thresh=-50, keep_silence=0)
#         seg = chunks[0] if chunks else seg
#         # apply tiny fades
#         return seg.fade_in(10).fade_out(10)

#     output = AudioSegment.silent(duration=50)
#     for syl in syllables:
#         if syl == "<s>":
#             output = output.append(AudioSegment.silent(duration=100), crossfade=0)
#             continue

#         audio_path = get_syllable_audio_path(syl, db_path)
#         if audio_path:
#             try:
#                 seg = prepare_segment(audio_path)
#                 # append with a short crossfade
#                 output = output.append(seg, crossfade=20)
#             except Exception as e:
#                 print(f"Error loading audio for syllable '{syl}': {e}")
#                 output = output.append(AudioSegment.silent(duration=200), crossfade=0)
#         else:
#             print(f"Missing syllable: {syl}")
#             output = output.append(AudioSegment.silent(duration=200), crossfade=0)

#     return output


# def synthesize_speech(syllables, db_path=None):
#     if db_path is None:
#         db_path = resource_path("tts_syllables.db")
#     from pydub import AudioSegment
#     output = AudioSegment.silent(duration=50)
#     for syl in syllables:
#         if syl == "<s>":
#             output += AudioSegment.silent(duration=100)
#             continue
#         audio_path = get_syllable_audio_path(syl, db_path)
#         if audio_path:
#             try:
#                 seg = AudioSegment.from_wav(audio_path)

#                 output += seg
#             except Exception as e:
#                 print(f"Error loading audio for syllable '{syl}': {e}")
#                 output += AudioSegment.silent(duration=200)
#         else:
#             print(f"Missing syllable: {syl}")
#             output += AudioSegment.silent(duration=200)
#     output = output.speedup(playback_speed=1.05, crossfade=50)
#     return output
def synthesize_speech(syllables, db_path=None):
    if db_path is None:
        db_path = resource_path("tts_syllables.db")

    def simple_crossfade(a, b, duration_ms=15):
        # Use pydub's built-in crossfade - much simpler and safer
        return a.append(b, crossfade=duration_ms)

    def prepare_segment(path):
        seg = AudioSegment.from_wav(path)
        # Normalize and remove DC/rumble
        seg = effects.normalize(seg).high_pass_filter(20)
        # Trim silence edges more aggressively
        chunks = split_on_silence(seg, min_silence_len=15, silence_thresh=-45, keep_silence=0)
        seg = chunks[0] if chunks else seg
        # Minimal fades
        return seg.fade_in(5).fade_out(5)

    # Start with empty audio instead of silence
    output = AudioSegment.empty()
    
    for i, syl in enumerate(syllables):
        if syl == "<s>":
            # Add shorter pauses for spaces (50ms instead of 100ms)
            if len(output) > 0:  # Only add space if we have content
                output = output + AudioSegment.silent(duration=100)
            continue
        if syl == "<eos>":
            # Add end-of-sentence pause
            if len(output) > 0:
                output = output + AudioSegment.silent(duration=400)
            continue

        path = get_syllable_audio_path(syl, db_path)
        if not path:
            print(f"Missing syllable: {syl}")
            # Add shorter silence for missing syllables (100ms instead of 200ms)
            if len(output) > 0:
                output = output + AudioSegment.silent(duration=100)
            continue

        try:
            seg = prepare_segment(path)
            
            if len(output) == 0:
                # First segment - no crossfade needed
                output = seg
            else:
                # Use simple crossfade
                output = simple_crossfade(output, seg, duration_ms=15)
                
        except Exception as e:
            print(f"Error processing syllable '{syl}': {e}")
            # Add shorter silence for errors
            if len(output) > 0:
                output = output + AudioSegment.silent(duration=100)

    # Only add room tone if we have audio content
    if len(output) > 0:
        # Use quieter room tone
        noise = WhiteNoise().to_audio_segment(duration=len(output)).apply_gain(-35)
        output = output.overlay(noise)
    
    return output



if __name__ == "__main__":
    text = "ე.ი. შ.შ.მ., პირების"
    text = normalize_text(text)
    print(text)