from fastapi import FastAPI
from app.routes import github_webhooks

app = FastAPI(title="CodeSage AI")

# 👇 THIS IS THE MOST IMPORTANT LINE
app.include_router(github_webhooks.router)


@app.get("/")
def home():
    return {"message": "CodeSage AI Backend Running 🚀"}