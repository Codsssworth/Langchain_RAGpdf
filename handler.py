import io
import os
import logging
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy import create_engine, Table, Column, MetaData, String, DateTime
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.chains.question_answering import load_qa_chain
from langchain.llms import OpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from chromadb.api.types import EmbeddingFunction

# Load environment variables
load_dotenv()

db_file = 'pdf_metadata.db'
engine = create_engine(f'sqlite:///{db_file}')
metadata = MetaData()

pdf_table = Table(
    'pdf_metadata', metadata,
    Column('file_name', String, primary_key=True),
    Column('date_uploaded', DateTime, default=datetime.utcnow)
)

metadata.create_all(engine)

logging.basicConfig(level=logging.INFO)

class ChromaEmbeddingFunction(EmbeddingFunction):
    def __init__(self):
        self.embedder = OpenAIEmbeddings()  # Using OpenAIEmbeddings without explicit api_key

    def __call__(self, texts):
        # Directly call the embedder on texts
        return self.embedder(texts)

class LangChainHandler:
    def __init__(self):
        self.knowledge_base = None
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is not set. Check your .env file.")
        
        # Set the API key for the OpenAI library globally
        os.environ["OPENAI_API_KEY"] = self.openai_api_key
        logging.info("API key loaded and set successfully.")

    def process_pdf(self, pdf_content):
        try:
            # Convert bytes content to a file-like object for PdfReader
            pdf_file = io.BytesIO(pdf_content)
            pdf_reader = PdfReader(pdf_file)
            text = "".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
            if not text:
                logging.error("No text extracted from PDF.")
                return False
            logging.info("Text extracted from PDF successfully.")

            # Split into chunks
            text_splitter = CharacterTextSplitter(separator="\n", chunk_size=1000, chunk_overlap=200)
            chunks = text_splitter.split_text(text)
            logging.info(f"Text split into {len(chunks)} chunks.")

    
            # with engine.connect() as connection:
            #     insert_stmt = pdf_table.insert().values(file_name=file_name, date_uploaded=datetime.utcnow())
            #     connection.execute(insert_stmt)
            #     logging.info(f"Stored metadata for file '{file_name}' in SQLite database.") 

            # Create embeddings and store in Chroma
            # embeddings = OpenAIEmbeddings()  # No need to pass api_key here
            # Create embeddings and store in Chroma using the custom ChromaEmbeddingFunction
            # embedding_function = ChromaEmbeddingFunction()

            embeddings_model = OpenAIEmbeddings()  # Initialize with the global API key
            embeddings = [embeddings_model.embed_documents([chunk])[0] for chunk in chunks]
            logging.info("Embeddings generated successfully.")

            self.knowledge_base = Chroma.from_texts(chunks, embeddings)
            if self.knowledge_base:
                logging.info("Knowledge base initialized successfully.")
            return True if self.knowledge_base else False
        except Exception as e:
            logging.error(f"Error in process_pdf: {e}")
            return False
        



    def store_pdf_metadata(self, file_name):
        """Stores the PDF metadata (file name and upload date) in the SQLite database."""
        with engine.connect() as connection:
            insert_stmt = pdf_table.insert().values(file_name=file_name, date_uploaded=datetime.utcnow())
            connection.execute(insert_stmt)
            logging.info(f"Stored metadata for file '{file_name}' in SQLite database.")               

    def generate_response(self, query):
        try:
            if not self.knowledge_base:
                return "Knowledge base not initialized. Please upload a PDF first."
            
            docs = self.knowledge_base.similarity_search(query)
            llm = OpenAI()  # No need to pass api_key here
            chain = load_qa_chain(llm, chain_type="stuff")
            response = chain.run(input_documents=docs, question=query)
            return response
        except Exception as e:
            logging.error(f"Error in generate_response: {e}")
            return "An error occurred while generating the response."













