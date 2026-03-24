"""
🚀 AI OPERATIONS ASSISTANT - ENTERPRISE EDITION v6.0
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✨ Features:
- 💾 Redis Caching
- 🔌 WebSocket Real-time Updates
- 📊 Advanced Analytics
- 🎯 Rate Limiting
- 🔄 Server-Sent Events (SSE)
- 🎤 Voice Assistant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager
import time

sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Request, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse
import uvicorn
import io

from agents.orchestrator import get_orchestrator, process_query
from voice.voice_assistant import get_voice_assistant
from utils.logger import logger
from utils.cache_manager import get_cache_manager
from utils.websocket_manager import get_websocket_manager, MessageType
from core.message_bus import get_message_bus, Event, EventType


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📊 ADVANCED ANALYTICS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AdvancedAnalytics:
    """Real-time analytics with caching"""
    
    def __init__(self):
        self.requests_count = 0
        self.total_processing_time = 0.0
        self.requests_by_endpoint = {}
        self.errors_count = {}
        self.active_requests = 0
        self.start_time = datetime.now()
        self.request_history = []
        self.max_history = 1000
    
    def record_request(self, endpoint: str, duration: float, status: str):
        self.requests_count += 1
        self.total_processing_time += duration
        self.requests_by_endpoint[endpoint] = self.requests_by_endpoint.get(endpoint, 0) + 1
        
        if status == "error":
            self.errors_count[endpoint] = self.errors_count.get(endpoint, 0) + 1
        
        self.request_history.append({
            "endpoint": endpoint,
            "duration": duration,
            "status": status,
            "timestamp": datetime.now().isoformat()
        })
        
        if len(self.request_history) > self.max_history:
            self.request_history.pop(0)
    
    def get_stats(self):
        uptime = (datetime.now() - self.start_time).total_seconds()
        avg_time = (self.total_processing_time / self.requests_count) if self.requests_count > 0 else 0
        
        return {
            "uptime_seconds": round(uptime, 2),
            "total_requests": self.requests_count,
            "active_requests": self.active_requests,
            "avg_processing_time_ms": round(avg_time * 1000, 2),
            "requests_per_second": round(self.requests_count / uptime, 2) if uptime > 0 else 0,
            "error_rate": round((sum(self.errors_count.values()) / self.requests_count * 100), 2) if self.requests_count > 0 else 0,
            "endpoints": dict(self.requests_by_endpoint),
            "errors_by_endpoint": dict(self.errors_count)
        }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛡️ RATE LIMITER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class RateLimiter:
    """Token bucket rate limiter"""
    
    def __init__(self, rate: int = 100, per: int = 60):
        self.rate = rate
        self.per = per
        self.client_buckets = {}
    
    async def check_rate_limit(self, client_id: str) -> bool:
        current = time.time()
        
        if client_id not in self.client_buckets:
            self.client_buckets[client_id] = {
                "allowance": self.rate,
                "last_check": current
            }
        
        bucket = self.client_buckets[client_id]
        time_passed = current - bucket["last_check"]
        bucket["last_check"] = current
        bucket["allowance"] += time_passed * (self.rate / self.per)
        
        if bucket["allowance"] > self.rate:
            bucket["allowance"] = self.rate
        
        if bucket["allowance"] < 1.0:
            return False
        else:
            bucket["allowance"] -= 1.0
            return True
    
    def get_remaining(self, client_id: str) -> int:
        if client_id not in self.client_buckets:
            return self.rate
        return int(self.client_buckets[client_id]["allowance"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📋 PYDANTIC MODELS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_iterations: int = Field(default=1, ge=1, le=3)
    enable_critique: bool = Field(default=True)
    output_format: str = Field(default="standard")
    use_cache: bool = Field(default=True)


class VoiceQueryRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    enable_tts: bool = Field(default=True)
    voice: Optional[str] = Field(default="nova")
    speed: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)
    voice: Optional[str] = Field(default="nova")
    speed: Optional[float] = Field(default=1.0, ge=0.5, le=2.0)
    format: Optional[str] = Field(default="mp3")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔄 LIFESPAN HANDLER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ✅ STARTUP
    logger.info("🚀 Starting AI Operations Assistant v6.0...")
    
    # Initialize cache
    cache = await get_cache_manager()
    logger.info("✅ Cache initialized")
    
    # Initialize orchestrator
    orchestrator = get_orchestrator()
    logger.info(f"✅ Orchestrator: {len(orchestrator.agents)} agents")
    
    # Initialize voice
    try:
        voice = get_voice_assistant()
        logger.info("✅ Voice Assistant ready")
    except Exception as e:
        logger.warning(f"⚠️ Voice: {e}")
    
    # Subscribe to message bus
    async def on_query_event(event: Event):
        await ws_manager.broadcast(MessageType.QUERY_RECEIVED, event.data)
    
    message_bus.subscribe(EventType.QUERY_RECEIVED, on_query_event)
    
    logger.info("🎯 System ready!")
    
    yield
    
    # ✅ SHUTDOWN
    logger.info("🛑 Shutting down...")
    await cache.close()
    await orchestrator.shutdown()
    await ws_manager.shutdown()
    logger.info("✅ Shutdown complete")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 FASTAPI APP
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

app = FastAPI(
    title="🤖 AI Operations Assistant",
    description="Enterprise Multi-Agent AI System",
    version="6.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# Global instances
analytics = AdvancedAnalytics()
rate_limiter = RateLimiter(rate=100, per=60)
ws_manager = get_websocket_manager()
message_bus = get_message_bus()

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    """Monitor all requests"""
    start_time = time.time()
    
    # Rate limiting
    client_ip = request.client.host
    if not await rate_limiter.check_rate_limit(client_ip):
        return JSONResponse(
            status_code=429,
            content={"error": "Rate limit exceeded", "retry_after": 60}
        )
    
    analytics.active_requests += 1
    
    try:
        response = await call_next(request)
        processing_time = time.time() - start_time
        
        response.headers["X-Processing-Time"] = f"{processing_time:.3f}s"
        response.headers["X-Rate-Limit-Remaining"] = str(rate_limiter.get_remaining(client_ip))
        
        analytics.record_request(
            endpoint=request.url.path,
            duration=processing_time,
            status="success" if response.status_code < 400 else "error"
        )
        
        return response
    finally:
        analytics.active_requests -= 1


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 📡 CORE ENDPOINTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/")
async def root():
    return HTMLResponse("""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Operations Assistant v6.0</title>
        <style>
            body { font-family: system-ui; max-width: 900px; margin: 50px auto; padding: 20px; 
                   background: #0a0f1a; color: #e2e8f0; }
            h1 { color: #60a5fa; font-size: 2.5rem; }
            .status { color: #34d399; font-size: 1.2rem; margin: 20px 0; }
            .endpoint { background: #1e293b; padding: 15px; margin: 10px 0; border-radius: 8px; 
                       border-left: 4px solid #3b82f6; }
            code { background: #334155; padding: 2px 8px; border-radius: 4px; }
            a { color: #60a5fa; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>🤖 AI Operations Assistant v6.0</h1>
        <p class="status">● System Online - Enterprise Edition</p>
        
        <h2>🚀 Features</h2>
        <ul>
            <li>💾 Redis Caching - Ultra-fast responses</li>
            <li>🔌 WebSocket Support - Real-time updates</li>
            <li>📊 Advanced Analytics - Performance metrics</li>
            <li>🎯 Rate Limiting - 100 req/min</li>
            <li>🔄 SSE Streaming - Live progress</li>
            <li>🎤 Voice Assistant - Whisper + OpenAI TTS</li>
        </ul>
        
        <h2>📚 API Endpoints</h2>
        
        <div class="endpoint">
            <strong>POST /api/research</strong><br>
            Full multi-agent pipeline with caching
        </div>
        
        <div class="endpoint">
            <strong>POST /api/voice/process</strong><br>
            Complete voice pipeline with TTS
        </div>
        
        <div class="endpoint">
            <strong>GET /api/research/stream?query=...</strong><br>
            Server-Sent Events streaming
        </div>
        
        <div class="endpoint">
            <strong>WS /ws/{client_id}</strong><br>
            WebSocket real-time connection
        </div>
        
        <div class="endpoint">
            <strong>GET /api/analytics</strong><br>
            System analytics & metrics
        </div>
        
        <h2>📖 Documentation</h2>
        <p>
            <a href="/api/docs">Swagger UI</a> | 
            <a href="/api/redoc">ReDoc</a> |
            <a href="/health">Health Check</a>
        </p>
    </body>
    </html>
    """)


@app.get("/health")
async def health_check():
    cache = await get_cache_manager()
    orchestrator = get_orchestrator()
    
    cache_stats = cache.get_stats()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": (datetime.now() - analytics.start_time).total_seconds(),
        "cache": {
            "backend": cache_stats["backend"],
            "hit_rate": f"{cache_stats['hit_rate_percent']:.1f}%"
        },
        "agents": {
            name: {"healthy": agent.is_healthy(), "status": agent.status.value}
            for name, agent in orchestrator.agents.items()
        },
        "connections": {
            "websocket": len(ws_manager.connections)
        }
    }


@app.get("/api/analytics")
async def get_analytics():
    cache = await get_cache_manager()
    
    return {
        "system": analytics.get_stats(),
        "cache": cache.get_stats(),
        "websocket": ws_manager.get_stats(),
        "recent_requests": analytics.request_history[-20:]
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎯 RESEARCH ENDPOINT (WITH CACHE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/research")
async def research_endpoint(request: QueryRequest):
    """Research with intelligent caching"""
    start_time = time.time()
    cache = await get_cache_manager()
    
    # Generate cache key
    cache_key = f"{request.query}:{request.enable_critique}"
    
    # Try cache first
    if request.use_cache:
        cached_result = await cache.get("research", cache_key)
        if cached_result:
            cached_result["_cached"] = True
            cached_result["_cache_age_seconds"] = int(time.time() - cached_result.get("_cached_at", time.time()))
            logger.info("✅ Cache HIT!")
            return cached_result
    
    # Process query
    logger.info(f"📥 Research: '{request.query[:80]}...'")
    
    # Emit event
    await message_bus.emit(
        EventType.QUERY_RECEIVED,
        source="api",
        data={"query": request.query}
    )
    
    try:
        result = await process_query(
            query=request.query,
            max_iterations=request.max_iterations,
            enable_critique=request.enable_critique
        )
        
        # Add metadata
        result["_processing_time_ms"] = round((time.time() - start_time) * 1000, 2)
        result["_cached"] = False
        result["_cached_at"] = time.time()
        
        # Cache result (10 min TTL)
        if request.use_cache:
            await cache.set("research", cache_key, result, ttl=600)
        
        # Emit completion
        await message_bus.emit(
            EventType.RESPONSE_READY,
            source="api",
            data={"query": request.query, "status": "success"}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Research failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔄 SERVER-SENT EVENTS (SSE)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/api/research/stream")
async def stream_research(query: str):
    """Stream research progress via SSE"""
    
    async def event_generator():
        # Start
        yield {
            "event": "start",
            "data": {"query": query, "timestamp": datetime.now().isoformat()}
        }
        
        # Planning
        yield {"event": "planning", "data": {"status": "started"}}
        await asyncio.sleep(0.5)
        yield {"event": "planning", "data": {"status": "completed"}}
        
        # Execution
        yield {"event": "execution", "data": {"status": "started"}}
        
        # Process
        result = await process_query(query)
        
        # Complete
        yield {"event": "complete", "data": result}
    
    return EventSourceResponse(event_generator())


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔌 WEBSOCKET
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Enhanced WebSocket with real-time updates"""
    
    connection = await ws_manager.connect(websocket, client_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            message_type = data.get("type")
            
            if message_type == "ping":
                await connection.send_message(MessageType.PONG)
            
            elif message_type == "query":
                query = data.get("query", "")
                
                # Send processing status
                await connection.send_message(
                    MessageType.QUERY_RECEIVED,
                    {"query": query}
                )
                
                # Process
                result = await process_query(query)
                
                # Send result
                await connection.send_message(
                    MessageType.RESULT_READY,
                    result
                )
            
            elif message_type == "subscribe":
                topic = data.get("topic")
                ws_manager.subscribe(client_id, topic)
            
            await ws_manager.handle_message(client_id, data)
    
    except WebSocketDisconnect:
        await ws_manager.disconnect(client_id)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎤 VOICE ENDPOINTS (FIXED PATHS!)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.post("/api/voice/transcribe")
async def voice_transcribe(
    audio: UploadFile = File(...),
    language: str = "en"
):
    """🎤 Transcribe audio to text"""
    try:
        audio_data = await audio.read()
        filename = audio.filename or "audio.wav"
        audio_format = filename.split(".")[-1].lower()
        
        if audio_format not in ["wav", "mp3", "webm", "ogg", "m4a"]:
            audio_format = "wav"
        
        logger.info(f"🎤 Transcribing {len(audio_data)} bytes ({audio_format})")
        
        voice = get_voice_assistant()
        result = await voice.stt.transcribe(
            audio_data=audio_data,
            language=language,
            format=audio_format
        )
        
        logger.info(f"✅ Transcript: '{result.get('transcript', '')[:60]}...'")
        
        return {
            **result,
            "audio_format": audio_format,
            "audio_size_bytes": len(audio_data),
            "language": language,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Transcription error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/speak")
async def voice_speak(request: TTSRequest):
    """🔊 Text to speech"""
    try:
        logger.info(f"🔊 TTS: '{request.text[:50]}...'")
        
        voice = get_voice_assistant()
        result = await voice.tts.synthesize(
            text=request.text,
            speed=request.speed,
            format=request.format
        )
        
        audio_data = result.get("audio_data")
        
        if not audio_data:
            raise HTTPException(status_code=500, detail="TTS failed")
        
        logger.info(f"✅ Audio: {len(audio_data)} bytes")
        
        mime_types = {
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "opus": "audio/opus"
        }
        
        return StreamingResponse(
            io.BytesIO(audio_data),
            media_type=mime_types.get(request.format, "audio/mpeg"),
            headers={
                "Content-Disposition": f"attachment; filename=speech.{request.format}",
                "X-Voice": request.voice
            }
        )
        
    except Exception as e:
        logger.error(f"❌ TTS error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/voice/process")
async def voice_process(request: VoiceQueryRequest):
    """🎙️ Complete voice pipeline"""
    try:
        logger.info(f"🎙️ Voice: '{request.text[:60]}...'")
        
        voice = get_voice_assistant()
        
        # Process through agents
        agent_results = await process_query(request.text)
        
        # Generate response text
        response_text = voice._generate_response_text(agent_results)
        
        logger.info(f"📝 Response: {len(response_text)} chars")
        logger.info(f"   Weather: {'✅' if agent_results.get('weather') else '❌'}")
        logger.info(f"   Repos: {len(agent_results.get('repositories') or [])}")
        
        # Generate TTS
        response_audio = None
        
        if request.enable_tts:
            try:
                logger.info("🔊 Generating TTS...")
                
                tts_result = await voice.tts.synthesize(
                    text=response_text,
                    speed=request.speed,
                    format="mp3"
                )
                
                audio_data = tts_result.get("audio_data")
                
                if audio_data:
                    import base64
                    response_audio = base64.b64encode(audio_data).decode('utf-8')
                    logger.info(f"✅ Audio encoded")
                    
            except Exception as e:
                logger.warning(f"⚠️ TTS failed: {e}")
                response_audio = None
        
        return {
            "transcript": request.text,
            "response_text": response_text,
            "response_audio": response_audio,
            "results": agent_results,
            "metadata": {
                "tts_enabled": request.enable_tts,
                "tts_success": response_audio is not None,
                "voice": request.voice,
                "speed": request.speed,
                "quality_score": agent_results.get("quality", {}).get("score", 0.0),
                "weather_included": bool(agent_results.get("weather")),
                "repos_count": len(agent_results.get("repositories") or []),
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Voice processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/voice/voices")
async def get_available_voices():
    """Get available TTS voices"""
    voice = get_voice_assistant()
    
    voices_info = {
        "nova": {"gender": "female", "style": "warm", "best_for": "general"},
        "alloy": {"gender": "neutral", "style": "balanced", "best_for": "professional"},
        "echo": {"gender": "male", "style": "deep", "best_for": "narration"},
        "fable": {"gender": "male", "style": "expressive", "best_for": "storytelling"},
        "onyx": {"gender": "male", "style": "authoritative", "best_for": "news"},
        "shimmer": {"gender": "female", "style": "bright", "best_for": "cheerful"}
    }
    
    return {
        "provider": voice.tts.provider,
        "current": voice.tts.voice,
        "available": voices_info,
        "speed_range": {"min": 0.5, "max": 2.0, "default": 1.0},
        "formats": ["mp3", "wav", "opus"]
    }


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 💾 CACHE MANAGEMENT
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

@app.get("/api/cache/stats")
async def get_cache_stats():
    cache = await get_cache_manager()
    return cache.get_stats()


@app.delete("/api/cache/clear")
async def clear_cache(namespace: str = None):
    cache = await get_cache_manager()
    success = await cache.clear_all(namespace)
    return {"success": success, "namespace": namespace or "all"}


@app.delete("/api/cache/{namespace}/{key}")
async def delete_cache_key(namespace: str, key: str):
    cache = await get_cache_manager()
    success = await cache.delete(namespace, key)
    return {"success": success}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🚀 MAIN
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    
    args = parser.parse_args()
    
    print("\n" + "=" * 70)
    print("🚀 AI OPERATIONS ASSISTANT - ENTERPRISE v6.0")
    print("=" * 70)
    print(f"\n📡 Server: http://{args.host}:{args.port}")
    print(f"📚 Docs: http://localhost:{args.port}/api/docs")
    print(f"🔌 WebSocket: ws://localhost:{args.port}/ws/{{client_id}}")
    print("\n💾 Features: Redis Cache | WebSocket | SSE | Voice | Analytics")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )