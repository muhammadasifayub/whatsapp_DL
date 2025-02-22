from flask import Flask, request, jsonify
import os
import re
import emoji
import numpy as np
from datetime import datetime
from collections import defaultdict
from textblob import TextBlob

app = Flask(__name__)

def parse_datetime(date_str):
    """Parses datetime from WhatsApp chat format."""
    if not date_str:
        return None  

    date_str = date_str.replace("\u202f", " ")
    date_str = re.sub(r"\s+", " ", date_str.strip())

    formats = [
        "%d/%m/%Y %I:%M %p", "%m/%d/%Y %I:%M %p", "%d/%m/%y %I:%M %p", "%m/%d/%y %I:%M %p",
        "%d-%m-%Y %I:%M %p", "%m-%d-%Y %I:%M %p", "%d-%m-%y %I:%M %p", "%m-%d-%y %I:%M %p",
        "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M", "%d/%m/%y %H:%M", "%m/%d/%y %H:%M"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None  

def is_system_message(line):
    """Detects system-generated messages."""
    system_patterns = [
        r".*Messages to this group are now secured.*", r".*created group.*",
        r".*left the group.*", r".*added.*to the group.*", r".*removed.*from the group.*"
    ]
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in system_patterns)

def parse_whatsapp_chat(filename):
    """Parses WhatsApp chat file and extracts structured data."""
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    chat_pattern = re.compile(r"^(\d{1,2}[-/\.\s]\d{1,2}[-/\.\s]\d{2,4}),?\s?(\d{1,2}:\d{2}(\s?[APMapm]{2})?)?\s?[-–]\s(.*?):\s(.*)")

    messages, timestamps, users, emojis_count = [], [], set(), defaultdict(int)
    user_message_count, link_count = defaultdict(int), 0

    for line in lines:
        line = line.strip()
        if is_system_message(line): 
            continue

        match = chat_pattern.match(line)
        if match:
            date, time, _, user, message = match.groups()
            time = time if time else "00:00"  
            timestamp = parse_datetime(f"{date} {time}")

            if timestamp:
                timestamps.append(timestamp)
                users.add(user)
                user_message_count[user] += 1
                messages.append({"timestamp": timestamp, "user": user, "message": message})

                for char in message:
                    if char in emoji.EMOJI_DATA:
                        emojis_count[user] += 1

                if "http" in message or "www." in message:
                    link_count += 1

    return {
        "messages": messages,
        "user_message_count": user_message_count,
        "users": list(users),
        "timestamps": timestamps,
        "chat_start": min(timestamps) if timestamps else None,
        "chat_end": max(timestamps) if timestamps else None,
        "emoji_count": dict(emojis_count),
        "link_count": link_count,
    }

@app.route('/upload', methods=['POST'])
def upload_chat():
    """Endpoint to upload a WhatsApp chat file and analyze it."""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400

    file = request.files['file']
    file_path = os.path.join("uploads", file.filename)
    os.makedirs("uploads", exist_ok=True)
    file.save(file_path)

    try:
        chat_data = parse_whatsapp_chat(file_path)
        return jsonify(chat_data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(debug=True)