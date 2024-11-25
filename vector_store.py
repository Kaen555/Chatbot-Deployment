from pinecone import Pinecone
from langchain_pinecone import PineconeVectorStore
from config import PINECONE_API_KEY, INDEX_NAME
from model import embedding_model

# Initialize Pinecone
pinecone_client = Pinecone(api_key=PINECONE_API_KEY)
index = pinecone_client.Index(INDEX_NAME)

# Set up vector store
vector_store = PineconeVectorStore(INDEX_NAME, embedding=embedding_model.embed_query)
