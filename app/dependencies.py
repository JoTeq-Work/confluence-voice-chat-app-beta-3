import os
import time
import json
import uuid
import shutil
import logging
import requests

import chromadb
from chromadb.utils import embedding_functions

from openai import OpenAI

import speech_recognition as sr
from requests.auth import HTTPBasicAuth
from dotenv import load_dotenv, find_dotenv
from tenacity import retry, wait_random_exponential, stop_after_attempt

# import chromadb
# from chromadb.config import Settings
from app.vectordb import aws_chroma_client

from app.utils import (
    get_spaces_details, 
    save_to_json_file, 
    read_from_json_file, 
    get_space_id,
    get_docs,
    retrieve_recent_updates
    )

from app.config import get_chromadb
from langchain.document_loaders import ConfluenceLoader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GPT_MODEL = "gpt-4-1106-preview" # "gpt-4-1106-preview"

load_dotenv("app/.env")

# Declare API keys
openai_key = os.environ["OPENAI_API_KEY"]
# ATLASSIAN_API_TOKEN = os.environ["ATLASSIAN_API_TOKEN"]
TRACKMATRIX_ATLASSIAN_API_TOKEN = os.environ["TRACKMATRIX_ATLASSIAN_API_TOKEN"]
# HUGGING_FACE_API_TOKEN = os.environ["HUGGING_FACE_API_KEY"]
HUGGING_FACE_API_TOKEN = os.environ["HUGGING_FACE_API_KEY2"]
print(openai_key)
# Declare HuggingFace embedding function
# HUGGINGFACE_EF = embedding_functions.HuggingFaceEmbeddingFunction(
#     api_key=HUGGING_FACE_API_TOKEN,
#     model_name="sentence-transformers/all-MiniLM-L6-v2"
#     )

# openai_ef = embedding_functions.OpenAIEmbeddingFunction(
#                 api_key=openai_key,
#                 model_name="text-embedding-ada-002"
#             )
# default_ef = embedding_functions.DefaultEmbeddingFunction()

client = OpenAI(
    api_key=openai_key
)

USERNAME = "josephnkumah97@gmail.com"

# Confluence REST API Utilities
# CONFLUENCE_SITE = "https://joteqwork.atlassian.net"
# API_TOKEN = ATLASSIAN_API_TOKEN
# AUTH = HTTPBasicAuth(USERNAME, API_TOKEN)

# TrackMatrix Confluence REST API Utilities
CONFLUENCE_SITE = "https://trackmatrix.atlassian.net"
API_TOKEN = TRACKMATRIX_ATLASSIAN_API_TOKEN
AUTH = HTTPBasicAuth(USERNAME, API_TOKEN)
    

def text_to_speech(text):
    if not text:
        return
    speech_file_path = "app/static/chat_app/files/audio/assistant_message_output.mp3"
    try:
        print("Deleting exisiting AI speech")
        os.remove(speech_file_path)
    except Exception as e:
        print("Audio file does not exist")
    
    try:
        response = client.audio.speech.create(
        model="tts-1",
        voice="shimmer",
        input=text
        )
        print("Generating new AI Speech")
        response.stream_to_file(speech_file_path)
        print("Generated new AI Speech")
    except Exception as e:
        logger.error("Error generating speech: %s", e)


def call_create_space_api(space_name):
    """
    This function calls the Confluence Create Space REST API
    """
    url = f"{CONFLUENCE_SITE}/wiki/rest/api/space"
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
        }

    payload = json.dumps({
        "key": space_name,
        "name": space_name,
        "description": {
            "plain": {
                "value": "A new space created",
                "representation": "plain"
            }
        },
        "metadata":{}
    })

    try:
        response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers,
        auth=AUTH
        )
    except Exception as e:
        logger.error("Error with calling Confluence Create Space API: %s", e)
        
        
    results = {
            "space_id": response.json()["id"],
            "space_key": response.json()["key"],
            "space_name": response.json()["name"],
            "space_html_link": f'<a href="{response.json()["_links"]["base"] + response.json()["_links"]["webui"]}" target="_blank">{response.json()["name"]}<a/>'
            }     
    save_to_json_file(results, "created_space")   

    return json.dumps(results)


