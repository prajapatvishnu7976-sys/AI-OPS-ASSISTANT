"""
🎤 SPEECH-TO-TEXT (STT) SERVICE
Converts audio to text using OpenAI Whisper
"""

import os
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path
from utils.logger import logger

# OpenAI import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Google Cloud import (optional)
try:
    from google.cloud import speech_v1
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.info("ℹ️ Google Cloud Speech not installed (optional)")


class STTService:
    """
    🎤 Speech-to-Text Service
    
    Supports:
    - OpenAI Whisper (default, recommended)
    - Google Cloud Speech-to-Text (optional)
    """
    
    def __init__(self, provider: str = "whisper"):
        """
        Initialize STT service
        
        Args:
            provider: 'whisper' or 'google'
        """
        self.provider = provider
        self.client = None
        
        if provider == "whisper":
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set for Whisper")
            
            if not OPENAI_AVAILABLE:
                raise ValueError("OpenAI package not installed. Run: pip install openai")
            
            self.client = OpenAI(api_key=self.api_key)
            logger.info("🎤 STT using OpenAI Whisper (high accuracy)")
            
        elif provider == "google":
            if not GOOGLE_AVAILABLE:
                raise ValueError("Google Cloud Speech not installed. Run: pip install google-cloud-speech")
            
            self.client = speech_v1.SpeechClient()
            logger.info("🎤 STT using Google Cloud Speech")
            
        else:
            raise ValueError(f"Unknown STT provider: {provider}")
    
    async def transcribe(
        self, 
        audio_data: bytes, 
        language: str = "en",
        format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Raw audio bytes
            language: Language code (en, es, fr, etc.)
            format: Audio format (wav, mp3, webm)
            
        Returns:
            {
                "transcript": "transcribed text",
                "confidence": 0.95,
                "language": "en",
                "duration_ms": 1234
            }
        """
        try:
            if self.provider == "whisper":
                return await self._transcribe_whisper(audio_data, language, format)
            elif self.provider == "google":
                return await self._transcribe_google(audio_data, language)
            
        except Exception as e:
            logger.error(f"❌ STT Error: {e}")
            return {
                "transcript": "",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _transcribe_whisper(
        self, 
        audio_data: bytes, 
        language: str,
        format: str
    ) -> Dict:
        """Transcribe using OpenAI Whisper"""
        
        # Create temporary file
        suffix = f".{format}"
        
        try:
            # Write audio to temp file (Whisper API needs file)
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_path = temp_file.name
            
            # Transcribe
            with open(temp_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language if language != "auto" else None,
                    response_format="verbose_json"
                )
            
            transcript = response.text
            
            logger.info(f"✅ Whisper: '{transcript[:50]}...'")
            
            return {
                "transcript": transcript.strip(),
                "confidence": 0.95,  # Whisper doesn't return confidence
                "language": getattr(response, 'language', language),
                "duration_ms": int(getattr(response, 'duration', 0) * 1000),
                "provider": "whisper"
            }
            
        finally:
            # Clean up temp file
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass
    
    async def _transcribe_google(
        self, 
        audio_data: bytes, 
        language: str
    ) -> Dict:
        """Transcribe using Google Cloud Speech"""
        
        if not GOOGLE_AVAILABLE:
            raise ValueError("Google Cloud Speech not available")
        
        audio = speech_v1.RecognitionAudio(content=audio_data)
        
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=16000,
            language_code=language,
            enable_automatic_punctuation=True,
            model="latest_long"
        )
        
        response = self.client.recognize(config=config, audio=audio)
        
        if not response.results:
            return {
                "transcript": "",
                "confidence": 0.0,
                "language": language,
                "provider": "google"
            }
        
        result = response.results[0]
        alternative = result.alternatives[0]
        
        logger.info(f"✅ Google STT: '{alternative.transcript[:50]}...'")
        
        return {
            "transcript": alternative.transcript.strip(),
            "confidence": alternative.confidence,
            "language": language,
            "provider": "google"
        }


# ============ SINGLETON ============
_stt_instance: Optional[STTService] = None


def get_stt_service(provider: str = "whisper") -> STTService:
    """Get or create STT service instance"""
    global _stt_instance
    
    if _stt_instance is None:
        _stt_instance = STTService(provider=provider)
    
    return _stt_instance