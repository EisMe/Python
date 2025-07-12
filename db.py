import sqlite3, os
from utils import resource_path

def populate_syllable_db(db_path=None, audio_dir=None):
    if db_path is None:
        db_path = resource_path("tts_syllables.db")
    if audio_dir is None:
        audio_dir = resource_path("AudioDB")
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS syllables (
                    id INTEGER PRIMARY KEY,
                    syllable TEXT UNIQUE,
                    file_path TEXT)''')

    for file in os.listdir(audio_dir):
        if file.endswith(".wav"):
            syl = file.replace(".wav", "")
            cur.execute("INSERT OR IGNORE INTO syllables (syllable, file_path) VALUES (?, ?)",
                        (syl, os.path.join(audio_dir, file)))
    conn.commit()
    conn.close()

def get_syllable_audio_path(syllable, db_path=None):
    if db_path is None:
        db_path = resource_path("tts_syllables.db")
    # Build the full path to the syllable audio file using resource_path
    audio_file = resource_path(os.path.join("AudioDB", f"{syllable}.wav"))
    if os.path.exists(audio_file):
        return audio_file
    return None
