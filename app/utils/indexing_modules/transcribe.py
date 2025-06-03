from openai import OpenAI
from ...utils.publish import publish_video_process_status 
import os
import requests
import subprocess
import openai
from  dotenv import load_dotenv
load_dotenv()
client =OpenAI()

def download_video(video_url, lesson_id):
    save_dir = f"/mnt/uploads/{lesson_id}"
    os.makedirs(save_dir, exist_ok=True)
    video_path = os.path.join(save_dir, "video.mp4")
    
    # Download the video file
    with requests.get(video_url, stream=True) as r:
        r.raise_for_status()
        with open(video_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

    # Transcribe the video
    with open(video_path, "rb") as video_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=video_file,
            response_format="verbose_json"
        )
    print(transcript.segments)
    return transcript.segments



def extract_audio_from_video(video_path, audio_path=None):
    print(os.path.dirname(video_path))
    print("[WORKER DEBUG] CWD:", os.getcwd())
    print("[WORKER DEBUG] Input exists:", os.path.exists(video_path))
    print("[WORKER DEBUG] Input path:", video_path)
    print("[WORKER DEBUG] Listing parent dir:", os.listdir(os.path.dirname(video_path)))
    if audio_path is None:
        audio_path = os.path.join(os.path.dirname(video_path), "audio.wav")
        print(audio_path)
        command = [
            "ffmpeg", "-y", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", audio_path
        ]
        print("Running:", " ".join(command))
        os.system(" ".join(command))

        print("ffmpeg completed with code:")
        return audio_path

def transcribe_with_whisper(audio_path):
    with open(audio_path, "rb") as audio_file:
         transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
    return transcript["segments"]

# -------- Usage Example --------
def transcribe(user_id,lesson_id,video_url):
    # Step 1: Download video
    publish_video_process_status(user_id,step="downloading video")
    transcript = download_video(video_url, lesson_id)
    print(f"Downloaded video to {transcript[0]}")
    
    # publish_video_process_status(user_id,step="extracting audio")
    # # Step 2: Extract audio
    # audio_path = extract_audio_from_video(video_path)
    # print(f"Extracted audio to {audio_path}")
    
    # publish_video_process_status(user_id,step="transcripting to text")
    # # Step 3: Transcribe audio
    # segments = transcribe_with_whisper(audio_path)
    # print("First segment:", segments)
    
    return transcript
