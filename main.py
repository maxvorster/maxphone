from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import random
import os

app = FastAPI()

# Allow all origins so frontend can connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Path to the word list file
WORD_LIST_FILE = "word_list.txt"

# Function to load words from file
def load_words():
    if not os.path.exists(WORD_LIST_FILE):
        raise Exception(f"Word list file {WORD_LIST_FILE} not found!")
    
    with open(WORD_LIST_FILE, "r") as file:
        return [line.strip() for line in file.readlines()]

# Load the word list once when the server starts
word_list = load_words()

# Active users and keys
active_keys = {}
user_keys = {}

def assign_unique_word():
    available = list(set(word_list) - set(user_keys.keys()))
    return random.choice(available) if available else None

@app.get("/")  # Homepage route
def read_root():
    return {"message": "FastAPI backend is running!"}

@app.websocket("/register")  # WebSocket route
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
