import os
import openai
import sys
from langchain.vectorstores import Chroma
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import DocArrayInMemorySearch
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
import uuid


sys.path.append('../..')


from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

openai.api_key  = os.environ['OPENAI_API_KEY']

llm_name = "gpt-4o-mini"

persist_directory = 'docs/chroma/'

embedding = OpenAIEmbeddings(openai_api_key= openai.api_key)
vectordb = Chroma(persist_directory=persist_directory, embedding_function=embedding)

def load_file(file, chain_type, k):
    # load documents
    loader = PyPDFLoader(file)
    documents = loader.load()
    # split documents
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    docs = text_splitter.split_documents(documents)
    # define embedding
    embeddings = OpenAIEmbeddings(openai_api_key= openai.api_key)
    # create vector database from data
    db = DocArrayInMemorySearch.from_documents(docs, embeddings)
    # define retriever
    retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": k})
    return retriever

llm = ChatOpenAI(model_name=llm_name, temperature=0,openai_api_key= openai.api_key)

def save_response(file_name, text):
    file = open(f"{file_name}_quiz_{uuid.uuid4()}.txt", "w")
    file.write(text)
    file.close()

def satgpt(uploaded_file):
    retriver = load_file(uploaded_file,"stuff", 4)
    # Build prompt
    question = ""
    template = """  

1.	The test should contain one question and four answers, one of which is correct. Mark correct answer with (CORRECT)
2.	Distractors (incorrect answers) should be plausible and logical to test the student's ability to distinguish the correct answer from the incorrect one. 
    Distractors can be based on common mistakes or misconceptions to make them more realistic and assess a genuine understanding of the topic.
3.	All options, both correct and incorrect, should be formulated clearly and unambiguously.
4.	Ideally, all answer options should be approximately the same length.
5.	Try to avoid options that can be easily ruled out.
6.	Try to place the question in real-world or scientific contexts to make the content relevant and help students connect theoretical knowledge with practical situations.
7.	There should be enough questions to cover definitions from the text and crucial points required for understanding the topic. Minimum number of question should be 20{question}.
9.	These tests can be used as examples:

The U.S. government is a member of which organization?
A United Nations
B European Union
C World Wildlife Fund
D International Red Cross

What do an absolute monarchy and an autocracy have in common?
A a single ruler
B a written constitution
C a national court system
D a single legislative house

Water is essential for life. Its special properties make water the single most important
molecule in plant life. Which of the following properties of water enable it to move
from the roots to the leaves of plants?
A Water expands as it freezes.
B Water is an excellent solvent.
C Water exhibits cohesive behavior.
D Water is able to moderate temperatures.

What was the purpose of the Palmer Raids?
A.	to find and deport illegal immigrants
B.	to break the power of the Ku Klux Klan
C.	to identify and punish suspected communists
D.	to undermine the Civil Rights movement




{context}


    """
    PROMPT = PromptTemplate(input_variables=["context", "question"],template=template,)

    satgpt_chain = RetrievalQA.from_chain_type(llm,
                                       retriever=retriver,
                                       return_source_documents=True,
                                       chain_type_kwargs={"prompt": PROMPT})
    result = satgpt_chain({"query": question})
    return result