# %%
import getpass
import os

os.environ["MISTRAL_API_KEY"] = getpass.getpass()

from langchain_mistralai import ChatMistralAI

model = ChatMistralAI(model="mistral-large-latest")

# %%
from langchain_core.messages import HumanMessage

model.invoke([HumanMessage(content="Hi! I'm Bob")])

# %%
model.invoke([HumanMessage(content="What's my name?")])

# %%
from langchain_core.messages import AIMessage

model.invoke(
    [
        HumanMessage(content="Hi! I'm Bob"),
        AIMessage(content="Hello Bob! How can I assist you today?"),
        HumanMessage(content="What's my name?"),
    ]
)

# %%
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph

# Define a new graph
workflow = StateGraph(state_schema=MessagesState)


# Define the function that calls the model
def call_model(state: MessagesState):
    response = model.invoke(state["messages"])
    return {"messages": response}


# Define the (single) node in the graph
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Add memory
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# %%
config = {"configurable": {"thread_id": "abc123"}}

# %%
query = "Hi! I'm Kaen."

input_messages = [HumanMessage(query)]
output = app.invoke({"messages": input_messages}, config)
output["messages"][-1].pretty_print()  # output contains all messages in state

# %%
query = "What's my name?"

input_messages = [HumanMessage(query)]
output = app.invoke({"messages": input_messages}, config)
output["messages"][-1].pretty_print()

# %%
config = {"configurable": {"thread_id": "abc234"}}

input_messages = [HumanMessage(query)]
output = app.invoke({"messages": input_messages}, config)
output["messages"][-1].pretty_print()

# %%
config = {"configurable": {"thread_id": "abc123"}}

input_messages = [HumanMessage(query)]
output = app.invoke({"messages": input_messages}, config)
output["messages"][-1].pretty_print()

# %%
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You talk like a yoda from star wars. Answer all questions to the best of your ability.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# %%
workflow = StateGraph(state_schema=MessagesState)


def call_model(state: MessagesState):
    chain = prompt | model
    response = chain.invoke(state)
    return {"messages": response}


workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# %%
config2 = {"configurable": {"thread_id": "abc345"}}
query = "Hi! I'm Cloud."

input_messages = [HumanMessage(query)]
output = app.invoke({"messages": input_messages}, config)
output["messages"][-1].pretty_print()

# %%
query = "What is my name?"

input_messages = [HumanMessage(query)]
output = app.invoke({"messages": input_messages}, config2)
output["messages"][-1].pretty_print()

# %%
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Answer all questions to the best of your ability in {language}.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# %%
from typing import Sequence

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str


workflow = StateGraph(state_schema=State)


def call_model(state: State):
    chain = prompt | model
    response = chain.invoke(state)
    return {"messages": [response]}


workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# %%
config3 = {"configurable": {"thread_id": "abc456"}}
query = "Hi! I'm Gandalf."
language = "Hindi"

input_messages = [HumanMessage(query)]
output = app.invoke(
    {"messages": input_messages, "language": language},
    config3,
)
output["messages"][-1].pretty_print()

# %%
query = "What is my name?"

input_messages = [HumanMessage(query)]
output = app.invoke(
    {"messages": input_messages},
    config3,
)
output["messages"][-1].pretty_print()

# %%
from langchain_core.messages import SystemMessage, trim_messages

trimmer = trim_messages(
    max_tokens=65,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)


# %%

messages = [
    SystemMessage(content="you're a good assistant"),
    HumanMessage(content="hi! I'm bob"),
    AIMessage(content="hi!"),
    HumanMessage(content="I like vanilla ice cream"),
    AIMessage(content="nice"),
    HumanMessage(content="whats 2 + 2"),
    AIMessage(content="4"),
    HumanMessage(content="thanks"),
    AIMessage(content="no problem!"),
    HumanMessage(content="having fun?"),
    AIMessage(content="yes!"),
]

trimmer.invoke(messages)

# %%
workflow = StateGraph(state_schema=State)


def call_model(state: State):
    chain = prompt | model
    trimmed_messages = trimmer.invoke(state["messages"])
    response = chain.invoke(
        {"messages": trimmed_messages, "language": state["language"]}
    )
    return {"messages": [response]}


workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

# %%
config = {"configurable": {"thread_id": "abc678"}}
query = "What math problem did I ask?"
language = "English"

input_messages = messages + [HumanMessage(query)]
output = app.invoke(
    {"messages": input_messages, "language": language},
    config,
)
output["messages"][-1].pretty_print()

# %%

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from typing import List

# Step 1: Define a list of keywords to determine if a question is legal-related
legal_keywords = ["law", "legal", "court", "contract", "case", "judge", "attorney", "rights", "lawsuit", "evidence", "statute"]

def is_legal_question(query: str) -> bool:
    # Check if any legal keyword is in the query (case insensitive)
    return any(keyword in query.lower() for keyword in legal_keywords)

# Step 2: Modify the call_model function to include the filter
def call_model(state):
    # Check if the latest message is a legal question
    latest_message = state["messages"][-1].content
    if not is_legal_question(latest_message):
        # Return invalid input if the question is not related to legal assistance
        return {"messages": [AIMessage(content="Invalid input. Please ask a legal-related question.")]}
    
    # Proceed with the model if it's a legal question
    response = model.invoke(state["messages"])
    return {"messages": response}

# Step 3: Update the workflow with the modified function
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Recompile the application with the updated workflow
app = workflow.compile(checkpointer=memory)


