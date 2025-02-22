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
    """Parses datetime from WhatsApp chat format with flexible handling of different formats."""
    if not date_str:
        return None  # Handle missing date cases

    date_str = date_str.replace("\u202f", " ")  # Fix non-breaking space issue
    date_str = re.sub(r"\s+", " ", date_str.strip())  # Normalize extra spaces
    
    # List of possible date-time formats in WhatsApp exports
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
    """Detects system-generated messages (not written by users)."""
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
    """Parses WhatsApp chat from a file, removes system messages, and extracts structured data."""
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

        if is_system_message(line):  # Skip system messages
            continue

        match = chat_pattern.match(line)
        if match:
            date, time, _, user, message = match.groups()

            if not date:
                print(f"Skipping line due to missing date: {line}")
                continue  # Skip messages without a valid date

            # Ensure time is handled properly (defaulting if missing)
            time = time if time else "00:00"  # Default to midnight if no time provided
            
            try:
                timestamp = parse_datetime(f"{date} {time}")
                timestamps.append(timestamp)
                users.add(user)
                user_message_count[user] += 1
                messages.append({"timestamp": timestamp, "user": user, "message": message})

                # Count emojis
                for char in message:
                    if char in emoji.EMOJI_DATA:
                        emojis_count[user] += 1

                # Count links
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



import numpy as np
from collections import defaultdict
from textblob import TextBlob

def daily_chat_frequency(timestamps):
    """Returns daily chat frequency as a dictionary."""
    daily_freq = defaultdict(int)
    for ts in timestamps:
        daily_freq[ts.date()] += 1  # Use `.date()` from `datetime` object
    return daily_freq

def average_messages_per_day(daily_freq):
    """Returns the average messages per day."""
    if not daily_freq:
        return 0
    return np.mean(list(daily_freq.values()))

def response_time_analysis(messages):
    """Analyzes the response time between consecutive messages."""
    response_times = []
    prev_time = None

    for msg in messages:
        timestamp = msg["timestamp"]  # Directly use `timestamp` from parsed data
        if prev_time:
            response_times.append((timestamp - prev_time).total_seconds() / 60)
        prev_time = timestamp

    return np.mean(response_times) if response_times else 0

def sentiment_analysis(messages):
    """Performs sentiment analysis and returns polarity (-1 to 1)."""
    polarities = []
    for msg in messages:
        analysis = TextBlob(msg["message"])
        polarities.append(analysis.sentiment.polarity)

    return np.mean(polarities) if polarities else 0

def display_chat_summary(chat_data):
    """Displays a summary of the chat."""
    if not chat_data:
        print("No chat data to display.")
        return

    print("\n--- Chat Summary ---")
    print(f"Chat Start Time: {chat_data['chat_start']}")
    print(f"Chat End Time: {chat_data['chat_end']}")
    print(f"Total Participants: {len(chat_data['users'])}")
    print(f"Participants: {', '.join(chat_data['users'])}")
    print(f"Total Messages: {len(chat_data['messages'])}")

    print("\nMessages Per User:")
    for user, count in chat_data["user_message_count"].items():
        print(f"{user}: {count} messages")

    daily_freq = daily_chat_frequency(chat_data["timestamps"])
    avg_messages_per_day = average_messages_per_day(daily_freq)
    response_time = response_time_analysis(chat_data["messages"])
    sentiment_polarity = sentiment_analysis(chat_data["messages"])

    print(f"\nDaily Chat Frequency: {len(daily_freq)} days of activity")
    print(f"Average Messages Per Day: {avg_messages_per_day:.2f}")
    print(f"Overall Average Response Time: {response_time:.2f} minutes")
    print(f"Total Emojis Used: {sum(chat_data['emoji_count'].values())}")
    print(f"Number of Links Shared: {chat_data['link_count']}")
    print(f"Chat Sentiment Polarity (−1 to 1): {sentiment_polarity:.2f}")

@app.route('/')
def home():
    return "Welcome to WhatsApp Chat Summary."
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
        chat_data = display_chat_summary(file_path)
        return jsonify(chat_data)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {e}"}), 500


# Example usage
chat_file = "WA_chat4.txt"  # Change this to your file name
try:
    chat_data = parse_whatsapp_chat(chat_file)
    display_chat_summary(chat_data)
except ValueError as e:
    print(e)
except Exception as e:
    print(f"Unexpected error: {e}")
