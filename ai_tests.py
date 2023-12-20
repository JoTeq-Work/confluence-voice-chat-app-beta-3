from app.utils import read_from_json_file, save_to_json_file
from app.dependencies import client, GPT_MODEL
import json

confluence_data = read_from_json_file("confluence_documents")
input = str(confluence_data)
query = "What are the recent updates made in software space?"
response = client.chat.completions.create(
    model=GPT_MODEL,
    messages=[
        {
            "role": "user", 
            "content": f"Use the following pieces of context to answer the user's question about Confluence spaces. \
                Use the knowledge base to let the user know of the recent updates made in the page content of the current versions and the name of the person who made the update\
                If you don't know the answer, just say you don't know, don't try to make up an answer. \
                Keep the answer as concise as possible. \
                User query: {query} \
                Retrieved answers from knowledge base: {input}"
        }
    ]        
)
retrieved_answer = response.choices[0].message.content
print(retrieved_answer)