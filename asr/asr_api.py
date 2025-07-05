# asr_api.py

"""ASR API service using FastAPI and Hugging Face wav2vec2 model."""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
import torch
import io
import torchaudio # <-- COMMENT OUT OR REMOVE THIS LINE
import soundfile as sf # <-- ADD THIS LINE
import numpy as np # <-- ADD THIS LINE
import uvicorn
import traceback
import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('asr_api.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="ASR API Service")

# Model and processor initialization
try:
    MODEL_NAME = "facebook/wav2vec2-large-960h"
    processor = Wav2Vec2Processor.from_pretrained(MODEL_NAME)
    model = Wav2Vec2ForCTC.from_pretrained(MODEL_NAME)
    logger.info(f"ASR model '{MODEL_NAME}' loaded successfully.")
except Exception as e:
    logger.error(f"Error loading ASR model: {e}")
    logger.error(traceback.format_exc())
    # Consider exiting or raising if the model couldn't load.
    # For now, it will proceed but /asr will likely fail.

@app.get("/ping")
async def ping() -> dict:
    """Health check endpoint to verify service is running."""
    logger.info("Health check endpoint accessed")
    return {"message": "pong"}

@app.post("/asr")
async def transcribe(file: UploadFile = File(...)) -> JSONResponse:
    """Transcribe uploaded MP3 audio file to text using wav2vec2 model.

    Args:
        file (UploadFile): Uploaded audio file in MP3 format.

    Returns:
        JSONResponse: JSON containing transcription text and audio duration in seconds.
    """
    start_time = time.time()
    request_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000) % 1000}"
    
    logger.info(f"[{request_id}] Transcription request started for file: {file.filename}")
    logger.info(f"[{request_id}] File size: {file.size if hasattr(file, 'size') else 'unknown'} bytes")
    logger.info(f"[{request_id}] Content type: {file.content_type}")
    
    try:
        # Read file
        logger.debug(f"[{request_id}] Reading uploaded file...")
        audio_bytes = await file.read()
        audio_buffer = io.BytesIO(audio_bytes)
        logger.info(f"[{request_id}] File read successfully, size: {len(audio_bytes)} bytes")

        # --- CHANGE START ---
        # Load audio waveform and sample rate using soundfile
        logger.debug(f"[{request_id}] Loading audio waveform...")
        waveform_np, sample_rate = sf.read(audio_buffer)
        logger.info(f"[{request_id}] Audio loaded - Sample rate: {sample_rate}Hz, Shape: {waveform_np.shape}")

        # Convert numpy array to torch tensor
        # wav2vec2 expects mono audio, so if it's stereo, take one channel
        if waveform_np.ndim > 1:
            waveform = torch.from_numpy(waveform_np[:, 0]).float().unsqueeze(0)  # mono
        else:
            waveform = torch.from_numpy(waveform_np).float().unsqueeze(0)
        # --- CHANGE END ---

        # Calculate audio duration in seconds
        duration = waveform.shape[1] / sample_rate
        logger.info(f"[{request_id}] Audio duration: {duration:.2f} seconds")

        # Resample audio to 16kHz if necessary
        TARGET_SAMPLE_RATE = 16000
        if sample_rate != TARGET_SAMPLE_RATE:
            logger.info(f"[{request_id}] Resampling from {sample_rate}Hz to {TARGET_SAMPLE_RATE}Hz")
            resampler = torchaudio.transforms.Resample(orig_freq=sample_rate, new_freq=TARGET_SAMPLE_RATE)
            waveform = resampler(waveform)
            logger.debug(f"[{request_id}] Resampling completed")
        else:
            logger.debug(f"[{request_id}] No resampling needed")

        # Prepare input tensor for model
        logger.debug(f"[{request_id}] Preparing input for model...")
        input_values = processor(waveform.squeeze().cpu().numpy(), sampling_rate=TARGET_SAMPLE_RATE, return_tensors="pt").input_values
        logger.debug(f"[{request_id}] Input tensor shape: {input_values.shape}")

        # Perform inference without gradient calculation
        logger.info(f"[{request_id}] Starting model inference...")
        inference_start = time.time()
        with torch.no_grad():
            logits = model(input_values.to(model.device)).logits
        inference_time = time.time() - inference_start
        logger.info(f"[{request_id}] Model inference completed in {inference_time:.3f} seconds")

        # Decode predicted token IDs to transcription text
        logger.debug(f"[{request_id}] Decoding transcription...")
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = processor.decode(predicted_ids[0])
        logger.info(f"[{request_id}] Transcription result: '{transcription[:100]}{'...' if len(transcription) > 100 else ''}'")

        # Calculate total processing time
        total_time = time.time() - start_time
        logger.info(f"[{request_id}] Total processing time: {total_time:.3f} seconds")
        logger.info(f"[{request_id}] Transcription request completed successfully")

        # Return transcription and duration as JSON
        return JSONResponse(content={"transcription": transcription, "duration": f"{duration:.1f}"})

    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"[{request_id}] An error occurred during transcription for file: {file.filename}")
        logger.error(f"[{request_id}] Error after {error_time:.3f} seconds: {str(e)}")
        logger.error(f"[{request_id}] Full traceback:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal Server Error during transcription. Please check server logs for details. Error: {e}"
        )

if __name__ == "__main__":
    logger.info("Starting Uvicorn server...")
    uvicorn.run("asr_api:app", host="127.0.0.1", port=8001, reload=True)