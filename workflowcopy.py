from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import START, StateGraph
from langchain_core.messages import AIMessage, HumanMessage, trim_messages
from langgraph.checkpoint.memory import MemorySaver
from typing import List, TypedDict
from utils import (
    get_context_from_pinecone,
    schedule_sms_reminder,
    find_nearby_lawyers,
    geocode_location,
    get_legal_resources,
    lookup_case_by_number,  # Updated function integration
    schedule_appointment,  # Existing appointment scheduling
)
from model import model
from datetime import datetime

# Define the chatbot prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a professional legal assistant/lawyer. Answer all questions to the best of your ability in {language} using the following context: {context}. Also, if someone asks something other than legal-related questions, kindly redirect them to legal topics or respond with 'Please ask a legal-related question.'"),
    MessagesPlaceholder(variable_name="messages"),
])

# Define State as a TypedDict for compatibility
class State(TypedDict):
    messages: List[HumanMessage]
    language: str

# Trim messages to ensure token limits are respected
trimmer = trim_messages(
    max_tokens=65, 
    strategy="last", 
    token_counter=model, 
    include_system=True, 
    allow_partial=False, 
    start_on="human"
)

# Initialize StateGraph
workflow = StateGraph(state_schema=State)

# Define the model call function
async def call_model(state: dict):  # Treat state as a dictionary
    chain = prompt | model
    query = state["messages"][-1].content  # Access the latest user query
    context = await get_context_from_pinecone(query)
    trimmed_messages = trimmer.invoke(state["messages"])
    language = state.get("language", "en")

    # Check if the query is for legal case lookup by case number
    if "lookup case" in query.lower():
        try:
            case_number = query.split("case ")[1].strip()  # Extract case number
            result = lookup_case_by_number(case_number)

            # Generate a response based on the lookup result
            if isinstance(result, dict):  # Case found
                response_content = "Case Details:\n" + "\n".join([f"{key}: {value}" for key, value in result.items()])
            else:  # Case not found or error
                response_content = result

            # Return response
            return {"messages": [AIMessage(content=response_content)]}

        except Exception as e:
            print(f"Error during case lookup: {e}")
            return {"messages": [AIMessage(content="An error occurred during case lookup. Please try again later.")]}

    # Check if the query is a reminder scheduling request
    elif "schedule reminder" in query.lower():
        try:
            case_name = query.split("'")[1]
            court_date = query.split("on ")[1].strip()
            user_phone = "+12508859340"  # Replace with dynamic input if needed

            # Validate court date
            court_datetime = datetime.strptime(court_date, "%Y-%m-%d %H:%M:%S")
            if court_datetime <= datetime.now():
                return {"messages": [AIMessage(content=f"Cannot schedule reminder for '{case_name}'. The court date is too soon or in the past.")]}

            # Schedule SMS reminder
            schedule_sms_reminder(user_phone, court_date, case_name)
            return {"messages": [AIMessage(content=f"Reminder scheduled for '{case_name}' on {court_date}. An SMS reminder will be sent 24 hours in advance.")]}

        except Exception as e:
            print(f"Error during reminder scheduling: {e}")
            return {"messages": [AIMessage(content="Invalid input format. Use: 'Schedule reminder for case <Case Name> on <YYYY-MM-DD HH:MM:SS>'.")]}
    
    elif "schedule appointment" in query.lower():
        try:
            lawyer_name = query.split("with ")[1].split(" on ")[0].strip()
            appointment_time = query.split("on ")[1].strip()
            user_phone = "+12508859340"  # Replace with dynamic input if needed

            # Validate appointment time
            appointment_datetime = datetime.strptime(appointment_time, "%Y-%m-%d %H:%M:%S")
            if appointment_datetime <= datetime.now():
                return {"messages": [AIMessage(content=f"Cannot schedule appointment with {lawyer_name}. The time is in the past.")]}

            # Schedule appointment
            schedule_appointment(user_phone, lawyer_name, appointment_time)
            return {"messages": [AIMessage(content=f"Appointment scheduled with {lawyer_name} on {appointment_time}. Confirmation SMS sent.")]}

        except Exception as e:
            print(f"Error during appointment scheduling: {e}")
            return {"messages": [AIMessage(content="Invalid input format. Use: 'Schedule appointment with <Lawyer Name> on <YYYY-MM-DD HH:MM:SS>'.")]}

    
    # Check if the query is to find nearby lawyers
    elif "find nearby lawyers" in query.lower():
        try:
            if "in" in query.lower():
                location_input = query.split("in")[1].strip()
                location_coords = geocode_location(location_input)
                if not location_coords:
                    return {"messages": [AIMessage(content="Unable to resolve the provided location. Please try another location.")]}

                lawyers = find_nearby_lawyers(location=location_coords)
                if lawyers:
                    response_content = "Here are some nearby lawyers:\n" + "\n".join(
                        [f"{lawyer['name']} - {lawyer['address']} [Google Maps]({lawyer['url']})" for lawyer in lawyers]
                    )
                else:
                    response_content = "No nearby lawyers found. Please refine your search."
                return {"messages": [AIMessage(content=response_content)]}
            else:
                return {"messages": [AIMessage(content="Please specify a location. For example: 'Find nearby lawyers in Vancouver'.")]}
        except Exception as e:
            print(f"Error finding nearby lawyers: {e}")
            return {"messages": [AIMessage(content="An error occurred while finding nearby lawyers. Please try again later.")]}

    # Process other queries normally
    else:
        response = await chain.ainvoke({"messages": trimmed_messages, "language": state["language"], "context": context})
        return {"messages": [response]}

# Build workflow graph
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)

# Compile app with memory saver
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)
