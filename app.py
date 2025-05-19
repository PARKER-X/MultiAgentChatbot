from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import uvicorn

# Import your chatbot logic
from main import run_chatbot

app = FastAPI()

# Mount static directory (your HTML/JS/CSS frontend)
static_dir = Path(__file__).parent / "static"
if not static_dir.exists():
    static_dir.mkdir()
    # You may want to add HTML/CSS/JS files manually or generate a default index.html
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Serve the main frontend page
@app.get("/")
async def serve_index():
    return FileResponse(static_dir / "index.html")


# Handle chatbot interaction
@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_input = data.get("message")
    history = data.get("history", [])

    result = run_chatbot(user_input=user_input, previous_messages=history)
    return JSONResponse({
        "response": result["response"],
        "history": result["state"]
    })


# Run the server
if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
