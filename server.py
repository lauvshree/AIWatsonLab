import os
import json
from bs4 import BeautifulSoup
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import SpeechToTextV1
from ibm_watson import AssistantV2
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request
import sys

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


def speechToText(filename, extn):
    recognition_service=SpeechToTextV1(IAMAuthenticator(stt_api))
    recognition_service.set_service_url(stt_url)
    SPEECH_EXTENSION="*."+extn
    SPEECH_AUDIOTYPE="audio/"+extn
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
    print(response)
    return response["output"]["generic"][0]["text"]

@app.route('/uploader', methods = ['POST'])
def upload_file():
   if request.method == 'POST':
        f = request.files['file']
        try:
            if f.filename != '':
                l = len(f.filename)
                extn = f.filename[l-3:l]
                if extn not in ["mp3","wav"]:
                    raise Exception("Sorry, the file type is unsupported. Try .mp3 or .wav files")
                print("The file type is ",extn )
                f.save(f.filename)
                stt_text=speechToText(f.filename,extn)
                return getResponseFromAssistant(stt_text)
            else:
                raise Exception("Sorry. No filename recognized")
        except Exception as excp:
            print(excp)
            return str(excp),500
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
