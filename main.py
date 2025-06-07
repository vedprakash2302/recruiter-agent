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
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from tools.db_tools import get_database_schema, get_applicant_details, get_job_details

# Import LangChain components for Groq
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load environment variables
load_dotenv()

MAX_RETRIES = 3

# Define the agent state
class AgentState(MessagesState):
    retry_count: int = 0
    tool_to_execute: str = ""
    tool_args: Dict[str, Any] = {}
    user_choice: str = ""
    
# Tool implementations
@tool
def get_fact(fact: str) -> str:
    """Get an interesting fact"""
    return fact

@tool
def get_quote(quote: str) -> str:
    """Get a motivational quote"""
    return quote

@tool
def get_joke(joke: str) -> str:
    """Get a joke"""
    return joke

# Initialize the model
model = ChatGroq(
    model="llama3-8b-8192",
    api_key=os.getenv("GROQ_API_KEY")
)
logger = logging.getLogger(__name__)

# Define the tools list for the model
tools = [get_fact, get_quote, get_joke, get_database_schema, get_applicant_details, get_job_details]
model_with_tools = model.bind_tools(tools)

# Agent node - makes the decision about what to do
def agent_node(state: AgentState) -> Dict[str, Any]:
    """The main agent that decides what tool to use"""
    if not state["messages"]:
        # Initial system message
        system_msg = HumanMessage(content="""
        You are a helpful agent that can:
        - Share a fun fact
        - Share a motivational quote
        - Share a joke
        - Get database schema information
        - Get detailed applicant information from the database
        - Get detailed job information from the database

        When you get a response from a tool:
        1. For facts, start with "Here's an interesting fact: " followed by the tool's output
        2. For quotes, start with "Here's a motivational quote: " followed by the tool's output
        3. For jokes, start with "Here's a joke: " followed by the tool's output
        4. For database schema, present the information clearly
        5. For applicant details, present the information in a readable format
        6. For job details, present the information in a readable format

        Ask the user before executing any tool, and retry only if they say so. Stop after 3 retries.
        """)
        state["messages"].append(system_msg)
    
    # Get the latest user message
    latest_message = state["messages"][-1] if state["messages"] else None
    
    if latest_message and isinstance(latest_message, HumanMessage):
        # Agent decides what to do based on the user's request
        response = model_with_tools.invoke(state["messages"])
        return {"messages": [response]}
    
    return {"messages": []}

class EmailWorkflowManager:
    """
    Manages the email generation workflow using LangGraph and Groq.
    """
    
    def __init__(self, model_name: str = "llama3-8b-8192"):
        """Initialize the workflow manager with Groq LLM."""
        try:
            self.model = ChatGroq(model=model_name)
            logger.info(f"Initialized Groq LLM with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Groq LLM: {e}")
            raise
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a professional recruiter AI assistant specializing in writing compelling recruitment emails.

Your task is to create personalized, professional recruitment emails that:
1. Are engaging and conversational yet professional
2. Highlight relevant candidate skills and experience
3. Present the job opportunity clearly and attractively
4. Include specific benefits and role details
5. Have a clear call-to-action
6. Are personalized to the candidate's background

