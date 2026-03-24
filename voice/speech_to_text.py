"""
🎤 SPEECH TO TEXT
Multiple STT provider support: Whisper, Google, Browser API
"""

import asyncio
import aiohttp
import base64
import tempfile
import os
from typing import Optional, Dict, Any
from datetime import datetime
from utils.logger import logger


class SpeechToText:
    """
    🎤 SPEECH TO TEXT ENGINE
    
    Supports:
    - OpenAI Whisper API (most accurate)
    - Google Speech-to-Text
    - Browser Web Speech API (frontend)
    """
    
    def __init__(self):
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.google_key = os.getenv("GOOGLE_CLOUD_API_KEY")
        
        # Determine best available provider
        if self.openai_key:
            self.provider = "whisper"
            logger.info("🎤 STT using OpenAI Whisper (high accuracy)")
        elif self.google_key:
            self.provider = "google"
            logger.info("🎤 STT using Google Speech-to-Text")
        else:
            self.provider = "browser"
            logger.info("🎤 STT using Browser Web Speech API")
        
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str = "webm",
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Transcribe audio to text
        
        Args:
            audio_data: Raw audio bytes
            audio_format: Audio format (webm, wav, mp3)
            language: Language code (en, hi, etc.)
        
        Returns:
            {
                "text": "transcribed text",
                "confidence": 0.95,
                "language": "en",
                "duration_ms": 2500
            }
        """
        start_time = datetime.now()
        
        try:
            if self.provider == "whisper":
                result = await self._transcribe_whisper(audio_data, audio_format, language)
            elif self.provider == "google":
                result = await self._transcribe_google(audio_data, audio_format, language)
            else:
                # Browser-based - return placeholder
                result = {
                    "text": "",
                    "confidence": 0.0,
                    "error": "Use browser Web Speech API for recording"
                }
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            result["processing_time_ms"] = round(duration, 2)
            
            logger.info(f"🎤 Transcribed: '{result.get('text', '')[:50]}...'")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ STT error: {e}")
            return {
                "text": "",
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def _transcribe_whisper(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str
    ) -> Dict[str, Any]:
        """Transcribe using OpenAI Whisper API"""
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(
            suffix=f".{audio_format}",
            delete=False
        ) as f:
            f.write(audio_data)
            temp_path = f.name
        
        try:
            session = await self._get_session()
            
            # Prepare multipart form data
            data = aiohttp.FormData()
            data.add_field(
                'file',
                open(temp_path, 'rb'),
                filename=f'audio.{audio_format}',
                content_type=f'audio/{audio_format}'
            )
            data.add_field('model', 'whisper-1')
            data.add_field('language', language)
            data.add_field('response_format', 'verbose_json')
            
            headers = {
                "Authorization": f"Bearer {self.openai_key}"
            }
            
            async with session.post(
                "https://api.openai.com/v1/audio/transcriptions",
                data=data,
                headers=headers
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise ValueError(f"Whisper API error: {response.status} - {text}")
                
                result = await response.json()
            
            return {
                "text": result.get("text", ""),
                "confidence": 0.95,  # Whisper doesn't provide confidence
                "language": result.get("language", language),
                "duration_ms": result.get("duration", 0) * 1000
            }
            
        finally:
            # Clean up temp file
            os.unlink(temp_path)
    
    async def _transcribe_google(
        self,
        audio_data: bytes,
        audio_format: str,
        language: str
    ) -> Dict[str, Any]:
        """Transcribe using Google Speech-to-Text API"""
        
        session = await self._get_session()
        
        # Encode audio
        audio_content = base64.b64encode(audio_data).decode('utf-8')
        
        # Prepare request
        encoding_map = {
            "webm": "WEBM_OPUS",
            "wav": "LINEAR16",
            "mp3": "MP3",
            "ogg": "OGG_OPUS"
        }
        
        payload = {
            "config": {
                "encoding": encoding_map.get(audio_format, "WEBM_OPUS"),
                "sampleRateHertz": 48000,
                "languageCode": language,
                "enableAutomaticPunctuation": True,
                "model": "latest_long"
            },
            "audio": {
                "content": audio_content
            }
        }
        
        url = f"https://speech.googleapis.com/v1/speech:recognize?key={self.google_key}"
        
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                text = await response.text()
                raise ValueError(f"Google STT error: {response.status} - {text}")
            
            result = await response.json()
        
        # Parse result
        results = result.get("results", [])
        if not results:
            return {"text": "", "confidence": 0.0}
        
        alternative = results[0].get("alternatives", [{}])[0]
        
        return {
            "text": alternative.get("transcript", ""),
            "confidence": alternative.get("confidence", 0.0),
            "language": language
        }
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()


# Singleton
_stt_instance: Optional[SpeechToText] = None

def get_stt() -> SpeechToText:
    """Get or create STT instance"""
    global _stt_instance
    if _stt_instance is None:
        _stt_instance = SpeechToText()
    return _stt_instance