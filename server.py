import os,sys,uuid,json
from ibm_cloud_sdk_core.authenticators import IAMAuthenticator
from ibm_watson import SpeechToTextV1,TextToSpeechV1, AssistantV2
from dotenv import load_dotenv, find_dotenv
from flask import Flask, render_template, request, Response

load_dotenv(find_dotenv())


stt_api = os.environ.get("stt_api")
stt_url = os.environ.get("stt_url")

tts_api = os.environ.get("tts_api")
tts_url = os.environ.get("tts_url")

assistant_api = os.environ.get("assistant_api")
assistant_url = os.environ.get("assistant_url")

ASSISTANT_ID = os.environ.get("assistant_id")
app = Flask(__name__)
response_text = None

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
    response=assistant.message(assistant_id=ASSISTANT_ID,session_id=session_id, 
input={'message_type': 'text','text': chat_text}).get_result()
    response_text = response["output"]["generic"][0]["text"]
    authenticator = IAMAuthenticator(tts_api)
    text_to_speech = TextToSpeechV1(
        authenticator=authenticator
    )
    text_to_speech.set_service_url(tts_url)
    resp_file = "response"+str(uuid.uuid1())[0:4]+".mp3"
    with open(resp_file, 'wb') as audio_file:
        audio_file.write(
            text_to_speech.synthesize(
                response_text,
                voice='en-US_MichaelV3Voice',
                accept='audio/mp3'        
            ).get_result().content)

    return resp_file

@app.route('/audio/<filename>')
def stream_mp3(filename):
    def generate():
        with open(filename, 'rb') as fmp3:
            data = fmp3.read(1024)
            while data:
                yield data
                data = fmp3.read(1024)
    return Response(generate(), mimetype="audio/mpeg3")


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
                f.save(f.filename)
                stt_text=speechToText(f.filename,extn)
                os.remove(f.filename)
                return getResponseFromAssistant(stt_text)
            else:
                raise Exception("Sorry. No filename recognized")
        except Exception as excp:
            print(excp.__traceback__)
            return str(excp),500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)