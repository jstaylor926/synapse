"""
FastAPI REST server — exposes the engine features (like flashcards) to clients
that cannot speak MCP directly (e.g., the Even Realities G2 glasses web apps).

Run: uvicorn synapse_engine.api_server:app --host 0.0.0.0 --port 8000
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from .config import Config
from .study.flashcards import make_flashcards

app = FastAPI(title="Synapse Engine API")

# Allow CORS for the Vite dev server and phone simulator
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FlashcardResponse(BaseModel):
    front: str
    back: str
    source: str = ""

@app.get("/api/flashcards/{topic}", response_model=List[FlashcardResponse])
def get_flashcards(topic: str, n: int = 8):
    """Generate and return flashcards for a specific topic."""
    config = Config.load()
    try:
        cards = make_flashcards(config, topic, n)
        # Assuming make_flashcards returns objects with `front`, `back`, `source` properties
        # or similar fields. Adapt as necessary based on the actual study/flashcards.py implementation.
        result = []
        for c in cards:
            c_dict = c.__dict__ if hasattr(c, '__dict__') else c
            result.append(FlashcardResponse(
                front=c_dict.get('front', c_dict.get('question', 'Unknown')),
                back=c_dict.get('back', c_dict.get('answer', 'Unknown')),
                source=c_dict.get('source', '')
            ))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("synapse_engine.api_server:app", host="0.0.0.0", port=8000, reload=True)
