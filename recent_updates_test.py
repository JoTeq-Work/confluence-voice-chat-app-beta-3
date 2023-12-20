from app.dependencies import call_get_spaces_api
from app.utils import read_from_json_file, save_to_json_file
from test import get_pages_in_space, remove_html_tags
from app.dependencies import CONFLUENCE_SITE, AUTH
import requests

def retrieve_versions(page_id):
    url = f"{CONFLUENCE_SITE}/wiki/rest/api/content/{page_id}/version?expand=content.body.view"
    headers = {
    "Accept": "application/json"
    }
    response = requests.request(
        "GET",
        url,
        headers=headers,
        auth=AUTH
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

def retrieve_recent_updates():   
    print("Getting Spaces in Confluence") 
    call_get_spaces_api()
    print("Reading Confluence spaces")
    spaces_results = read_from_json_file("spaces_in_confluence")[:-1]
    
    spaces = {}
    
    # Get pages of each space
    for space in spaces_results:    
        
        pages = {}
        pages_results = get_pages_in_space(space['space_id'])
        for page in pages_results:
            page_id = page['id']
            page_versions = retrieve_versions(page_id)
            if page_versions:
                pages[page['title']] = page_versions
        
        if pages:   
            spaces[space['space_name']] = {
                'id': space['space_id'],
                'key': space['space_key'],
                'name': space['space_name'],     
                'pages': pages,    
                } 
    print("Storing Confluence Documents")
    save_to_json_file(spaces, "confluence_documents")
    print("Stored Confluence Documents")
        
              
        
    
    # print(pages)
    
    # pages = []
    # for space in spaces.values():
    #     space_id = space['id']
    #     pages_results = get_pages_in_space(space_id)
    #     print(len(pages_results))
        
        
        
    #     pages_res = get_pages_in_space(space_id)
    #     pages.append(pages_res[0])
    # return pages
    
retrieve_recent_updates()

# versions = retrieve_versions(3835101)
# print(versions)
# print("Page 1:", pages[0]['id'], "\n")
# print("Page 2:", pages[1]['id'])