def call_get_spaces_api():
    url = f"{CONFLUENCE_SITE}/wiki/api/v2/spaces"
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=AUTH
        )
    except Exception as e:
        logger.error("Error with calling Confluence Create Space API: %s", e)
        
    spaces_res = response.json()['results']
    
    spaces_in_confluence = get_spaces_details(spaces_res)
    
    save_to_json_file(spaces_in_confluence, "spaces_in_confluence")
        
    # return json.dumps(spaces_in_confluence)


def call_create_page_api(space_name, title, content):
    url = f"{CONFLUENCE_SITE}/wiki/api/v2/pages"
    headers = {
      "Accept": "application/json",
      "Content-Type": "application/json"
    }
    
    spaces_in_confluence = read_from_json_file("spaces_in_confluence")
    space_id = get_space_id(spaces_in_confluence, space_name)
    
    payload = json.dumps({
        "spaceId": space_id,
        "status": "current",
        "title": title,
        "body": {
            "representation": "storage",
            "value": content
            }
        })
    
    try:
        response = requests.request(
        "POST",
        url,
        data=payload,
        headers=headers,
        auth=AUTH
        )  
    except Exception as e:
        logger.error("Error with calling Confluence Create Page API: %s", e)
        
    results = {
        "page_id": response.json()["id"],
        "page_title": response.json()["title"],
        "page_html_link": f'<a href="{CONFLUENCE_SITE}/wiki{response.json()["_links"]["webui"]}" target="_blank">{response.json()["title"]}</a>',
        "space_id": response.json()['spaceId']
    }
    
    save_to_json_file(results, "created_page")

    return json.dumps(results)

def update_confluence_vector_database(): 
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    start_time = time.perf_counter()
    loader = ConfluenceLoader(
        url=CONFLUENCE_SITE,
        username=USERNAME,
        api_key=API_TOKEN
    )
    
    print("Get Confluence spaces")
    call_get_spaces_api()
    print("Reading Confluence spaces")
    spaces = read_from_json_file("spaces_in_confluence")[:-1]
    
    try: 
        logger.info("Collection does not exist")
        print("Creating new `confluence_documents` collection")
        collection  = aws_chroma_client.create_collection(
            name="confluence_documents",
            embedding_function=sentence_transformer_ef,
            )
        print("New collection created")
    except Exception as e:
        logger.warning(e)
        logger.info("Collection already exists. Deleting existing `confluence_documents` collection")
        aws_chroma_client.delete_collection(name="confluence_documents") 
        print("Creating new `confluence_documents` collection")
        collection  = aws_chroma_client.create_collection(
            name="confluence_documents",
            embedding_function=sentence_transformer_ef,
            )
        print("New collection created")       
        
    conf_docs = []
    for space in spaces:
        space_docs = loader.load(
        space_key=space['space_key'],
        limit=50,
        )
        
        logger.info("Getting docs")
        docs = get_docs(space_docs)
        print("Split docs:", docs)
        print("Number of docs:", len(docs))
        print("Adding to confluence documents\n")
        # conf_docs.append(docs)
        for i, doc in enumerate(docs):  
            single_document = str(doc)
            print(f"Single Document {i+1}: {single_document}")         
        
            # docs_ids = [str(uuid.uuid4()) for _ in range(len(docs))]
            # print("Documents IDs:", docs_ids)
            print("Adding Collection", i+1)
            collection.add(
                documents=[single_document],
                ids=[str(uuid.uuid4())] 
            )
            print(f"Collection {i+1} added\n")
    
    # print("Confluence Documents:", conf_docs)
    # print("Number of documents", len(conf_docs))
    # print("All documents are in conf_docs list. Proceeding to add documents to db")
    # for i, docs in enumerate(conf_docs):
    #     space_documents= [str(docs)]
    #     print("Single Document:", space_documents, "\n")
    #     collection.add(
    #         documents=space_documents,
    #         ids=[str(uuid.uuid4())]
    #     )
    #     print("Document", i, "added")
    logger.info("Chromadb Ready!\n")
    print("Collection count:", collection.count(), "\n")
    logger.info("Retrieving Recent Updates")
    retrieve_recent_updates(CONFLUENCE_SITE, AUTH)
    logger.info("Recent Updates Retrieved\n")
    
    end_time = time.perf_counter()
    
    elasped_time = end_time - start_time
    print("Elasped_time to update the knowledge base:", elasped_time)
    
   
