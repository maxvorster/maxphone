from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import random

app = FastAPI()

# Allow all origins so frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dummy word list (replace with your full 1774 list)
word_list = ["happy", "heroic", "helpful", "heavenly"]
active_keys = {}
user_keys = {}

def assign_unique_word():
    available = list(set(word_list) - set(user_keys.keys()))
    return random.choice(available) if available else None

@app.websocket("/register")
async def register_user(websocket: WebSocket):
    await websocket.accept()
    word = assign_unique_word()
    if not word:
        await websocket.send_text("No available keys")
        return
    user_keys[word] = websocket
    active_keys[websocket] = word
    await websocket.send_text(f"Your key is: {word}")
    try:
        while True:
            data = await websocket.receive_text()
            if data.startswith("call:"):
                target = data.split(":")[1].strip()
                if target in user_keys:
                    await user_keys[target].send_text(f"Incoming call from {word}")
            else:
                try:
                    msg = eval(data)
                    if msg["type"] in ["offer", "answer", "ice"]:
                        to = msg["to"]
                        if to in user_keys:
                            await user_keys[to].send_text(data)
                except Exception as e:
                    print("Error parsing signaling message:", e)
    except WebSocketDisconnect:
        print("Client disconnected")
        del user_keys[word]
        del active_keys[websocket]
