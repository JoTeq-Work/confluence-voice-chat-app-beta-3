confluence_functions = [
    {
        "name": "call_create_space_api",
        "description": "Use this function to create a space in Confluence",
        "parameters": {
            "type": "object",
            "properties": {
                "space_name": {
                    "type": "string",
                    "description": "User response is the name of the new space being created.",
                }
            }
        },
        "required": ["space_name"]
    },
    {
        "name": "call_get_spaces_api",
        "description": "Use this function to get the spaces from Confluence",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "result": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    {
        "name": "call_create_page_api",
        "description": "Use this function to create a page in a user's Confluence space",
        "parameters": {
            "type": "object",
            "properties": {
                "space_name": {
                  "type": "string",
                  "description": "User response is the name of the space." ,
                },
                "title": {
                  "type": "string",
                  "description": "User response is the title of the page." ,
                },
                "content": {
                    "type": "string",
                    "description": "User response is the content of the page.",
                }
            }
        },
        "required": ["space_name", "title", "content"]
    },
    {
        "name": "update_confluence_vector_database",
        "description": "Use this function to create a vector database of spaces in Confluence",
        "parameters": {
            "type": "object",
            "properties": {}
        },
    },
    {
        "name": "retrieve_answer_from_confluence_knowledge_base",
        "description": "Use this function to retrieve answers to user's query from the Confluence knowledge base",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "User query in string. Responses should be information from the confluence knowledge base." ,
                }
            }
        },
        "required": ["query"]
    },
    {
        "name": "ask_recent_updates",
        "description": "Use this function to get information about the current_version of confluence spaces",
        "parameters": {
            "type": "object",
            "properties": {}
        },
    },
]