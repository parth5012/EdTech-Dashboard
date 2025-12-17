import assemblyai as aai
from utils.models import JobApplication
from utils.app import db
from uuid import UUID
from typing import List

def get_transcription(audio: __file__) -> str:
    config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.universal)

    transcript = aai.Transcriber(config=config).transcribe(audio)

    if transcript.status == "error":
        raise RuntimeError(f"Transcription failed: {transcript.error}")

    return transcript.text

def find_missing_words_count(user_id: UUID) -> int:
    apps = db.session.query(JobApplication).filter_by(user_id=user_id).all()
    missing_counts = {}
    
    for app in apps:
        # Assuming keyword_analysis is stored as {'missing': ['SQL', 'Java']}
        if app.keyword_analysis and 'missing' in app.keyword_analysis:
            for word in app.keyword_analysis['missing']:
                missing_counts[word] = missing_counts.get(word, 0) + 1
    
    # Sort top 5 missing skills
    top_missing = sorted(missing_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    return top_missing

def find_filler_word_count(answers: List[str]):
    filler_words = ['um', 'uh', 'like', 'actually', 'basically']
    total_fillers = 0
    fillers_per_question = [] # For the Bar Chart
    
    for ans in answers:
        text = ans.transcribed_text.lower() if ans.transcribed_text else ""
        count = sum(text.count(word) for word in filler_words)
        total_fillers += count
        fillers_per_question.append(count)