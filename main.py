"""
AI Recruiter Email Workflow
Enhanced version with modular design and FastAPI integration support
"""

import os
import uuid
import logging
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
import uuid
from dotenv import load_dotenv

# --- Import LangChain components for Groq ---
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# --- Load API key from .env file ---
load_dotenv()

# --- Initialize the Groq LLM ---
model = ChatGroq(model="llama3-8b-8192")

# --- Chain 1: For initial email drafting ---
drafting_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant that drafts professional emails. Your tone should be clear and concise."),
        ("human", "Please draft an email based on the following request: {request}")
    ]
)
email_drafting_chain = drafting_prompt | model | StrOutputParser()

# --- Chain 2: For enhancing an existing email draft ---
enhancement_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are an expert email editor. Your task is to take an existing email draft and improve it. Make it more professional, clear, and impactful, while keeping the original meaning intact."),
        ("human", "Please enhance the following email draft:\n\n---\n\n{email_draft}")
    ]
)
email_enhancement_chain = enhancement_prompt | model | StrOutputParser()


# 1. Define the State
class GraphState(TypedDict):
    """
    Represents the state of our graph.
    """
    user_request: str
    email_draft: str
    enhancement_feedback: str # User's decision to enhance or not
    user_feedback: str      # User's final decision to send or not

# --- Graph Nodes ---

def draft_email_node(state: GraphState) -> GraphState:
    """Uses the Groq API to draft an initial email."""
    print("--- Step: Drafting Initial Email with Groq ---")
    request = state["user_request"]
    email_draft = email_drafting_chain.invoke({"request": request})
    print("Initial draft created.")
    return {"email_draft": email_draft}

def enhance_email_node(state: GraphState) -> GraphState:
    """Uses the Groq API to enhance the existing email draft."""
    print("--- Step: Enhancing Email with Groq ---")
    current_draft = state["email_draft"]
    enhanced_draft = email_enhancement_chain.invoke({"email_draft": current_draft})
    print("Email has been enhanced.")
    return {"email_draft": enhanced_draft}

def final_approval_gate(state: GraphState) -> GraphState:
    """A placeholder node to act as a gate before the final user approval."""
    print("--- Email is ready for FINAL approval ---")
    return {}

def send_email_node(state: GraphState) -> GraphState:
    """A placeholder node that 'sends' the email."""
    print("--- Step: Sending Email ---")
    print(f"Email Sent!\n--- FINAL CONTENT ---\n{state['email_draft']}")
    return {}

def operation_cancelled_node(state: GraphState) -> GraphState:
    """A node to handle the cancellation of the operation."""
    print("--- Step: Operation Cancelled ---")
    print("As per your request, the email will not be sent.")
    return {}

# --- Conditional Edge Logic ---

def should_enhance_email(state: GraphState) -> str:
    """Decides whether to enhance the email or proceed to final approval."""
    print("--- Evaluating: Enhance email? ---")
    if state.get("enhancement_feedback", "").strip().lower() == "yes":
        return "enhance_email"
    else:
        return "final_approval_gate"

def should_send_email(state: GraphState) -> str:
    """Determines the final step based on user approval."""
    print("--- Evaluating: Send email? ---")
    if state.get("user_feedback", "").strip().lower() == "yes":
        return "send_email"
    else:
        return "cancel_operation"

# --- Build the Graph ---
workflow = StateGraph(GraphState)
workflow.add_node("draft_email", draft_email_node)
workflow.add_node("enhance_email", enhance_email_node)
workflow.add_node("final_approval_gate", final_approval_gate)
workflow.add_node("send_email", send_email_node)
workflow.add_node("cancel_operation", operation_cancelled_node)
workflow.set_entry_point("draft_email")
workflow.add_edge("enhance_email", "final_approval_gate")
workflow.add_edge("send_email", END)
workflow.add_edge("cancel_operation", END)
workflow.add_conditional_edges(
    "draft_email",
    should_enhance_email,
    {"enhance_email": "enhance_email", "final_approval_gate": "final_approval_gate"}
)
workflow.add_conditional_edges(
    "final_approval_gate",
    should_send_email,
    {"send_email": "send_email", "cancel_operation": "cancel_operation"}
)

memory = MemorySaver()
app = workflow.compile(
    checkpointer=memory,
    interrupt_after=["draft_email", "final_approval_gate"]
)

# --- Running the Graph with the Two-Stage Human-in-the-Loop ---

config = {"configurable": {"thread_id": str(uuid.uuid4())}}
initial_user_prompt = "Write a brief project update for Project Phoenix, mention we are on track for Q3 goals and the new dashboard is live."

print(f"\n--- Starting Email Generation Process for: '{initial_user_prompt}' ---\n")

# --- STAGE 1: DRAFT and ask for ENHANCEMENT ---
app.invoke({"user_request": initial_user_prompt}, config=config)
current_state = app.get_state(config)
initial_draft = current_state.values.get('email_draft', '')

print("\n\n---------------------------------")
print("--- STAGE 1: ENHANCEMENT REVIEW ---")
print("---------------------------------\n")
print("INITIAL DRAFT:\n")
print(initial_draft)
print("\n---------------------------------")

while True:
    enhancement_input = input("Do you want to enhance this draft? (yes/no): ").strip().lower()
    if enhancement_input in ['yes', 'no']:
        break
    print("Please answer with 'yes' or 'no'.")

# ### FIXED: Explicitly update state, then invoke with None to resume ###
# This ensures the graph continues from its paused state correctly.
print("\n...Resuming graph...")
app.update_state(config, {"enhancement_feedback": enhancement_input})
app.invoke(None, config=config)


# --- STAGE 2: Get FINAL DRAFT and ask for APPROVAL to SEND ---
final_state = app.get_state(config)
final_draft = final_state.values.get('email_draft', '')

print("\n\n-----------------------------")
print("--- STAGE 2: FINAL APPROVAL ---")
print("-----------------------------\n")
print("FINAL EMAIL DRAFT:\n")
print(final_draft)
print("\n-----------------------------")

while True:
    send_input = input("Do you approve sending this email? (yes/no): ").strip().lower()
    if send_input in ['yes', 'no']:
        break
    print("Please answer with 'yes' or 'no'.")

# ### FIXED: Apply the same robust pattern for the final step ###
print("\n...Resuming graph for final action...")
app.update_state(config, {"user_feedback": send_input})
app.invoke(None, config=config)

print("\n--- Graph execution finished. ---")