import shutil
import os
from langchain.vectorstores import Chroma
from langchain.document_loaders import ConfluenceLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import JSONLoader

from app.dependencies import CONFLUENCE_SITE, API_TOKEN, call_get_spaces_api
from app.utils import save_to_json_file, read_from_json_file
import json

from langchain.text_splitter import CharacterTextSplitter, RecursiveCharacterTextSplitter

PERSIST_DIRECTORY = "chroma_docs/chroma/"
def get_docs(documents):
    # text_splitter = CharacterTextSplitter(
    #     separator="",
    #     chunk_size = 1000,
    #     chunk_overlap = 0,
    # )
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000,
        chunk_overlap = 200,
    )
    
    docs = text_splitter.split_documents(documents)
    return docs

def store_documents(documents):
    embeddings = OpenAIEmbeddings()
    
    print("Deleting existing vector db")
    shutil.rmtree("chroma_docs", ignore_errors=True)
    print("Deleted existing db, now creating new db")
    
    Chroma.from_documents(
        documents=documents,
        embedding=embeddings,
        persist_directory=PERSIST_DIRECTORY
    )

def load_json_data():
    loader = JSONLoader(
    file_path='./confluence_data.json',
    jq_schema='.messages[].content',
    text_content=False)

    print("Loading JSON")
    data = loader.load()
    
    
    
    print("Storing documents in vectordb")
    store_documents(data)
    print("Stored documents of space")
    print("Done")


def load_spaces_docs():    
    loader = ConfluenceLoader(
        url=CONFLUENCE_SITE,
        username="joteqwork@gmail.com",
        api_key=API_TOKEN
    )
    
    print("Get Confluence spaces")
    call_get_spaces_api()
    print("Reading Confluence spaces")
    spaces = read_from_json_file("spaces_in_confluence")

    print("Deleting existing vector db")
    shutil.rmtree("chroma_docs", ignore_errors=True)
    print("Deleted existing db, now creating new db")
    num_docs = 0
    i = 1
    for space in spaces[:-1]:
        print("Loading spaces from space", i)
        space_docs = loader.load(
        space_key=space['space_key'],
        # include_attachments=True, # PDF, PNG, JPEG/JPG, SVG, Word, Excel
        limit=50,
        # max_pages=2
        )
        print("Getting docs")
        docs = get_docs(space_docs)
        print("Number of docs for", space['space_key'], ":", len(docs))
        num_docs += len(docs)
        print("Docs:", docs)
        
        print("Storing documents in vectordb")
        store_documents(docs)
        print("Stored documents of space", i)
        i+=1
    
    print("Done\n")
    print("Total number of docs:", num_docs)
    save_to_json_file("confluence_data")

def qa(query):
    vectordb = Chroma(
        persist_directory=PERSIST_DIRECTORY,
        embedding_function=OpenAIEmbeddings()
    )
    # retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    # docs = retriever.get_relevant_documents(query)
    docs = vectordb.similarity_search(query, k=3)
    return docs
      
def print_docs(docs):
  for doc in docs:
    print(doc.page_content, end="\n---------------------------------------------------------------------------\n\n")  

# call_get_spaces_api()


def test_read_from_json_file(filename: str):
    with open(f"{filename}.json", 'r') as openfile:    
        # Reading from json file
        json_object = json.load(openfile)   
    return json_object

# spaces_in_confluence = read_from_json_file("spaces_in_confluence")

# for space in spaces_in_confluence:
#     print(space)
    
if "__main__" == __name__:
    # load_spaces_docs()
    # load_json_data()
    docs = qa("What are support vector machines?")
    print_docs(docs)
    # vectordb = Chroma(
    #     persist_directory=PERSIST_DIRECTORY,
    #     embedding_function=OpenAIEmbeddings()
    # )
    # print(vectordb._collection.count())
    