#----------------------------------------------------------------------------------------------------------------------------------

def ask_recent_updates():
    confluence_data = read_from_json_file("confluence_recent_updates")
    return {"confluence_data": confluence_data}

def retrieve_answer_from_confluence_knowledge_base(query):
    sentence_transformer_ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
    collection = aws_chroma_client.get_collection(
        name="confluence_documents",        
        embedding_function=sentence_transformer_ef,
        )
    
    results = collection.query(
        query_texts=[query],
        n_results=3
    )
    print("Results\n", results, "\n\n")
    # vectordb = Chroma(
    #     persist_directory=PERSIST_DIRECTORY,
    #     embedding_function=OpenAIEmbeddings()
    # )
    
    # top_k_answers = vectordb.similarity_search(query, k=3)
    
    # retrieved_answers = [top_k_answer.page_content for top_k_answer in top_k_answers]
    # response = client.chat.completions.create(
    #     model=GPT_MODEL,
    #     messages=[
    #         {
    #             "role": "user", 
    #             "content": f"Use the following pieces of context to answer the user's question about Confluence spaces. \
    #                 If you don't know the answer, just say you don't know, don't try to make up an answer. \
    #                 Keep the answer as concise as possible. \
    #                 User query: {query} \
    #                 Retrieved answers from knowledge base: {top_k_answers}"
    #         }
    #     ]        
    # )
    # retrieved_answer = response.choices[0].message.content
    retreived_answers = results["documents"]
    return {"retrieved_answers": retreived_answers}

@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def chat_completion_request(messages, functions=None, model=GPT_MODEL):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_key}",
    }
    json_data = {"model": model, "messages": messages}
    if functions is not None:
        json_data.update({"functions": functions})
        logger.info("chat completion request, will try now")
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=json_data,
        )
        logger.info(response.json())
        return response
    except Exception as e:
        logger.error("Unable to generate ChatCompletion response. Exception: %s", e)
    
class Conversation:
    def __init__(self):
        self.conversation_history = []

    def add_message(self, role, content):
        message = {"role": role, "content": content}
        self.conversation_history.append(message)
        
        
def chat_completion_with_function_execution(messages, functions=[None]):
    """This function makes a ChatCompletion API call with the option of adding functions"""
    logger.info("Started process")
    response = chat_completion_request(messages, functions)
    print("First response", response.json()["choices"][0])
    full_message = response.json()["choices"][0]
    if full_message["finish_reason"] == "function_call":
        print("Calling function")
        return call_confluence_rest_api_function(messages, full_message)
    else:
        logger.warning("Function not called")
        return response.json()


