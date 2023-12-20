from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.routers import chat_app
from fastapi.testclient import TestClient
from starlette.staticfiles import StaticFiles

# from app.config import get_chromadb
from functools import lru_cache
# from app.dependencies import start_chromadb

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     print("Starting Chromadb")    
#     start_chromadb()
#     print("Chromadb started")
#     yield


# chroma_client = get_chromadb() 

# @lru_cache
# def get_chromadb():
#     chroma_client = chromadb.HttpClient(
#         host='localhost', 
#         port=8000,
#         )
    
#     return chroma_client

# chroma_client = get_chromadb()

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

  
@app.get("/")
async def home():
    return {"Home": "Welcome to the Confluence Voice AI Chat App"}


    
def test_home():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
    
    
app.include_router(chat_app.router)