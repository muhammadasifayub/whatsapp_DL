import re
import json
import csv
import emoji
import numpy as np
import pandas as pd
from datetime import datetime
from collections import defaultdict
from textblob import TextBlob
from flask import Flask, request, jsonify
import os



app = Flask(__name__)


def parse_datetime(date_str):
    if not date_str:
        return None

    date_str = date_str.replace("\u202f", " ")
    date_str = re.sub(r"\s+", " ", date_str.strip())
    
    formats = [
        "%d/%m/%Y %I:%M %p", "%m/%d/%Y %I:%M %p", "%d/%m/%y %I:%M %p", "%m/%d/%y %I:%M %p",
        "%Y/%m/%d %I:%M %p", "%y/%m/%d %I:%M %p", "%d/%m/%Y %H:%M", "%m/%d/%Y %H:%M",
        "%d/%m/%y %H:%M", "%m/%d/%y %H:%M", "%Y/%m/%d %H:%M", "%y/%m/%d %H:%M",
        "%d-%m-%Y %I:%M %p", "%m-%d-%Y %I:%M %p", "%d-%m-%y %I:%M %p", "%m-%d-%y %I:%M %p",
        "%d-%m-%Y %H:%M", "%m-%d-%Y %H:%M", "%d-%m-%y %H:%M", "%m-%d-%y %H:%M"
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Time data '{date_str}' does not match known formats.")

def is_system_message(line):
    system_patterns = [
        r".*Messages to this group are now secured with end-to-end encryption.*",
        r".*created group.*",
        r".*changed this group's.*",
        r".*left the group.*",
        r".*added.*to the group.*",
        r".*removed.*from the group.*",
        r".*changed the subject to.*",
        r".*changed the group description.*",
        r".*deleted this message.*",
        r".*started a call.*",
        r".*ended the call.*"
    ]

    return any(re.search(pattern, line, re.IGNORECASE) for pattern in system_patterns)

def parse_whatsapp_chat(filename):
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    chat_pattern = re.compile(
        r"^(\d{1,2}[-/\.\s]\d{1,2}[-/\.\s]\d{2,4}),?\s?(\d{1,2}:\d{2}(\s?[APMapm]{2})?)?\s?[-–]\s(.*?):\s(.*)"
    )

    messages = []
    user_message_count = defaultdict(int)
    timestamps = []
    users = set()
    emojis_count = defaultdict(int)
    link_count = 0

    for line in lines:
        line = line.strip()

        if is_system_message(line):  
            continue

        match = chat_pattern.match(line)
        if match:
            date, time, _, user, message = match.groups()

            if not date:
                print(f"Skipping line due to missing date: {line}")
                continue
            time = time if time else "00:00"  
            
            try:
                timestamp = parse_datetime(f"{date} {time}")
                timestamps.append(timestamp)
                users.add(user)
                user_message_count[user] += 1
                messages.append({"timestamp": timestamp, "user": user, "message": message})

                for char in message:
                    if char in emoji.EMOJI_DATA:
                        emojis_count[user] += 1

                if "http" in message or "www." in message:
                    link_count += 1
            except ValueError as e:
                print(f"Skipping line due to format error: {line} - {e}")

    if not messages:
        raise ValueError("Error: No valid messages found in the chat file.")

    return {
        "messages": messages,
        "user_message_count": user_message_count,
        "users": users,
        "timestamps": timestamps,
        "chat_start": min(timestamps) if timestamps else None,
        "chat_end": max(timestamps) if timestamps else None,
        "emoji_count": emojis_count,
        "link_count": link_count,
    }
def daily_chat_frequency(timestamps):
    daily_freq = defaultdict(int)
    for ts in timestamps:
        daily_freq[ts.date()] += 1  # Use `.date()` from `datetime` object
    return daily_freq

def average_messages_per_day(daily_freq):
    if not daily_freq:
        return 0
    return np.mean(list(daily_freq.values()))

def response_time_analysis(messages):
    response_times = []
    prev_time = None

    for msg in messages:
        timestamp = msg["timestamp"]  
        if prev_time:
            response_times.append((timestamp - prev_time).total_seconds() / 60)
        prev_time = timestamp

    return np.mean(response_times) if response_times else 0

def sentiment_analysis(messages):
    polarities = []
    for msg in messages:
        analysis = TextBlob(msg["message"])
        polarities.append(analysis.sentiment.polarity)

    return np.mean(polarities) if polarities else 0

def display_chat_summary(chat_data):
    if not chat_data:
        print("No chat data to display.")
        return
    print("\nMessages Per User:")
    for user, count in chat_data["user_message_count"].items():
        print(f"{user}: {count} messages")

    daily_freq = daily_chat_frequency(chat_data["timestamps"])
    avg_messages_per_day = average_messages_per_day(daily_freq)
    response_time= response_time_analysis(chat_data["messages"])
    sentiment_polarity = sentiment_analysis(chat_data["messages"])
    return {
        "Chat Start Time": chat_data['chat_start'],
        "Chat End Time": chat_data['chat_end'],
        "Total Participants": len(chat_data['users']),
        "Participants": ', '.join(chat_data['users']),
        "Total Messages": len(chat_data['messages']),
        "Daily Chat Frequency": len(daily_freq),
        "Average Messages Per Day": avg_messages_per_day,
        "Overall Average Response Time": response_time,
        "Total Emojis Used": sum(chat_data['emoji_count'].values()),
        "Number of Links Shared": chat_data['link_count'],
        "Chat Sentiment Polarity (−1 to 1)": sentiment_polarity
    }

@app.route('/')
def home():
    return "Welcome to WhatsApp Chat Summary."
@app.route('/upload', methods=['POST'])
def upload_chat():
    
    if 'file' not in request.files:
        print("No file found in request")
        return jsonify({"error": "No file provided"}), 400
    file = request.files['file']
    if file.filename == '':
        print("File has no name")
        return jsonify({"error": "No selected file"}), 400
    os.makedirs("uploads", exist_ok=True)
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)
    try:
        chat_data = parse_whatsapp_chat(file_path)  
        chat_data = display_chat_summary(chat_data) 
        if isinstance(chat_data, set):
            chat_data = list(chat_data)
        print("File uploaded successfully:", file.filename)
        return jsonify(chat_data)
    except ValueError as e:
        print("ValueError:", str(e))
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print("Unexpected error:", str(e))
        return jsonify({"error": f"Unexpected error: {e}"}), 500
if __name__ == '__main__':
    app.run(debug=True)
