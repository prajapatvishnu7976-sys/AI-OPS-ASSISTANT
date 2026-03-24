"""
🔊 TEXT-TO-SPEECH (TTS) SERVICE
Converts text to audio using OpenAI TTS
"""

import os
from typing import Dict, Any, Optional
from utils.logger import logger

# OpenAI import
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Google Cloud import (optional)
try:
    from google.cloud import texttospeech
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    logger.info("ℹ️ Google Cloud TTS not installed (optional)")


class TTSService:
    """
    🔊 Text-to-Speech Service
    
    Supports:
    - OpenAI TTS (realistic voices, recommended)
    - Google Cloud TTS (optional)
    """
    
    VOICES = {
        "openai": {
            "alloy": "Neutral, balanced",
            "echo": "Male, clear",
            "fable": "British accent",
            "onyx": "Deep male",
            "nova": "Female, energetic",
            "shimmer": "Soft female"
        },
        "google": {
            "en-US-Neural2-A": "Male",
            "en-US-Neural2-C": "Female",
            "en-US-Neural2-D": "Male, deep",
            "en-US-Neural2-F": "Female, warm"
        }
    }
    
    def __init__(self, provider: str = "openai", voice: str = "nova"):
        """
        Initialize TTS service
        
        Args:
            provider: 'openai' or 'google'
            voice: Voice name (see VOICES dict)
        """
        self.provider = provider
        self.voice = voice
        self.client = None
        
        if provider == "openai":
            self.api_key = os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError("OPENAI_API_KEY not set for TTS")
            
            if not OPENAI_AVAILABLE:
                raise ValueError("OpenAI package not installed. Run: pip install openai")
            
            self.client = OpenAI(api_key=self.api_key)
            logger.info(f"🔊 TTS using OpenAI ({voice} voice)")
            
        elif provider == "google":
            if not GOOGLE_AVAILABLE:
                raise ValueError("Google Cloud TTS not installed. Run: pip install google-cloud-texttospeech")
            
            self.client = texttospeech.TextToSpeechClient()
            logger.info(f"🔊 TTS using Google Cloud ({voice} voice)")
            
        else:
            raise ValueError(f"Unknown TTS provider: {provider}")
    
    async def synthesize(
        self, 
        text: str, 
        speed: float = 1.0,
        format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Convert text to speech
        
        Args:
            text: Text to speak
            speed: Speech rate (0.5 to 2.0)
            format: Audio format (mp3, wav, opus)
            
        Returns:
            {
                "audio_data": bytes,
                "format": "mp3",
                "duration_ms": 1234,
                "text_length": 100
            }
        """
        try:
            if self.provider == "openai":
                return await self._synthesize_openai(text, speed, format)
            elif self.provider == "google":
                return await self._synthesize_google(text, speed)
                
        except Exception as e:
            logger.error(f"❌ TTS Error: {e}")
            return {
                "audio_data": b"",
                "error": str(e)
            }
    
    async def _synthesize_openai(
        self, 
        text: str, 
        speed: float,
        format: str
    ) -> Dict:
        """Synthesize using OpenAI TTS"""
        
        # Truncate if too long (OpenAI limit: 4096 chars)
        if len(text) > 4000:
            text = text[:4000] + "..."
        
        response = self.client.audio.speech.create(
            model="tts-1",  # or "tts-1-hd" for higher quality
            voice=self.voice,
            input=text,
            speed=speed,
            response_format=format
        )
        
        audio_data = response.content
        
        logger.info(f"🔊 OpenAI TTS: Generated {len(audio_data)} bytes")
        
        return {
            "audio_data": audio_data,
            "format": format,
            "text_length": len(text),
            "provider": "openai",
            "voice": self.voice
        }
    
    async def _synthesize_google(
        self, 
        text: str, 
        speed: float
    ) -> Dict:
        """Synthesize using Google Cloud TTS"""
        
        if not GOOGLE_AVAILABLE:
            raise ValueError("Google Cloud TTS not available")
        
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name=self.voice
        )
        
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=speed,
            pitch=0.0
        )
        
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        audio_data = response.audio_content
        
        logger.info(f"🔊 Google TTS: Generated {len(audio_data)} bytes")
        
        return {
            "audio_data": audio_data,
            "format": "mp3",
            "text_length": len(text),
            "provider": "google",
            "voice": self.voice
        }


# ============ SINGLETON ============
_tts_instance: Optional[TTSService] = None


def get_tts_service(provider: str = "openai", voice: str = "nova") -> TTSService:
    """Get or create TTS service instance"""
    global _tts_instance
    
    if _tts_instance is None:
        _tts_instance = TTSService(provider=provider, voice=voice)
    
    return _tts_instance