def call_confluence_rest_api_function(messages, full_message):
    """
    Function calling function which executes function calls when the model believes it is necessary.
    Currently extended by adding clauses to this if statement.
    """

    if full_message["message"]["function_call"]["name"] == "call_create_space_api":
        try:
            parsed_output = json.loads(
                full_message["message"]["function_call"]["arguments"]
            )
            print(parsed_output)
            logger.info("call_confluence_rest_api_function parsed out:", parsed_output)
            space_results = call_create_space_api(parsed_output["space_name"])
            # print("Space Results", space_results)
            created_space = read_from_json_file("created_space")
            logger.info("Created space:", created_space)
            
        except Exception as e:
            logger.error("Space error. Unable to generate ChatCompletion response: %s", e)
          
        messages.append(
            {
                "role": "function",
                "name": full_message["message"]["function_call"]["name"],
                "content": space_results,
            }
        )
        try:
            response = chat_completion_request(messages)
            return response.json()
        except Exception as e:
            logger.error("Function chat request failed: %s", e)
            
    elif full_message["message"]["function_call"]["name"] == "call_get_spaces_api":
        try:
            call_get_spaces_api()
            spaces_in_confluence = read_from_json_file("spaces_in_confluence")
            print("Spaces in Confleunce", spaces_in_confluence) 
        except Exception as e:
            logger.error(
                "Getting Spaces Error!\n",
                "Function: call_confluence_rest_api_function\n",
                "Unable to generate ChatCompletion response: %s", e
                )
        
        messages.append(
            {
                "role": "function",
                "name": full_message["message"]["function_call"]["name"],
                "content": str(spaces_in_confluence),
            }
        )        
        try:
            response = chat_completion_request(messages)
            return response.json()
        except Exception as e:
            logger.error(
                "Getting Spaces Error!\n",
                "Function: call_confluence_rest_api_function\n",
                "Function chat request failed: %s", e
                )
            
    elif full_message["message"]["function_call"]["name"] == "call_create_page_api":    
        try:
            parsed_output = json.loads(
            full_message["message"]["function_call"]["arguments"]
            )
            
            page_results = call_create_page_api(parsed_output["space_name"], parsed_output["title"], parsed_output["content"])
            print("Page Results", page_results)
            page_id = page_results['page_id']
            print("Page id", page_id)
            created_page = read_from_json_file("created_page")
            logger.info("Created Page:", created_page)
        except Exception as e:
            logger.error("Page error. Unable to generate ChatCompletion response: %s", e)
            
        messages.append(
            {
                "role": "function",
                "name": full_message["message"]["function_call"]["name"],
                "content": page_results,
            }
        )
        try:
            response = chat_completion_request(messages)
            return response.json()
        except Exception as e:
            logger.error("Function chat request failed: %s", e)
    
    elif full_message["message"]["function_call"]["name"] == "update_confluence_vector_database":
        try:
            update_confluence_vector_database()
            confluence_documents = read_from_json_file("confluence_recent_updates")
            logger.info("Confluence Documents", confluence_documents)  
        except:
            logger.error(
                "Updating Confluence Vector Database Error!\n",
                "Function: call_confluence_rest_api_function\n",
                "Unable to generate ChatCompletion response: %s", e
                )
        messages.append(
            {
                "role": "function",
                "name": full_message["message"]["function_call"]["name"],
                "content": str(confluence_documents),
            }
        )        
        try:
            response = chat_completion_request(messages)
            return response.json()
        except Exception as e:
            logger.error(
                "Updating Confluence Vector Database Error!\n",
                "Function: call_confluence_rest_api_function\n",
                "Function chat request failed: %s", e
                )
    elif full_message["message"]["function_call"]["name"] == "retrieve_answer_from_confluence_knowledge_base":
        try:
            parsed_output = json.loads(
            full_message["message"]["function_call"]["arguments"]
            )
            
            retrieved_answers = retrieve_answer_from_confluence_knowledge_base(parsed_output["query"])
            print("Retrieved answer:", retrieved_answers)
        except Exception as e:
            logger.error(
                "Retrieving answer from Confluence Knowledge Base Error!\n",
                "Function: call_confluence_rest_api_function\n",
                "Unable to generate ChatCompletion response: %s", e
                )
        messages.append(
            {
                "role": "function",
                "name": full_message["message"]["function_call"]["name"],
                "content": str(retrieved_answers),
            }
        )
        try:
            response = chat_completion_request(messages)
            return response.json()
        except Exception as e:
            logger.error(
                "Retrieve Answer from Confluence Knowledge Base Error!\n",
                "Function: call_confluence_rest_api_function\n",
                "Function chat request failed: %s", e
                )
    elif full_message["message"]["function_call"]["name"] == "ask_recent_updates":
        start_time = time.perf_counter()
        try:
            parsed_output = json.loads(
            full_message["message"]["function_call"]["arguments"]
            )
            
            recent_updates = ask_recent_updates()
            # print("Recent Updates:", recent_updates)
        except Exception as e:
            logger.error(
                "Ask Recent Updates Error!\n",
                "Function: call_confluence_rest_api_function\n",
                "Unable to generate ChatCompletion response: %s", e
                )
        messages.append(
            {
                "role": "function",
                "name": full_message["message"]["function_call"]["name"],
                "content": str(recent_updates),
            }
        )
        try:
            response = chat_completion_request(messages)
            end_time = time.perf_counter()
    
            elasped_time = end_time - start_time
            print("Elasped_time to get response for recent updates:", elasped_time)
            return response.json()
        except Exception as e:
            logger.error(
                "Ask Recent Updates Error!\n",
                "Function: call_confluence_rest_api_function\n",
                "Function chat request failed: %s", e
                )
            
    else:
        logger.warning("Function does not exist and cannot be called: %s", e)

    
    
if __name__ == "__main__":
    print("Running whole module")
