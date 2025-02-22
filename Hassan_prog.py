import re
import pandas as pd
import emoji
from datetime import datetime
from collections import Counter
from textblob import TextBlob

def count_messages(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        messages = file.readlines()
    return len(messages)

def count_emojis(text):
    emoji_pattern = re.compile(
        "[\U0001F600-\U0001F64F"  # Emoticons
        "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
        "\U0001F680-\U0001F6FF"  # Transport and Map Symbols
        "\U0001F700-\U0001F77F"  # Alchemical Symbols
        "\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
        "\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
        "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
        "\U0001FA00-\U0001FA6F"  # Chess Symbols
        "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
        "\U00002702-\U000027B0"  # Dingbats
        "\U000024C2-\U0001F251"  # Enclosed characters
        "]+", flags=re.UNICODE)
    return len(re.findall(emoji_pattern, text))

def count_links(text):
    links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    return len(links)


def calculate_avg_response_time(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()
    timestamps = []
    for line in lines:
        timestamp_str = line.split(' - ')[0].strip()
        try:
            timestamp = datetime.strptime(timestamp_str, '%m/%d/%y, %I:%M %p')  
            timestamps.append(timestamp)
        except ValueError:
            continue

    response_times = []
    for i in range(1, len(timestamps)):
        response_times.append((timestamps[i] - timestamps[i - 1]).total_seconds())  # Total seconds
    avg_response_seconds = sum(response_times) / len(response_times) if response_times else 0
    avg_response_minutes = avg_response_seconds // 60
    avg_response_seconds = avg_response_seconds % 60
    return int(avg_response_minutes), round(avg_response_seconds, 2)

def sentiment_analysis(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    sentiment_percentage = (polarity + 1) * 50
    return round(sentiment_percentage, 2)

def analyze_file(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()

    num_messages = count_messages(filename)
    emoji_count = count_emojis(content)
    link_count = count_links(content)
    avg_response_minutes, avg_response_seconds = calculate_avg_response_time(filename)
    sentiment = sentiment_analysis(content)

    # Print results
    print(f"Number of Messages: {num_messages}")
    print(f"Emoji Count: {emoji_count}")
    print(f"Link Count: {link_count}")
    print(f"Average Response Time: {avg_response_minutes} minutes and {avg_response_seconds} seconds")
    print(f"Sentiment: {sentiment}%")
   

analyze_file('WA_chat.txt')
