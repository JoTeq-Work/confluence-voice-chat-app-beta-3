import json
import logging
import requests
import speech_recognition as sr
from app.utils import save_to_json_file
from app.dependencies import CONFLUENCE_SITE, API_TOKEN, AUTH
from bs4 import BeautifulSoup
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

r = sr.Recognizer()
def speech_to_text():   
    with sr.Microphone() as source:
        print("Say something")
        audio_input = r.listen(source)
    
    try:
        text_input = r.recognize_whisper(audio_input, language="english")
        return text_input
    except sr.UnknownValueError:
        return "Whisper could not understand audio"
    except sr.RequestError as e:
        return "Could not request results from Whisper"
    
# input = speech_to_text()
# print(input)
# print(space.get_space_id())

def get_spaces_api():
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
    
    spaces_det = get_spaces_details(spaces_res)
        
    return spaces_det



def get_spaces_details(spaces_results):    
    spaces = []
    spaces_in_conf = []
    
    for space_result in spaces_results:    
        space_name = space_result['name']
        space_id = space_result['id']
        spaces.append(space_name)
        space_details = {
            "space_id": space_id,
            "space_name": space_name,
        }
        
        spaces_in_conf.append(space_details)
    spaces_in_conf.append({"spaces": spaces})
    return spaces_in_conf
    
# print(spaces)
# print(spaces_in_conf)
# spaces = get_spaces_api()
# spaces_results = spaces['results']
# print(get_spaces(spaces_results))
# spaces = get_spaces_api()

# with open("spaces_in_confluence.json", "w") as outfile:
#     json.dump(spaces, outfile)
    
# with open('spaces_in_confluence.json', 'r') as openfile:
    
    # Reading from json file
    # json_object = json.load(openfile)

def get_space_id(json_object: dict, requested_space: str):
    space_id = None
    for res in json_object[:-1]:
        if res['space_name'] == requested_space:
            space_id = res['space_id']
            return space_id
    
# space_id = get_space_id(json_object, "testtwo") 
# print(space_id)

def get_page_by_id(page_id):
    url = f"{CONFLUENCE_SITE}/wiki/api/v2/pages/{page_id}"
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
        logger.error("Error with calling Confluence Get Page by Id API: %s", e)
        
    page_res = response.json()
    
    return page_res

def get_pages_in_space(space_id):
    url = f"{CONFLUENCE_SITE}/wiki/api/v2/spaces/{space_id}/pages"
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
        logger.error("Error with calling Confluence Get Pages in Space API: %s", e)
        
    pages_res = response.json()['results']
    # pages_list = 
    return pages_res
    

