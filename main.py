import os
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import uuid
from dotenv import load_dotenv

# --- NEW: Import LangChain components for Groq ---
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- NEW: Load API key from .env file ---
# Make sure you have a .env file with GROQ_API_KEY="gsk_..."
load_dotenv()

# --- NEW: Initialize the Groq LLM and the generation chain ---
# We'll use LLaMA3 8B, which is very fast on Groq.
model = ChatGroq(model="llama3-8b-8192")

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that drafts professional emails."),
        ("human", "Please draft an email based on the following request: {request}")
    ]
)

# This chain will take a request, format it with the prompt, send to Groq, and parse the string output.
email_generation_chain = prompt | model | StrOutputParser()


# 1. Define the State
# --- MODIFIED: Added `user_request` to the state ---
class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        user_request: The initial instruction from the user about the email.
        email_draft: The generated email content to be approved.
        user_feedback: The 'yes' or 'no' from the user for approval.
    """
    user_request: str
    email_draft: str
    user_feedback: str

# --- Graph Nodes ---

# --- MODIFIED: This node now calls the Groq API ---
def draft_email_node(state: GraphState) -> GraphState:
    """
    Uses the Groq API to draft an email based on the user's request.
    """
    print("--- Step: Drafting Email with Groq ---")
    
    # Get the user's request from the state
    request = state["user_request"]
    
    # Invoke the LLM chain to generate the email
    email_draft = email_generation_chain.invoke({"request": request})
    
    print("Draft created and is ready for review.")
    return {"email_draft": email_draft}

def send_email_node(state: GraphState) -> GraphState:
    """
    A placeholder node that "sends" the email.
    """
    print("--- Step: Sending Email ---")
    print(f"Email Sent!\n--- CONTENT ---\n{state['email_draft']}")
    return {}

def operation_cancelled_node(state: GraphState) -> GraphState:
    """
    A node to handle the cancellation of the operation.
    """
    print("--- Step: Operation Cancelled ---")
    print("As per your request, the email will not be sent.")
    return {}

# --- Conditional Edge Logic (Unchanged) ---
def should_send_email(state: GraphState) -> str:
    """
    Determines the next step based on user feedback.
    """
    print("--- Step: Evaluating User Feedback ---")
    feedback = state.get("user_feedback", "").strip().lower()

    if feedback == "yes":
        return "send_email"
    else:
        return "cancel_operation"

# --- Build the Graph ---
workflow = StateGraph(GraphState)
workflow.add_node("draft_email", draft_email_node)
workflow.add_node("send_email", send_email_node)
workflow.add_node("cancel_operation", operation_cancelled_node)
workflow.set_entry_point("draft_email")
workflow.add_edge("send_email", END)
workflow.add_edge("cancel_operation", END)
workflow.add_conditional_edges(
    "draft_email",
    should_send_email,
    {
        "send_email": "send_email",
        "cancel_operation": "cancel_operation",
    },
)

# Create a memory checkpointer and compile the app
memory = MemorySaver()
app = workflow.compile(checkpointer=memory, interrupt_after=["draft_email"])


# --- Running the Graph with Human-in-the-Loop ---

config = {"configurable": {"thread_id": str(uuid.uuid4())}}

# --- MODIFIED: We now provide an initial user_request to start the graph ---
initial_user_prompt = "Write a brief project update email for Project Phoenix, mentioning we are on track for Q3 goals and that the new dashboard is live."

print("\n--- Starting Email Draft Process ---")
print(f"Request: {initial_user_prompt}\n")

# Start the graph. It will run the draft_email_node and then pause.
events = app.stream(
    {"user_request": initial_user_prompt},
    config=config,
    stream_mode="values"
)

# Process initial events until interruption
try:
    for event in events:
        # Print any relevant state changes for debugging
        if 'email_draft' in event:
            print("Email draft generated...")
except Exception as e:
    print(f"Error during initial execution: {e}")

# Get the current state after interruption
current_state = app.get_state(config)
email_to_approve = current_state.values.get('email_draft', '')

if not email_to_approve:
    print("Error: No email draft was generated.")
    exit(1)

print("\n\n-----------------------------")
print("--- HUMAN APPROVAL REQUIRED ---")
print("-----------------------------\n")
print("DRAFT EMAIL:\n")
print(email_to_approve)
print("\n-----------------------------")

# Ask the user for their decision
while True:
    user_input = input("Do you want to send this email? (yes/no): ").strip().lower()
    if user_input in ['yes', 'no']:
        break
    print("Please answer with 'yes' or 'no'")

# Resume the graph with the user's feedback
try:
    resume_events = app.stream(
        {"user_feedback": user_input},
        config=config,
        stream_mode="values"
    )
    
    for event in resume_events:
        if 'email_draft' in event:
            print("Processing email...")
    
    print("\n--- Graph execution finished successfully ---")
    if user_input == 'yes':
        print("Email has been sent!")
    else:
        print("Email sending was cancelled.")

except Exception as e:
    print(f"\nError during email processing: {e}")
    print("Graph execution failed")