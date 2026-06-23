from fastapi import FastAPI
from app.routes.github_webhooks import router as github_router
print("hello")
app = FastAPI()

@app.get("/")
def home():
    return {"message": "CodeSage AI is running 🚀"}

app.include_router(github_router)