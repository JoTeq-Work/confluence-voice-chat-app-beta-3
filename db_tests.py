import os

import chromadb
from chromadb.config import Settings
chroma = chromadb.HttpClient(host="3.87.159.18", port=8000)
print(chroma)

# print(os.getenv("AWS_REGION"))