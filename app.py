import streamlit as st
import asyncio
from langchain_core.messages import HumanMessage, AIMessage
from workflow import app
from utils import get_context_from_pinecone, summarize_document  # Import the summarize_document function

st.set_page_config(
    page_title="Legal Chatbot",
    page_icon="⚖️",  # Scales of Justice emoji for legal theme
    layout="centered",  # Center the layout
    initial_sidebar_state="collapsed",  # Collapse the sidebar by default
)

# Streamlit UI setup
st.title("Legal Chatbot")
st.write("Ask me anything related to legal issues or guidance!")

# Document upload section
st.subheader("Document Upload for Summarization")
uploaded_file = st.file_uploader("Upload a document (PDF, DOCX, or TXT):", type=["pdf", "docx", "txt"])

if uploaded_file:
    with st.spinner("Processing the document..."):
        try:
            # Call summarize_document function from utils
            summary = summarize_document(uploaded_file)
            st.success("Document processed successfully!")
            st.text_area("Document Summary", summary, height=200)
        except Exception as e:
            st.error(f"An error occurred while summarizing the document: {e}")

# Chat interface
st.subheader("Chat with the Legal Chatbot")

query = st.text_input("Your question:")
language = st.selectbox("Language", ["English", "Spanish", "French", "German"])

if st.button("Ask"):
    input_messages = [HumanMessage(query)]
    config = {"configurable": {"thread_id": "abc1"}}

    # Define a placeholder for the response that will be updated
    response_placeholder = st.empty()

    async def display_response():
        accumulated_response = ""  # Variable to accumulate chunks
        chunk_counter = 0  # Initialize a counter
        
        async for chunk, metadata in app.astream(
            {"messages": input_messages, "language": language},
            config,
            stream_mode="messages"
        ):
            if isinstance(chunk, AIMessage):
                # Append the new chunk to the accumulated response
                accumulated_response += chunk.content
                chunk_counter += 1  # Increment the counter
                # Update the placeholder text area with a unique key each time
                response_placeholder.text_area(
                    "Response",
                    accumulated_response,
                    height=200,
                    key=f"response_area_{chunk_counter}"  # Dynamic unique key
                )

    # Check for existing event loop
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:  # No existing event loop
        loop = None

    if loop and loop.is_running():
        # Run in the existing event loop
        asyncio.ensure_future(display_response())
    else:
        # Create a new event loop if none exists
        asyncio.run(display_response())
