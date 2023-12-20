import chromadb
from chromadb.config import Settings

aws_chroma_client = chromadb.HttpClient(
    host="52.221.238.213", 
    port=8000,
    )