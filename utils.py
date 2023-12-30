import openai
import streamlit as st

from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.prompts import PromptTemplate
from langchain.prompts.chat import SystemMessagePromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory


@st.cache_resource
def load_chain(openai_api_key):
    """
    The `load_chain()` function initializes and configures a conversational retrieval chain for
    answering user questions.
    :return: The `load_chain()` function returns a ConversationalRetrievalChain object.
    """
    openai.api_key = openai_api_key
    
    # Load OpenAI embedding model
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    
    # Load OpenAI chat model
    model = "gpt-4"
    temperature = 0.3
    llm = ChatOpenAI(openai_api_key=openai_api_key,temperature=temperature, model=model)
    
    # Load our local Chroma index as a retriever
    persist_directory="db"
    vector_store = Chroma(persist_directory=persist_directory, embedding_function=embeddings)
    search_kwargs = {"k": 3}
    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    
    # Create memory 'chat_history' 
    memory = ConversationBufferWindowMemory(k=5, memory_key="chat_history")

    # Create the Conversational Chain
    chain = ConversationalRetrievalChain.from_llm(llm=llm, 
                                                  retriever=retriever, 
                                                  memory=memory, 
                                                  get_chat_history=lambda h : h,
                                                  verbose=True)

    # Create system prompt
    template = """
    You are a tutor for a high school Computer Science Principles course.
    You are given the following extracted parts of a long document and a question. Provide a conversational answer.
    If you don't know the answer, just say that you don't know, don't try to make up an answer.
    All answers must be understandable for a high school student.
    All answers should be succinct and less than 1000 words.
    Encourage the learner to reflect on their personal experience by using follow-up questions.
    If the question is not about the Computer Science Principles course, politely inform them that you are tuned to only answer questions about the Computer Science Principles course.
    Only present follow-up questions if the question are related to the Computer Science Principles course. 
    Do not provide follow-up questions for topics not related to to the Computer Science Principles course.
    
    Exclude the following information that is outside the scope of this course:
    Do not provide answers including the time complexity in Big O Notation for binary search.
    Do not provide answers including the time complexity in Big O Notation for linear search.
    Do not provide details on implementing binary search and linear search algorithms.
    Specific range limitations for real numbers.
    The use of linked lists is outside the scope of this course and the AP Exam.
    Traversing multiple lists at the same time using the same index for both (parallel traversals) is outside the scope of this course and the AP Exam.
    Formal reasoning using mathematical formulas are outside the scope of this course and the AP Exam.
    Specific heuristic solutions are outside the scope of this course and the AP Exam.
    Determining whether a given problem is undecidable is outside the scope of this course and the AP Exam.
    Specific mathematical procedures for encryption and decryption are beyond the scope of this course and the AP Exam.

    {context}
    Question: {question}
    Helpful Answer:"""

    # Add system prompt to chain
    QA_CHAIN_PROMPT = PromptTemplate(input_variables=["context", "question"],template=template)
    chain.combine_docs_chain.llm_chain.prompt.messages[0] = SystemMessagePromptTemplate(prompt=QA_CHAIN_PROMPT)

    return chain