def create_page_api(title, content):
    url = f"{CONFLUENCE_SITE}/wiki/api/v2/pages"
    headers = {
      "Accept": "application/json",
      "Content-Type": "application/json"
    }
    
    # spaces_in_confluence = read_from_json_file("spaces_in_confluence")
    # space_id = get_space_id(spaces_in_confluence, space_name)
    
    payload = json.dumps({
        "spaceId": 4423768,
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
        print(response)
    except Exception as e:
        logger.error("Error with calling Confluence Create Page API: %s", e)
        # print(f"Confluence Create Page API request failed with status code {response.status_code}")
        # print(f"Respnse content: {response.content}")
        
    results = {
        "page_id": response.json()["id"],
        "page_title": response.json()["title"],
        "page_html_link": f'<a href="{CONFLUENCE_SITE}/wiki{response.json()["_links"]["webui"]}" target="_blank">{response.json()["title"]}</a>',
        "space_id": response.json()['spaceId']
    }
    
    # save_to_json_file(results, "created_page")

    return json.dumps(results)

def get_content_by_id(page_id):
    url = f"{CONFLUENCE_SITE}/wiki/rest/api/content/{page_id}?expand=body.storage"
    headers = {
        "Accept": "application/json"
    }
    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=AUTH
    )
    
    return response

def test_save_to_json_file(data: dict, filename: str):
    with open(f"{filename}.json", "w") as outfile:
        # Writing to json file
        json.dump(data, outfile, indent=4, separators=(",", ": "))

# create_page_api('Test7', 
#                      'To push code to a Git repository, you can follow these steps:\\n\\n1. Initialize a Git repository in the root directory of your project:\\n\\n<ac:structured-macro ac:name=\'code\'>\\n<ac:plain-text-body>\\n<![CDATA[\\n$ git init\\n]]>\\n</ac:plain-text-body>\\n</ac:structured-macro>\\n\\n2. Add the files you want to track to the staging area:\\n\\n<ac:structured-macro ac:name=\'code\'>\\n<ac:plain-text-body>\\n<![CDATA[\\n$ git add .\\n]]>\\n</ac:plain-text-body>\\n</ac:structured-macro>\\n\\n3. Commit the changes with a descriptive commit message:\\n\\n<ac:structured-macro ac:name=\'code\'>\\n<ac:plain-text-body>\\n<![CDATA[\\n$ git commit -m \'Initial commit\'\\n]]>\\n</ac:plain-text-body>\\n</ac:structured-macro>\\n\\n4. Create a remote repository on a Git hosting service such as GitHub or Bitbucket.\\n\\n5. Link the local repository to the remote repository:\\n\\n<ac:structured-macro ac:name=\'code\'>\\n<ac:plain-text-body>\\n<![CDATA[\\n$ git remote add origin <remote_repository_url>\\n]]>\\n</ac:plain-text-body>\\n</ac:structured-macro>\\n\\n6. Push the code to the remote repository:\\n\\n<ac:structured-macro ac:name=\'code\'>\\n<ac:plain-text-body>\\n<![CDATA[\\n$ git push -u origin master\\n]]>\\n</ac:plain-text-body>\\n</ac:structured-macro>\\n\\nThese are the basic steps to push code to a Git repository. Make sure to replace <remote_repository_url> with the actual URL of your remote repository."\n')

def remove_html_tags(text):
    soup = BeautifulSoup(text, 'html.parser')
    cleaned_text = soup.get_text()
    return cleaned_text

if __name__ == "__main__":
    confluence_data = []
    # Get the spaces in confluence
    res = get_spaces_api()
    spaces = res[:-1]  
      
    # pages = get_pages_in_space(spaces[0]['space_id'])
    # print(pages['results'])
    
    # Get pages of each space
    for space in spaces:
        space_name = space['space_name']
        space_id = space['space_id']
        
        
        pages_res = get_pages_in_space(space_id)
        # print("Space Name:", space_name)
        pages = []
        page_number = 1
        for page in pages_res:   
            # confluence_data['spaces']      
            page_id = page['id'] 
            page_title = page['title']
            content_response = get_content_by_id(page_id)   
            # page_title = content_response.json()['title']   
            page_content = content_response.json()['body']['storage']['value']   
            cleaned_page_content = remove_html_tags(page_content).replace("\n", " ")             
        #     print("Page Id:", page_id)
        #     print("Page Title:", page_title)
        #     print("Page Content:", page_content, "\n")
            pages.append({
                "page_number": page_number,
                "page_id": page_id,
                "page_title": page_title,
                "page_content": cleaned_page_content,
            })
            page_number += 1
        # print("------------------------------------------------")
        confluence_data.append({"space_id": space_id, "space_name": space_name, "pages": pages})
    # print(confluence_data)
    # print(json.dumps(confluence_data, indent=4, separators=(",", ": ")))
    test_save_to_json_file(confluence_data, "confluence_data")
    
    
    # content_response = get_content_by_id(3835101)
    # page_title = content_response.json()['title']
    # page_content = content_response.json()['body']['storage']['value']
    # page = {
    #     'title': page_title,
    #     'content': page_content
    # }
    # print(page)
    # print("Page title", title)
    # print("content", content)
    # print(json.dumps(json.loads(content), sort_keys=True, indent=4, separators=(",", ": ")))
    
    
    # page = get_page_by_id(3835101)
    # print(page)
    # print(json.loads(page), sort_keys=True, indent=4, separators=(",", ": "))
