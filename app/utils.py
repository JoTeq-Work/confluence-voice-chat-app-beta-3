import json
import base64
import logging
import requests
from bs4 import BeautifulSoup

from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter, CharacterTextSplitter

# from app.dependencies import CONFLUENCE_SITE, AUTH

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_docs(documents):
    doc_splitter = CharacterTextSplitter(
        separator="",
        chunk_size = 1000,
        chunk_overlap = 0,
    )
    
    docs = doc_splitter.split_documents(documents)
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap  = 200,
        length_function = len,
        is_separator_regex = False,
    )
    
    conf_docs = []
    for doc in docs:
        page_content = doc.page_content
        texts = text_splitter.create_documents([page_content])
        for text in texts:
            conf_docs.append(text)
        
    # conf_docs = {}
    # for doc in docs:
    #     conf_docs
    # docs_str = [str([doc]) for doc in docs]
    return conf_docs

# PERSIST_DIRECTORY = "app/chroma_docs/chroma/"
# def store_documents(documents):
#     embeddings = OpenAIEmbeddings()
    
#     Chroma.from_documents(
#         documents=documents,
#         embedding=embeddings,
#         persist_directory=PERSIST_DIRECTORY
#     )
 
 
def get_spaces_details(spaces_results):    
    spaces = []
    spaces_in_conf = []
    
    for space_result in spaces_results:    
        space_id = space_result['id']
        space_key = space_result['key']
        space_name = space_result['name']        
        spaces.append(space_name)
        space_details = {
            "space_id": space_id,
            "space_key": space_key,
            "space_name": space_name,
        }
        
        spaces_in_conf.append(space_details)
    spaces_in_conf.append({"spaces": spaces})
    
    return spaces_in_conf




def save_to_json_file(data: dict, filename: str):
    with open(f"app/static/chat_app/files/json_data_store/{filename}.json", "w") as outfile:
        # Writing to json file
        json.dump(data, outfile, indent=4, separators=(",", ": "))
        

def read_from_json_file(filename: str):
    with open(f"app/static/chat_app/files/json_data_store/{filename}.json", 'r') as openfile:    
        # Reading from json file
        json_object = json.load(openfile)    
    
    return json_object

def get_space_id(json_object: dict, requested_space: str):
    space_id = None
    for res in json_object[:-1]:
        if res['space_name'] == requested_space:
            space_id = res['space_id']
            return space_id
        
# -------------------------------------------------------------------------------------------------------------------------------------

def remove_html_tags(text):
    soup = BeautifulSoup(text, 'html.parser')
    cleaned_text = soup.get_text()
    return cleaned_text

def get_pages_in_space(space_id, confluence_site, auth):
    url = f"{confluence_site}/wiki/api/v2/spaces/{space_id}/pages"
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = requests.request(
            "GET",
            url,
            headers=headers,
            auth=auth,
        )
    except Exception as e:
        logger.error("Error with calling Confluence Get Pages in Space API: %s", e)
        
    pages_res = response.json()['results']
    # pages_list = 
    return pages_res

def retrieve_versions(page_id, confluence_site, auth):
    url = f"{confluence_site}/wiki/rest/api/content/{page_id}/version?expand=content.body.view"
    headers = {
    "Accept": "application/json"
    }
    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=auth,
    )
    results = response.json()['results']
    
    if len(results) <= 1 :
        return False 
    
    cleaned_previous_page_content = remove_html_tags(results[1]['content']['body']['view']['value'])
    previous_version = {
        "name": results[1]['by']['displayName'],
        "date": results[1]['friendlyWhen'],
        "title": results[1]['content']['title'],
        "page_content": cleaned_previous_page_content.replace('\n', '').replace('\"', ''),
    }  
    
    cleaned_current_page_content = remove_html_tags(results[0]['content']['body']['view']['value'])
    current_version = {
        "name": results[0]['by']['displayName'],
        "date": results[0]['friendlyWhen'],
        "title": results[0]['content']['title'],
        "page_content": cleaned_current_page_content.replace('\n', '').replace('\"', ''),
    }      
    
    versions = {
        "previous_version": previous_version,
        "current_version": current_version
    }
    
    return versions

def check_date(page_versions):
    date = page_versions['previous_version']['date']
    if ('yesterday' in date) or ('today' in date) or ("hours" in date) or ("hour" in date) or \
        ("minutes" in date) or ("minute" in date) or ("seconds" in date) or ("second" in date):
            return True
        
def retrieve_recent_updates(confluence_site, auth): 
    spaces_results = read_from_json_file("spaces_in_confluence")[:-1]     
    spaces = {}
    
    # Get pages of each space
    for space in spaces_results:    
        
        pages = {}
        pages_results = get_pages_in_space(space['space_id'], confluence_site, auth)
        for page in pages_results:
            page_id = page['id']
            page_versions = retrieve_versions(page_id, confluence_site, auth)
            if page_versions and check_date(page_versions):
                pages[page['title']] = page_versions
        
        if pages: 
                spaces[space['space_name']] = {
                    'id': space['space_id'],
                    'key': space['space_key'],
                    'name': space['space_name'],     
                    'pages': pages,    
                    } 
    print("Storing Confluence Documents in JSON Store")
    save_to_json_file(spaces, "confluence_recent_updates")
    print("Stored Confluence Documents in JSON Store")


def read_audio_file(file_name):
    with open(f"app/static/chat_app/files/audio/{file_name}.mp3", "rb") as audio_file:
        audio_data = base64.b64encode(audio_file.read()).decode("utf-8")
    return audio_data


if __name__ == "__main__":
    print()