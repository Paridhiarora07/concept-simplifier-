from flask import Flask, render_template, request
import re
import sqlite3

DATABASE = "concept_simplifier.db"

app = Flask(__name__)


def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS text_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT NOT NULL,
            simplified_text TEXT NOT NULL,
            readability_score REAL
        )
    """)

    conn.commit()
    conn.close()


def readability_score(text):
    sentences = re.split(r'[.!?]+', text)
    sentences = [s for s in sentences if s.strip()]

    words = re.findall(r'\b\w+\b', text)

    if not sentences or not words:
        return 0

    average_words_per_sentence = len(words) / len(sentences)
    average_word_length = sum(len(word) for word in words) / len(words)

    score = 100 - (
        average_words_per_sentence * 2
        + average_word_length * 5
    )

    return max(0, min(100, score))


def simplified_text(text):
    replacement = {
        "utilize": "use",
        "utilizes": "uses",
        "numerous": "many",
        "approximately": "about",
        "facilitate": "help",
        "facilitates": "helps",
        "demonstrate": "show",
        "demonstrates": "show",
        "obtain": "get",
        "require": "need",
        "requires": "need",
        "commence": "start",
        "terminate": "end",
        "assistant": "help",
        "additional": "extra",
        "individual": "people",
        "therefore": "so",
        "however": "but",
        "due to the fact that": "because",
        "a large number of": "many"
    }

    simplified = text

    for old, new in replacement.items():
        simplified = re.sub(
            r'\b' + re.escape(old) + r'\b',
            new,
            simplified,
            flags=re.IGNORECASE
        )

    return simplified


@app.route("/", methods=["GET", "POST"])
def home():

    text = ""
    result = ""
    score = ""
    word_count = 0
    sentence_count = 0
    character_count = 0

    if request.method == "POST":

        text = request.form.get("text", "")

        if text.strip():

            score = readability_score(text)
            result = simplified_text(text)

            words = re.findall(r'\b\w+\b', text)

            sentences = re.split(r'[.!?]+', text)
            sentences = [s for s in sentences if s.strip()]

            word_count = len(words)
            sentence_count = len(sentences)
            character_count = len(text)

            conn = sqlite3.connect(DATABASE)

            conn.execute(
                """
                INSERT INTO text_history
                (original_text, simplified_text, readability_score)
                VALUES (?, ?, ?)
                """,
                (text, result, score)
            )

            conn.commit()
            conn.close()

    return render_template(
        "index.html",
        text=text,
        result=result,
        score=score,
        word_count=word_count,
        sentence_count=sentence_count,
        character_count=character_count
    )


@app.route("/history")
def history():

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, original_text, simplified_text, readability_score
        FROM text_history
        ORDER BY id DESC
    """)

    records = cursor.fetchall()

    conn.close()

    return render_template(
        "history.html",
        records=records
    )


init_db()


if __name__ == "__main__":
    app.run(debug=True)
