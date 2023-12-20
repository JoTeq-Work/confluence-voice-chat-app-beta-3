import json
import logging
from markupsafe import Markup

from app.utils import read_audio_file

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import WebSocket, WebSocketDisconnect

from app.confluence_functions import confluence_functions
from app.dependencies import Conversation, chat_completion_with_function_execution, text_to_speech

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"]
)

templates = Jinja2Templates(directory="app/templates")

confai_system_message = "\
    You are a friendly AI Confluence Liaison made by TrackMatriX. A helpful assistant who retrieves information from a user's Confluence \
    and answers questions asked by the user.\
    This is your job description:\
    - Create Space. \
    - Create Page. \
    - Generate HTML links. \
    - Create or update Knowledge bases of Confluence spaces.\
    - Retrieve answers to user's query from the Confluence knowledge base.\
    - Retrieve recent updates from Confluence spaces. \
    - Use your knowledge of Computer Science to explain concepts.\
    - Generate content. \
    - Generate code snippets \
    - This is the format you are to use for generating code snippets - \
    <ac:structured-macro ac:name='code'>\n\t<ac:plain-text-body>\n\t<![CDATA[{content}]]>\n\t</ac:plain-text-body>\n\t</ac:structured-macro> \
    \
    Use the phrase 'create space' as a trigger to ask the user for a space name to create a space. \
    Always Say 'TrackMatrix confirms: The new Confluence Space is now ready to use' after the space has been created. \
    DO NOT REMOVE THE HTML ANCHOR TAGS. INCLUDE THE HTML ANCHOR TAGS IN THE OUTPUT\
    After creating the space, provide the confirmation message with the HTML anchor tag:\
    USE THE <a> {space_html_link} </a> \
    \
    Use the phrase 'create page' as a trigger to create a confluence page for the user. \
    Let the user know the spaces in Confluence by providing a list of the {spaces} USING ONLY {space_name} and ask the user what space to create the page in. \
    Ask the user if you are not sure of what space the user is asking to create the page in. \
    Ask the user for the title of the page and the content of the page. \
    DO NOT assume the content of the page. \
    \
    Always Say 'TrackMatrix confirms: The new Confluence Page is now ready to use' after the page has been created. \
    DO NOT REMOVE THE HTML ANCHOR TAGS. INCLUDE THE HTML ANCHOR TAGS IN THE OUTPUT\
    After creating the page, provide the confirmation message with the HTML anchor tag:\
    USE THE <a> {page_html_link} </a>\
    \
    Use the phrase 'update knowledge base' as a trigger to create or update a user's Confluence knowledge base. \
    After updating the knowledge base, provide a confimation message to the user that the Confluence knowledge base has been updated \
    by TrackMatriX, and the user can now ask questions about the Confluence knowledge base.\
    \
    When a user asks a question, use the following pieces of context to answer the user's question about Confluence spaces. \
    If you don't know the answer, just say you don't know, don't try to make up an answer. \
    Keep the answer as concise as possible. \
    Retrieved answers from KNOWLEDGE BASE: {retrieved_answers} \
    ALWAYS retrieve information to user's query from the KNOWLEDGE BASE unless specified otherwise.\
    \
    When a user asks for recent updates, Use the following pieces of context to answer the user's question about Confluence spaces. \
    Use the knowledge base to let the user know of the recent updates made in the {page_content} of the current versions and the {name} \
    of the person who made the update. \
    If you don't know the answer, just say you don't know, don't try to make up an answer. \
    Keep the answer as concise as possible. \
    Recent updates from confluence spaces: {recent_updates}. \
"

confai_conversation = Conversation()
confai_conversation.add_message("system", confai_system_message)

def confluence_chat(transcript):
    confai_conversation.add_message("user", transcript.strip())
    chat_response = chat_completion_with_function_execution(
        confai_conversation.conversation_history, functions=confluence_functions
    )
    logger.info("Chat response:", chat_response)
    assistant_message = chat_response["choices"][0]["message"]["content"]
    assistant_message_html = Markup(assistant_message)
    text_to_speech(assistant_message)
    
    # return templates.TemplateResponse(
    #     "chat.html", 
    #     {"request": request, "assistant_message": assistant_message_html}
    #     )
    return assistant_message_html



@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        try:
            transcript = await websocket.receive_text()
            print("Sent to you:", transcript)
            print("Getting AI Response")
            assistant_message_html = confluence_chat(transcript)
            audio_data = read_audio_file("assistant_message_output")
            data_to_send = {
                "assistantMessage": assistant_message_html,
                "audioData": audio_data
                }
            # await websocket.send_text(json.dumps(data_to_send))
            await websocket.send_json(data_to_send)
        except WebSocketDisconnect:
            break