import re
from datetime import datetime
from textblob import TextBlob

# Function to count number of messages in the file
def count_messages(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        messages = file.readlines()
    return len(messages)

# Function to count emojis in the text
def count_emojis(text):
    # A more comprehensive regular expression to match emojis across different ranges
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

# Function to count links in the text
def count_links(text):
    links = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
    return len(links)

# Function to calculate average response time based on message timestamps (in minutes and seconds)
def calculate_avg_response_time(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()
    timestamps = []
    for line in lines:
        timestamp_str = line.split(' - ')[0].strip()  # Adjust based on your timestamp format
        try:
            # Adjusted format: MM/DD/YY, HH:MM AM/PM
            timestamp = datetime.strptime(timestamp_str, '%m/%d/%y, %I:%M %p')  
            timestamps.append(timestamp)
        except ValueError:
            continue  # Skip lines with invalid timestamp formats

    response_times = []
    for i in range(1, len(timestamps)):
        response_times.append((timestamps[i] - timestamps[i - 1]).total_seconds())  # Total seconds
    avg_response_seconds = sum(response_times) / len(response_times) if response_times else 0
    avg_response_minutes = avg_response_seconds // 60
    avg_response_seconds = avg_response_seconds % 60
    return int(avg_response_minutes), round(avg_response_seconds, 2)

# Function to perform sentiment analysis on the text (as a percentage)
def sentiment_analysis(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # Range from -1 (negative) to 1 (positive)
    sentiment_percentage = (polarity + 1) * 50  # Convert the polarity score to a percentage (0% to 100%)
    return round(sentiment_percentage, 2)

# Function to identify chat participants (senders) and their message counts
def identify_chat_participants(filename):
    participants = {}  # Use a dictionary to store names and message counts
    total_characters = 0  # Variable to track total characters
    start_time = None
    end_time = None

    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        lines = file.readlines()
        for line in lines:
            # Regular expression to capture the participant's name before the colon and timestamp
            match = re.match(r"(\d{1,2}/\d{1,2}/\d{2,4}), (\d{1,2}:\d{2} (AM|PM)) - (.*?):", line)
            if match:
                timestamp = match.    (1) + ', ' + match.group(2)
                sender = match.group(4)  # Extract the sender's name
                message = line.split(":", 1)[1].strip()  # Extract the message content
                
                # Update start and end time
                if start_time is None:
                    start_time = timestamp  # First message time is the chat start time
                end_time = timestamp  # Last message time is the chat end time
                
                total_characters += len(message)  # Count characters in the message
                if sender in participants:
                    participants[sender]['message_count'] += 1  # Increment the message count
                    participants[sender]['char_count'] += len(message)  # Count characters in the message
                else:
                    participants[sender] = {'message_count': 1, 'char_count': len(message)}  # Initialize the message and char count
    
    return participants, total_characters, start_time, end_time

# Function to analyze the WhatsApp chat file
def analyze_file(filename):
    with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()

    # Get all the details
    num_messages = count_messages(filename)
    emoji_count = count_emojis(content)
    link_count = count_links(content)
    avg_response_minutes, avg_response_seconds = calculate_avg_response_time(filename)
    sentiment = sentiment_analysis(content)
    participants, total_characters, start_time, end_time = identify_chat_participants(filename)

    # Print results
    print(f"Chat Start Time: {start_time}")
    print(f"Chat End Time: {end_time}")
    print(f"Number of Messages: {num_messages}")
    print(f"Emoji Count: {emoji_count}")
    print(f"Link Count: {link_count}")
    print(f"Average Response Time: {avg_response_minutes} minutes and {avg_response_seconds} seconds")
    print(f"Sentiment: {sentiment}%")
    print(f"Total Number of Characters in Chat: {total_characters}")
    print(f"Participants and Message Counts:")
    for participant, stats in participants.items():
        print(f"{participant}: {stats['message_count']} messages, {stats['char_count']} characters")

# Example usage (adjust path to your file)
analyze_file('WA_chat.txt')  # Replace 'WA_chat.txt' with your file path
