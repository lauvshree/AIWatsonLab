import os
import json
from bs4 import BeautifulSoup
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import SpeechToTextV1
from ibm_watson import AssistantV2
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request

load_dotenv(find_dotenv())


stt_api = os.environ.get("stt_api")
stt_url = os.environ.get("stt_url")

assistant_api = os.environ.get("assistant_api")
assistant_url = os.environ.get("assistant_url")

ASSISTANT_ID = os.environ.get("assistant_id")
print("************* Assistant_id is  ",ASSISTANT_ID)
app = Flask(__name__)

load_dotenv()
@app.route('/')
def file_uploader():
   return render_template('upload.html')


def speechToText(filename):
    recognition_service=SpeechToTextV1(IAMAuthenticator(stt_api))
    recognition_service.set_service_url(stt_url)
    SPEECH_EXTENSION="*.mp3"
    SPEECH_AUDIOTYPE="audio/mp3"
    audio_file=open(filename,"rb")
    result=recognition_service.recognize(audio=audio_file, content_type=SPEECH_AUDIOTYPE).get_result()
    return result["results"][0]["alternatives"][0]["transcript"]

def getResponseFromAssistant(chat_text):
    assistant=AssistantV2(version='2019-02-28',authenticator=IAMAuthenticator(assistant_api))
    assistant.set_service_url(assistant_url)
    session=assistant.create_session(assistant_id =ASSISTANT_ID)
    session_id=session.get_result()["session_id"]
    print(session_id)
    response=assistant.message(assistant_id=ASSISTANT_ID,session_id=session_id, 
input={'message_type': 'text','text': chat_text}).get_result()
    return response["output"]["generic"][0]["text"]

@app.route('/uploader', methods = ['POST'])
def upload_file():
   if request.method == 'POST':
        f = request.files['file']
        if f.filename != '':
            f.save(f.filename)
            speechToText(f.filename)
            stt_text=speechToText(f.filename)
            return getResponseFromAssistant(stt_text)
		
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
