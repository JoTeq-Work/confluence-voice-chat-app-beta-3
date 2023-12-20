from functools import lru_cache

import chromadb

@lru_cache
def get_chromadb():
    chroma_client = chromadb.HttpClient(
        host='localhost', 
        port=8000,
        )
    
    return chroma_client

