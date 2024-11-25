from langchain_mistralai import ChatMistralAI
from langchain_huggingface import HuggingFaceEmbeddings
from config import MISTRAL_API_KEY

# Initialize Mistral model with API key
model = ChatMistralAI(model="mistral-large-latest", api_key=MISTRAL_API_KEY)

# Initialize embedding model
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

print("Mistral API Key:", MISTRAL_API_KEY)