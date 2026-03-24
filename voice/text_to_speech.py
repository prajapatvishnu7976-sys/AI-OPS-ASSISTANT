"""
🔊 TEXT TO SPEECH
Multiple TTS provider support: ElevenLabs, Google, Browser API
"""

import asyncio
import aiohttp
import base64
import os
from typing import Optional, Dict, Any, List
from datetime import datetime
from utils.logger import logger


class TextToSpeech:
    """
    🔊 TEXT TO SPEECH ENGINE
    
    Supports:
    - ElevenLabs (most natural, premium)
    - Google Cloud TTS
    - OpenAI TTS
    - Browser Web Speech API (frontend fallback)
    """
    
    # ElevenLabs voice options
    ELEVENLABS_VOICES = {
        "rachel": "21m00Tcm4TlvDq8ikWAM",  # Calm, professional
        "domi": "AZnzlk1XvdvUeBnXmlld",    # Strong, confident
        "bella": "EXAVITQu4vr4xnSDxMaL",   # Soft, friendly
        "antoni": "ErXwobaYiN019PkySvjV",  # Warm, natural
        "josh": "TxGEqnHWrfWFTfGW9XjX",    # Deep, authoritative
        "arnold": "VR6AewLTigWG4xSOukaG",  # Crisp, narrator
        "adam": "pNInz6obpgDQGcFmaJgB",    # Deep, confident
        "sam": "yoZ06aMxZJJ28mfd3POQ"      # Raspy, energetic
    }
    
    # OpenAI TTS voices
    OPENAI_VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    
    def __init__(self):
        self.elevenlabs_key = os.getenv("ELEVENLABS_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.google_key = os.getenv("GOOGLE_CLOUD_API_KEY")
        
        # Determine best available provider
        if self.elevenlabs_key:
            self.provider = "elevenlabs"
            self.voice = "rachel"  # Default voice
            logger.info("🔊 TTS using ElevenLabs (premium quality)")
        elif self.openai_key:
            self.provider = "openai"
            self.voice = "nova"
            logger.info("🔊 TTS using OpenAI TTS")
        elif self.google_key:
            self.provider = "google"
            self.voice = "en-US-Neural2-F"
            logger.info("🔊 TTS using Google Cloud TTS")
        else:
            self.provider = "browser"
            self.voice = "default"
            logger.info("🔊 TTS using Browser Speech Synthesis")
        
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def synthesize(
        self,
        text: str,
        voice: str = None,
        speed: float = 1.0,
        output_format: str = "mp3"
    ) -> Dict[str, Any]:
        """
        Convert text to speech
        
        Args:
            text: Text to convert
            voice: Voice ID/name
            speed: Speech speed (0.5 to 2.0)
            output_format: Output format (mp3, wav)
        
        Returns:
            {
                "audio_base64": "base64 encoded audio",
                "audio_url": "url if available",
                "duration_ms": 2500,
                "format": "mp3"
            }
        """
        start_time = datetime.now()
        voice = voice or self.voice
        
        try:
            if self.provider == "elevenlabs":
                result = await self._synthesize_elevenlabs(text, voice, speed)
            elif self.provider == "openai":
                result = await self._synthesize_openai(text, voice, speed)
            elif self.provider == "google":
                result = await self._synthesize_google(text, voice, speed)
            else:
                # Browser-based
                result = {
                    "text": text,
                    "use_browser": True,
                    "voice": voice
                }
            
            duration = (datetime.now() - start_time).total_seconds() * 1000
            result["processing_time_ms"] = round(duration, 2)
            result["provider"] = self.provider
            
            logger.info(f"🔊 Synthesized {len(text)} chars in {duration:.0f}ms")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ TTS error: {e}")
            return {
                "error": str(e),
                "use_browser": True,
                "text": text
            }
    
    async def _synthesize_elevenlabs(
        self,
        text: str,
        voice: str,
        speed: float
    ) -> Dict[str, Any]:
        """Synthesize using ElevenLabs API"""
        
        session = await self._get_session()
        
        # Get voice ID
        voice_id = self.ELEVENLABS_VOICES.get(voice, voice)
        
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.elevenlabs_key
        }
        
        payload = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.5,
                "use_speaker_boost": True
            }
        }
        
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                text_err = await response.text()
                raise ValueError(f"ElevenLabs error: {response.status} - {text_err}")
            
            audio_data = await response.read()
        
        # Encode to base64
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "audio_base64": audio_base64,
            "format": "mp3",
            "voice": voice,
            "char_count": len(text)
        }
    
    async def _synthesize_openai(
        self,
        text: str,
        voice: str,
        speed: float
    ) -> Dict[str, Any]:
        """Synthesize using OpenAI TTS API"""
        
        session = await self._get_session()
        
        # Validate voice
        if voice not in self.OPENAI_VOICES:
            voice = "nova"
        
        url = "https://api.openai.com/v1/audio/speech"
        
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "tts-1-hd",  # High quality
            "input": text,
            "voice": voice,
            "speed": max(0.25, min(4.0, speed)),
            "response_format": "mp3"
        }
        
        async with session.post(url, json=payload, headers=headers) as response:
            if response.status != 200:
                text_err = await response.text()
                raise ValueError(f"OpenAI TTS error: {response.status} - {text_err}")
            
            audio_data = await response.read()
        
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            "audio_base64": audio_base64,
            "format": "mp3",
            "voice": voice,
            "char_count": len(text)
        }
    
    async def _synthesize_google(
        self,
        text: str,
        voice: str,
        speed: float
    ) -> Dict[str, Any]:
        """Synthesize using Google Cloud TTS API"""
        
        session = await self._get_session()
        
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.google_key}"
        
        payload = {
            "input": {"text": text},
            "voice": {
                "languageCode": "en-US",
                "name": voice,
                "ssmlGender": "FEMALE"
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": speed,
                "pitch": 0,
                "volumeGainDb": 0
            }
        }
        
        async with session.post(url, json=payload) as response:
            if response.status != 200:
                text_err = await response.text()
                raise ValueError(f"Google TTS error: {response.status} - {text_err}")
            
            result = await response.json()
        
        return {
            "audio_base64": result.get("audioContent", ""),
            "format": "mp3",
            "voice": voice,
            "char_count": len(text)
        }
    
    def get_available_voices(self) -> List[Dict]:
        """Get list of available voices"""
        if self.provider == "elevenlabs":
            return [
                {"id": k, "name": k.capitalize(), "provider": "elevenlabs"}
                for k in self.ELEVENLABS_VOICES.keys()
            ]
        elif self.provider == "openai":
            return [
                {"id": v, "name": v.capitalize(), "provider": "openai"}
                for v in self.OPENAI_VOICES
            ]
        else:
            return [{"id": "default", "name": "Browser Default", "provider": "browser"}]
    
    async def close(self):
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()


# Singleton
_tts_instance: Optional[TextToSpeech] = None

def get_tts() -> TextToSpeech:
    """Get or create TTS instance"""
    global _tts_instance
    if _tts_instance is None:
        _tts_instance = TextToSpeech()
    return _tts_instance