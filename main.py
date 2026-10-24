import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5-mini").strip()

app = FastAPI(title="BoardTutor API", version="1.0.0")
client = AsyncOpenAI(api_key=API_KEY) if API_KEY else None
ROOT = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")


class TutorRequest(BaseModel):
    name: str = Field(default="Student", max_length=60)
    level: Literal["Class 6", "Class 7", "Class 8", "Class 9", "Class 10", "Class 11", "Class 12", "Competitive Exam"] = "Class 8"
    topic: str = Field(min_length=1, max_length=120)
    difficulty: Literal["Beginner", "Intermediate", "Advanced"] = "Beginner"
    mode: Literal["Learn", "Practice", "Quiz", "Ask a Doubt"] = "Learn"
    message: str = Field(min_length=1, max_length=1500)


@app.get("/")
async def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.get("/health")
async def health():
    return {"status": "ok", "api_key_configured": bool(API_KEY), "model": MODEL}


@app.post("/api/tutor")
async def tutor(req: TutorRequest):
    if not client:
        raise HTTPException(
            status_code=503,
            detail="OpenAI API key is not configured. Add OPENAI_API_KEY to your .env file, then restart the server."
        )

    mode_instructions = {
        "Learn": "Teach the topic clearly in small steps. Include a worked example and finish with one short check-your-understanding question. Do not overwhelm the learner.",
        "Practice": "Generate 3 practice questions on the selected topic and difficulty. Put questions first; do not reveal answers unless the learner asks. Invite the learner to submit an answer.",
        "Quiz": "Act as a quizmaster. If the learner asks to start, provide 3 numbered questions without answers. If the learner submits answers, evaluate them one by one, explain mistakes, and state the score only when enough answers were submitted.",
        "Ask a Doubt": "Answer the learner's specific doubt step by step. For maths, show calculations and check the result when possible."
    }

    instructions = f"""
You are BoardTutor, a patient and encouraging school mathematics tutor.
Learner name: {req.name}
Level: {req.level}
Topic: {req.topic}
Difficulty: {req.difficulty}
Learning mode: {req.mode}

Teaching rules:
- Stay focused on school mathematics and the selected topic. If the request is unrelated, politely guide the learner back to mathematics.
- Adapt vocabulary and depth to the learner's level and difficulty.
- Explain reasoning, not just the final answer. Use readable equations and numbered steps.
- In answer-evaluation requests, begin with exactly one of these labels on the first line: "CORRECT", "INCORRECT", or "PARTLY CORRECT", then explain why and give a hint or correction.
- Never shame the learner; encourage another attempt when useful.
- Do not claim to have saved progress to a database. Progress is only tracked in the current browser session.
- Keep the response concise and useful.
Mode instructions: {mode_instructions[req.mode]}
"""

    try:
        response = await client.responses.create(
            model=MODEL,
            instructions=instructions,
            input=req.message,
            max_output_tokens=500,
            store=False,
        )
        answer = response.output_text.strip()
        if not answer:
            answer = "I couldn't generate a response this time. Please try again."
        return {"answer": answer, "mode": req.mode, "model": MODEL}
    except Exception as exc:
        # Avoid returning secrets or raw server internals to the browser.
        print(f"OpenAI API request failed: {type(exc).__name__}: {exc}")
        raise HTTPException(
            status_code=502,
            detail="The AI service request failed. Check your API key, API billing/limits, model name, and internet connection."
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