Always write in a warm, human tone while maintaining professionalism."""),
            ("human", "Please draft a recruitment email based on the following request: {request}")
        ])
        
        # Create the email generation chain
        self.email_generation_chain = self.prompt | self.model | StrOutputParser()
        
        # Setup the workflow graph
        self.workflow = self._build_workflow()
        self.memory = MemorySaver()
        self.app = self.workflow.compile(
            checkpointer=self.memory, 
            interrupt_after=["draft_email"]
        )
        
        logger.info("Email workflow manager initialized successfully")
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(GraphState)
        
        # Add nodes
        workflow.add_node("draft_email", self._draft_email_node)
        workflow.add_node("send_email", self._send_email_node)
        workflow.add_node("cancel_operation", self._operation_cancelled_node)
        
        # Set entry point
        workflow.set_entry_point("draft_email")
        
        # Add edges
        workflow.add_edge("send_email", END)
        workflow.add_edge("cancel_operation", END)
        workflow.add_conditional_edges(
            "draft_email",
            self._should_send_email,
            {
                "send_email": "send_email",
                "cancel_operation": "cancel_operation",
            },
        )
        
        return workflow
    
    def _draft_email_node(self, state: GraphState) -> GraphState:
        """Uses the Groq API to draft an email based on the user's request."""
        logger.info(f"Drafting email for session: {state.get('session_id', 'unknown')}")
        
        try:
            request = state["user_request"]
            email_draft = self.email_generation_chain.invoke({"request": request})
            
            logger.info("Email draft created successfully")
            return {
                "email_draft": email_draft,
                "metadata": {
                    **(state.get("metadata", {})),
                    "draft_created_at": os.environ.get("TIMESTAMP", "unknown"),
                    "draft_length": len(email_draft)
                }
            }
        except Exception as e:
            logger.error(f"Failed to draft email: {e}")
            raise
    
    def _send_email_node(self, state: GraphState) -> GraphState:
        """A node that handles the email sending process."""
        logger.info(f"Processing email send for session: {state.get('session_id', 'unknown')}")
        
        # In a real implementation, this would integrate with email service
        logger.info("Email marked for sending")
        return {
            "metadata": {
                **(state.get("metadata", {})),
                "status": "sent",
                "sent_at": os.environ.get("TIMESTAMP", "unknown")
            }
        }
    
    def _operation_cancelled_node(self, state: GraphState) -> GraphState:
        """A node to handle the cancellation of the operation."""
        logger.info(f"Operation cancelled for session: {state.get('session_id', 'unknown')}")
        return {
            "metadata": {
                **(state.get("metadata", {})),
                "status": "cancelled"
            }
        }
    
    def _should_send_email(self, state: GraphState) -> str:
        """Determines the next step based on user feedback."""
        feedback = state.get("user_feedback", "").strip().lower()
        
        if feedback == "yes":
            logger.info("User approved email for sending")
            return "send_email"
        else:
            logger.info("User declined to send email")
            return "cancel_operation"
    
    def start_workflow(self, user_request: str, session_id: str = None) -> dict:
        """
        Start a new email generation workflow.
        
        Args:
            user_request: The user's request for email generation
            session_id: Optional session ID (will generate if not provided)
            
        Returns:
            dict: Workflow configuration and initial state
        """
        if not session_id:
            session_id = str(uuid.uuid4())
        
        config = {"configurable": {"thread_id": session_id}}
        
        initial_state = {
            "user_request": user_request,
            "session_id": session_id,
            "metadata": {
                "created_at": os.environ.get("TIMESTAMP", "unknown"),
                "request_length": len(user_request)
            }
        }
        
        logger.info(f"Starting workflow for session: {session_id}")
        
        # Start the workflow
        events = list(self.app.stream(initial_state, config=config, stream_mode="values"))
        
        # Get current state after interruption
        current_state = self.app.get_state(config)
        
        return {
            "session_id": session_id,
            "config": config,
            "current_state": current_state.values,
            "email_draft": current_state.values.get('email_draft', ''),
            "status": "awaiting_approval"
        }
    
    def resume_workflow(self, session_id: str, user_feedback: str) -> dict:
        """
        Resume a workflow with user feedback.
        
        Args:
            session_id: The session ID from start_workflow
            user_feedback: User's approval decision ('yes' or 'no')
            
        Returns:
            dict: Final workflow state
        """
        config = {"configurable": {"thread_id": session_id}}
        
        logger.info(f"Resuming workflow for session: {session_id} with feedback: {user_feedback}")
        
        # Resume with user feedback
        events = list(self.app.stream(
            {"user_feedback": user_feedback}, 
            config=config, 
            stream_mode="values"
        ))
        
        # Get final state
        final_state = self.app.get_state(config)
        
        return {
            "session_id": session_id,
            "final_state": final_state.values,
            "status": "completed"
        }

