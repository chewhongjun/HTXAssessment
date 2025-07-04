"""ASR API service using FastAPI and Hugging Face wav2vec2 model."""

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torch
import io
import torchaudio

app = FastAPI()

# Model and processor initialization
MODEL_NAME = "facebook/wav2vec2-large-960h"
processor = Wav2Vec2Processor.from_pretrained(MODEL_NAME)
model = Wav2Vec2ForCTC.from_pretrained(MODEL_NAME)

@app.get("/ping")
async def ping() -> dict:
    """Health check endpoint to verify service is running."""
    return {"message": "pong"}

@app.post("/asr")
async def transcribe(file: UploadFile = File(...)) -> JSONResponse:
    """Transcribe uploaded MP3 audio file to text using wav2vec2 model.

    Args:
        file (UploadFile): Uploaded audio file in MP3 format.

    Returns:
        JSONResponse: JSON containing transcription text and audio duration in seconds.
    """
    # Read uploaded file bytes
    audio_bytes = await file.read()
    audio_buffer = io.BytesIO(audio_bytes)

    # Load audio waveform and sample rate
    waveform, sample_rate = torchaudio.load(audio_buffer)

    # Calculate audio duration in seconds
    duration = waveform.shape[1] / sample_rate

    # Resample audio to 16kHz if necessary
    TARGET_SAMPLE_RATE = 16000
    if sample_rate != TARGET_SAMPLE_RATE:
        resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=TARGET_SAMPLE_RATE)
        waveform = resampler(waveform)

    # Prepare input tensor for model
    input_values = processor(waveform.squeeze().numpy(), sampling_rate=TARGET_SAMPLE_RATE, return_tensors="pt").input_values

    # Perform inference without gradient calculation
    with torch.no_grad():
        logits = model(input_values).logits

    # Decode predicted token IDs to transcription text
    predicted_ids = torch.argmax(logits, dim=-1)
    transcription = processor.decode(predicted_ids[0])

    # Return transcription and duration as JSON
    return JSONResponse(content={"transcription": transcription, "duration": f"{duration:.1f}"})
