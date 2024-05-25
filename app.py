from modal import App, Image, Secret, Volume, web_endpoint
from fastapi import Request
from fastapi.responses import StreamingResponse
from datetime import datetime
from dotenv import load_dotenv
import os
import openai
import random
import re
import smtplib
from typing import Dict

# Define the custom image
third_wheels_image = Image.debian_slim(python_version="3.10").pip_install(
    "openai==0.27.10",
    "fastapi",
    "python-dotenv",
)

# Define the volume
third_wheels_volume = Volume.from_name("third-wheels")

# Load environment variables from .env file
load_dotenv()

# Set up your OpenAI API key from .env file
openai.api_key = os.getenv('OPENAI_API_KEY')

app = App("third-wheels-modal-app", image=third_wheels_image, volumes={"/volumes/third-wheels": third_wheels_volume})

@app.cls(
    secrets=[Secret.from_name("third-wheels-secret")],
)
class ThirdWheels:
    def __init__(self):
        self.smtpObj = smtplib.SMTP('smtp.qq.com', 587)
        self.login()

    def login(self):
        self.smtpObj.ehlo()
        self.smtpObj.starttls()
        self.smtpObj.login(os.getenv('EMAIL_USER'), os.getenv('EMAIL_PASSWORD'))

    def generate_dataset(self, id):
        """Generates a single dataset entry."""
        speakers = ["belinda", "john", "sarah", "alex"]
        tones = ["warm and fuzzy", "neutral", "sad", "excited", "frustrated"]
        facial_expressions = ["smiling", "frowning", "neutral", "surprised", "angry"]
        apps = ["Instagram", "TikTok", "YouTube", "WhatsApp", "Spotify", "Gmail", "Calendar"]
        events = ["gym", "work meeting", "dinner with friends", "movie", "grocery shopping"]

        conversation = [
            {"bot": "Heyhey, Jill! How’s your day going so far? Anything fun or exciting happen?", "user": "Not really. I haven't talked to Alex lately."},
            {"bot": "Aww, that sucks. Have you been busy, or is he just MIA?", "user": "He is.. actually, do you think he is cheating on me?"},
            {"bot": "Oh no, that’s a tough feeling to shake. Why do you think that?", "user": "I mean he hasn't been calling me, and when we called, he seems really absent."},
            {"bot": "I get why that’s worrying. Maybe he’s just super stressed or distracted with something?", "user": "I am not sure, I just feel like he should be talking to me more."},
            {"bot": "Totally fair, you deserve that connection. Have you tried letting him know how you feel?"}
        ]

        calendar = []
        for _ in range(random.randint(0, 3)):  # Generate 0-3 calendar events
            hour = random.randint(7, 22)
            minute = random.choice(["00", "30"])
            end_hour = hour + 1 if hour < 22 else 22
            calendar.append({
                "time": f"{hour}:{minute} - {end_hour}:{minute}",
                "event": random.choice(events)
            })

        app_usage = []
        for _ in range(random.randint(0, 5)):  # Generate 0-5 app usage entries
            hour = random.randint(7, 23)
            minute = random.choice(["00", "30"])
            end_minute = "30" if minute == "00" else "00"
            end_hour = hour if minute == "00" else hour + 1
            app_usage.append({
                "time": f"{hour}:{minute} - {end_hour}:{end_minute}",
                "app": random.choice(apps)
            })

        dataset = {
            "id": str(id),
            "conversation": random.choice(conversation),
            "tone": random.choice(tones),
            "facial expressions": random.choice(facial_expressions),
            "Time of the day": f"{random.randint(0, 23):02}:{random.randint(0, 59):02}",
            "calendar of the day": calendar,
            "Application Usage": app_usage
        }

        return dataset

    def evaluate_the_score(self, input):
        prompt = f"""
        Generate a conversation where the user feels lonely.
        After the conversation, provide a loneliness score between 0 and 1, where 1 is the most lonely state.
        Use the following structure for the conversation:

        {input}

        output the score(in float) only:
        []
        """

        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        return response.choices[0].text.strip()

    def message_to_remind(self, score):
        prompt = f"""
        Generate a text message to remind the user to communicate with his/her companion.
        Don't mention the following below in the message.
        His/her companion's loneliness score is between 0 and 1, where 1 is the most lonely state.
        His/her companion's loneliness score is:

        {score}

        output the text message only: []
        """

        response = openai.Completion.create(
            model="gpt-3.5-turbo-instruct",
            prompt=prompt,
            temperature=1,
            max_tokens=256,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )

        return response.choices[0].text.strip()

    def main(self, data):
        conversation, tone, facial, time = data['conversation'], data['tone'], data['facial expressions'], data['Time of the day']

        tone_score_table = {"warm and fuzzy": 0.5, "neutral": 0.5, "sad": 0.9, "excited": 1, "frustrated": 0.5}
        facial_score_table = {"smiling": 0.5, "frowning": 0.2, "neutral": 0.9, "surprised": 1, "angry": 0.5}

        hour = int(time.split(':')[0])  # Extract the hour and convert to integer

        if hour < 8:
            time_dummy = 0
        elif 8 <= hour < 12:
            time_dummy = 1
        elif 12 <= hour < 18:
            time_dummy = 2
        else:
            time_dummy = 3

        weights_by_time = {
            0: {'conversation_weight': 0.6, 'tone_weight': 0.2, 'facial_weight': 0.2},
            1: {'conversation_weight': 0.5, 'tone_weight': 0.25, 'facial_weight': 0.25},
            2: {'conversation_weight': 0.4, 'tone_weight': 0.3, 'facial_weight': 0.3},
            3: {'conversation_weight': 0.7, 'tone_weight': 0.15, 'facial_weight': 0.15}
        }

        tone_score = tone_score_table[tone]
        facial_score = facial_score_table[facial]
        numbers = re.findall(r"[-+]?\d*\.\d+|\d+", self.evaluate_the_score(conversation))

        try:
            conversation_score = float(numbers[0])
        except:
            conversation_score = 0

        selected_weights = weights_by_time[time_dummy]

        aggregated_score = (selected_weights['conversation_weight'] * conversation_score +
                            selected_weights['tone_weight'] * tone_score +
                            selected_weights['facial_weight'] * facial_score)

        return aggregated_score

    @web_endpoint(method="POST")
    def web_inference(self, request: Request, item: Dict):
        data = item["data"]
        print("Data: ", data)
        aggregated_score = self.main(data)
        print("Aggregated score: ", aggregated_score)
        message = self.message_to_remind(aggregated_score)
        print("Message: ", message)
        return {"aggregated_score": aggregated_score, "message": message}

    def mail_sender(self, name, email, passage):
        body = f'Subject: [Kindly Reminder] Talk to your sweet heat\r\nFrom: 451165547@qq.com\r\n\r\nDear {name}, \n\n{passage}'
        body = body.encode('utf-8')  # Specify the encoding
        print('Sending email to %s...' % email)
        sendmailStatus = self.smtpObj.sendmail('451165547@qq.com', email, body)

        if sendmailStatus != {}:
            print('There was a problem sending email to %s: %s' % (email, sendmailStatus))
        self.smtpObj.quit()


if __name__ == "__main__":
    datasets = []
    for i in range(10):
        datasets.append(generate_dataset(i + 215))

    for data in datasets:
        print("-------------------------------")
        print()
        print("data: ", data)
        aggregated_score = main(data)
