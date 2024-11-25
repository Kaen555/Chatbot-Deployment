import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_AI_API")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "l6v2"  # Adjust if needed
