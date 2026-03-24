"""
🎙️ VOICE ASSISTANT - FAST VERSION
Complete response with ALL data (weather + repos)
"""

import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from voice.stt import get_stt_service
from voice.tts import get_tts_service
from agents.orchestrator import get_orchestrator
from utils.logger import logger


class VoiceAssistant:
    """
    🎙️ FAST VOICE ASSISTANT
    
    Features:
    - Fast response generation
    - Complete data in response (weather + ALL repos)
    - Optimized TTS
    """
    
    def __init__(
        self,
        stt_provider: str = "whisper",
        tts_provider: str = "openai",
        tts_voice: str = "nova"
    ):
        self.stt = get_stt_service(provider=stt_provider)
        self.tts = get_tts_service(provider=tts_provider, voice=tts_voice)
        self.orchestrator = get_orchestrator()
        self.conversation_history = []
        
        logger.info("🎙️ Voice Assistant initialized (FAST MODE)")
    
    async def process_voice_query(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
        enable_tts: bool = True
    ) -> Dict[str, Any]:
        """Fast voice processing"""
        start_time = datetime.now()
        
        try:
            # STT
            logger.info("🎤 Transcribing...")
            stt_result = await self.stt.transcribe(audio_data, "en", audio_format)
            transcript = stt_result.get("transcript", "")
            
            if not transcript:
                return {"error": "Failed to transcribe", "transcript": ""}
            
            logger.info(f"✅ Transcript: '{transcript}'")
            
            # Process
            logger.info("🤖 Processing...")
            agent_results = await self.orchestrator.process_query(transcript)
            
            # Generate response
            response_text = self._generate_response_text(agent_results)
            logger.info(f"📝 Response: '{response_text[:80]}...'")
            
            # TTS
            response_audio = None
            if enable_tts and response_text:
                logger.info("🔊 Generating audio...")
                tts_result = await self.tts.synthesize(response_text)
                response_audio = tts_result.get("audio_data")
            
            total_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return {
                "transcript": transcript,
                "response_text": response_text,
                "response_audio": response_audio,
                "results": agent_results,
                "metadata": {"total_time_ms": round(total_time, 2)}
            }
            
        except Exception as e:
            logger.error(f"❌ Voice error: {e}")
            return {
                "error": str(e),
                "transcript": "",
                "response_text": "Sorry, an error occurred."
            }
    
    def _generate_response_text(self, results: Dict) -> str:
        """
        🎯 COMPLETE RESPONSE with ALL data
        
        Includes: Weather details + ALL repositories
        """
        if results.get("status") == "error":
            return f"Sorry, I encountered an error: {results.get('error', 'Unknown error')}"
        
        parts = []
        
        # ========== WEATHER (COMPLETE) ==========
        weather = results.get("weather")
        if weather:
            city = weather.get("city", "Unknown")
            temp = weather.get("temperature", "N/A")
            desc = weather.get("description", "")
            humidity = weather.get("humidity", "")
            wind = weather.get("wind_speed", "")
            
            weather_text = f"The weather in {city} is {temp}"
            if desc:
                weather_text += f" with {desc}"
            weather_text += "."
            
            details = []
            if humidity and humidity != "N/A":
                details.append(f"humidity is {humidity}")
            if wind and wind != "N/A":
                details.append(f"wind speed is {wind}")
            
            if details:
                weather_text += f" The {' and '.join(details)}."
            
            parts.append(weather_text)
        
        # ========== REPOSITORIES (ALL OF THEM) ==========
        repos = results.get("repositories", [])
        if repos:
            count = len(repos)
            parts.append(f"I found {count} GitHub repositories.")
            
            # List ALL repos (up to 10 for voice)
            repo_list = []
            for i, repo in enumerate(repos[:10], 1):
                name = repo.get("name", "Unknown")
                stars = repo.get("stars", "0")
                language = repo.get("language", "")
                
                repo_text = f"Number {i}: {name} with {stars} stars"
                if language and language != "Unknown":
                    repo_text += f", written in {language}"
                
                repo_list.append(repo_text)
            
            parts.append(". ".join(repo_list) + ".")
            
            # Add descriptions for top 3
            if repos[0].get("description"):
                top_desc = repos[0].get("description", "")[:100]
                parts.append(f"The top repository {repos[0].get('name')} is described as: {top_desc}.")
        
        # ========== WEB RESULTS ==========
        web = results.get("web_results", [])
        if web:
            # Find AI answer
            for item in web:
                if item.get("is_answer"):
                    parts.append(f"Here's what I found: {item.get('snippet', '')[:200]}")
                    break
        
        # ========== QUALITY ==========
        quality = results.get("quality", {})
        grade = quality.get("grade", "")
        if grade in ["A+", "A"]:
            parts.append("The data quality is excellent.")
        elif grade == "B":
            parts.append("The data quality is good.")
        
        # ========== BUILD RESPONSE ==========
        if parts:
            return " ".join(parts)
        
        # Fallback
        summary = results.get("summary", "")
        if summary:
            return summary
        
        return "I processed your request but couldn't find specific results."
    
    def _generate_spoken_response(self, query: str, results: Dict) -> str:
        """Alias for compatibility"""
        return self._generate_response_text(results)
    
    def get_conversation_history(self, limit: int = 10) -> list:
        return self.conversation_history[-limit:]
    
    def clear_history(self):
        self.conversation_history = []
    
    async def close(self):
        logger.info("🎙️ Voice Assistant closing...")


# ============ SINGLETON ============
_voice_instance: Optional[VoiceAssistant] = None

def get_voice_assistant(
    stt_provider: str = "whisper",
    tts_provider: str = "openai",
    tts_voice: str = "nova"
) -> VoiceAssistant:
    global _voice_instance
    if _voice_instance is None:
        _voice_instance = VoiceAssistant(stt_provider, tts_provider, tts_voice)
    return _voice_instance