# Tool execution node
def execute_tool_node(state: AgentState) -> Dict[str, Any]:
    """Execute the approved tool"""
    
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}
    
    tool_call = last_message.tool_calls[0]
    tool_name = tool_call['name']
    tool_args = tool_call['args']
    
    # Execute the appropriate tool
    if tool_name == "get_fact":
        result = get_fact.invoke(tool_args)
        response = f"Here's an interesting fact: {result}"
    elif tool_name == "get_quote":
        result = get_quote.invoke(tool_args)
        response = f"Here's a motivational quote: {result}"
    elif tool_name == "get_joke":
        result = get_joke.invoke(tool_args)
        response = f"Here's a joke: {result}"
    elif tool_name == "get_database_schema":
        result = get_database_schema.invoke(tool_args)
        response = f"Database schema:\n{result}"
    elif tool_name == "get_applicant_details":
        result = get_applicant_details.invoke(tool_args)
        response = f"Applicant information:\n{result}"
    elif tool_name == "get_job_details":
        result = get_job_details.invoke(tool_args)
        response = f"Job information:\n{result}"
    else:
        response = "I don't have any tools to use."
    
    return {"messages": [AIMessage(content=response)]}

# Utility functions for integration with FastAPI service
def create_email_workflow_manager() -> EmailWorkflowManager:
    """Create and return a configured EmailWorkflowManager instance."""
    return EmailWorkflowManager()

# Routing function
def should_continue(state: AgentState):
    """Determine the next step in the workflow"""
    
    if not state["messages"]:
        return END
    
    last_message = state["messages"][-1]
    
    # If it's an AI message with tool calls, go to human approval
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "human_approval"
    
    # If we just executed a tool or cancelled, we're done
    user_choice = state.get("user_choice", "")
    if user_choice in ["cancelled", "max_retries"]:
        return END
    
    # Check if we should continue or end
    if isinstance(last_message, AIMessage) and not last_message.tool_calls:
        return END
    
    return "execute_tool"

def demo_workflow():
    """
    Demonstration of the email workflow system.
    """
    print("\n" + "="*60)
    print("AI RECRUITER EMAIL WORKFLOW DEMO")
    print("="*60)
    
    try:
        # Initialize workflow manager
        manager = create_email_workflow_manager()
        
        # Sample request
        user_request = (
            "Write a recruitment email for a Senior Frontend Developer position at TechFlow Inc. "
            "The candidate is Sarah Chen, currently working at DataViz Solutions as a Frontend Lead. "
            "She has expertise in React, TypeScript, and modern CSS frameworks. "
            "The role offers remote work, competitive salary ($140K-160K), and leadership opportunities."
        )
        
        print(f"\nUser Request: {user_request}\n")
        
        # Start workflow
        result = manager.start_workflow(user_request)
        
        if not result['email_draft']:
            print("❌ Error: No email draft was generated.")
            return
        
        print("📧 GENERATED EMAIL DRAFT:")
        print("-" * 40)
        print(result['email_draft'])
        print("-" * 40)
        
        # Get user approval
        while True:
            user_input = input("\n🤔 Do you want to send this email? (yes/no): ").strip().lower()
            if user_input in ['yes', 'no']:
                break
            print("Please answer with 'yes' or 'no'")
        
        # Resume workflow
        final_result = manager.resume_workflow(result['session_id'], user_input)
        
        print("\n" + "="*60)
        if user_input == 'yes':
            print("✅ EMAIL APPROVED AND PROCESSED!")
        else:
            print("❌ EMAIL SENDING CANCELLED")
        print("="*60)
        
        print(f"\n📊 Session: {result['session_id']}")
        print(f"📊 Status: {final_result['status']}")
        
    except Exception as e:
        logger.error(f"Demo workflow failed: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    demo_workflow()