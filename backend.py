import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from main import attend_bot

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"message": "Attendance Bot API"}


@app.get("/attend")
async def attend(username: str, password: str):
    try:
        attend_bot(username, password)
        return {"message": "Attendance Bot API"}
    except Exception as e:
        return {"message": str(e)}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
