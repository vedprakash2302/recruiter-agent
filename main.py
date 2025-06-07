import os
from typing import Dict, Any, Literal
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.types import interrupt, Command
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from rich.console import Console  
from rich.prompt import Prompt

load_dotenv()
console = Console()

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
model = ChatOpenAI(
    model="gpt-4",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.7
)

# Define the tools list for the model
tools = [get_fact, get_quote, get_joke]
model_with_tools = model.bind_tools(tools)

# Agent node - makes the decision about what to do
def agent_node(state: AgentState) -> Dict[str, Any]:
    """The main agent that decides what tool to use"""
    if not state["messages"]:
        # Initial system message
        system_msg = HumanMessage(content="""
        You are a fun and informative agent. Use the appropriate tool to share either:
        - a fun fact
        - a motivational quote
        - or a joke

        When you get a response from a tool:
        1. For facts, start with "Here's an interesting fact: " followed by the tool's output
        2. For quotes, start with "Here's a motivational quote: " followed by the tool's output
        3. For jokes, start with "Here's a joke: " followed by the tool's output

        Ask the user before sharing, and retry only if they say so. Stop after 3 retries.
        """)
        state["messages"].append(system_msg)
    
    # Get the latest user message
    latest_message = state["messages"][-1] if state["messages"] else None
    
    if latest_message and isinstance(latest_message, HumanMessage):
        # Agent decides what to do based on the user's request
        response = model_with_tools.invoke(state["messages"])
        return {"messages": [response]}
    
    return {"messages": []}

# Human approval node - implements the pre-hook functionality
def human_approval_node(state: AgentState) -> Command[Literal["execute_tool", "retry_or_stop"]]:
    """Human approval node that mimics the pre-hook functionality"""
    
    # Get the last AI message with tool calls
    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return Command(goto="execute_tool")
    
    tool_call = last_message.tool_calls[0]
    
    # Display tool information like the original pre-hook
    console.print(f"\n🔍 [bold]Preparing to run:[/bold] [cyan]{tool_call['name']}[/cyan]")
    console.print(f"📦 [bold]Arguments:[/bold] {tool_call['args']}")
    
    # Ask for user approval
    choice = interrupt({
        "question": "🤔 Do you want to continue?",
        "tool_name": tool_call['name'],
        "tool_args": tool_call['args'],
        "options": ["y", "n", "retry"],
        "default": "y"
    })
    
    if choice == "n":
        console.print("❌ [red]Operation cancelled by user.[/red]")
        return Command(
            goto="retry_or_stop",
            update={
                "user_choice": "cancelled",
                "messages": [AIMessage(content="I don't have any tool calls to make.")]
            }
        )
    
    if choice == "retry":
        current_retry = state.get("retry_count", 0) + 1
        if current_retry >= MAX_RETRIES:
            console.print("❌ [red]Maximum retries reached.[/red]")
            return Command(
                goto="retry_or_stop",
                update={
                    "retry_count": current_retry,
                    "user_choice": "max_retries",
                    "messages": [AIMessage(content="Stopped after several retries.")]
                }
            )
        
        console.print(f"🔄 [yellow]Retrying... (Attempt {current_retry} of {MAX_RETRIES})[/yellow]")
        return Command(
            goto="retry_or_stop",
            update={
                "retry_count": current_retry,
                "user_choice": "retry",
                "messages": [AIMessage(content="Let me try again!")]
            }
        )
    
    # Reset retry counter when user chooses to continue
    return Command(
        goto="execute_tool",
        update={
            "retry_count": 0,
            "user_choice": "continue"
        }
    )

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
    else:
        response = "I don't have any tools to use."
    
    return {"messages": [AIMessage(content=response)]}

# Retry or stop node
def retry_or_stop_node(state: AgentState) -> Dict[str, Any]:
    """Handle retry logic or stopping"""
    user_choice = state.get("user_choice", "")
    
    if user_choice == "retry":
        # Go back to agent to try again
        return {"messages": []}
    else:
        # Stop execution
        return {"messages": []}

# Routing function
def should_continue(state: AgentState) -> Literal["human_approval", "execute_tool", END]:
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

# Build the graph
def create_agent_graph():
    """Create the LangGraph agent with human-in-the-loop"""
    
    # Create the state graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", agent_node)
    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("execute_tool", execute_tool_node)
    workflow.add_node("retry_or_stop", retry_or_stop_node)
    
    # Add edges
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", should_continue)
    workflow.add_edge("execute_tool", END)
    workflow.add_edge("retry_or_stop", "agent")
    
    # Add memory for checkpointing (required for interrupt)
    memory = MemorySaver()
    
    # Compile the graph
    return workflow.compile(checkpointer=memory)

# Main execution function
def run_agent(user_input: str = "Share something fun!"):
    """Run the agent with human-in-the-loop functionality"""
    
    # Create the agent graph
    agent_graph = create_agent_graph()
    
    # Configuration with thread ID
    config = {"configurable": {"thread_id": "human_in_loop_demo"}}
    
    # Initial state
    initial_state = {
        "messages": [HumanMessage(content=user_input)],
        "retry_count": 0,
        "user_choice": "",
        "tool_to_execute": "",
        "tool_args": {}
    }
    
    console.print("[bold green]🚀 Starting Human-in-the-Loop Agent[/bold green]")
    console.print(f"[bold]User input:[/bold] {user_input}")
    
    try:
        # Run the graph until first interrupt
        for event in agent_graph.stream(initial_state, config, stream_mode="updates"):
            # Check for interrupt
            if "__interrupt__" in event:
                interrupt_data = event["__interrupt__"][0].value
                
                # Use Rich to prompt for user input
                console.print(f"\n{interrupt_data['question']}")
                console.print(f"Options: {interrupt_data['options']}")
                
                choice = Prompt.ask(
                    "Your choice",
                    choices=interrupt_data['options'],
                    default=interrupt_data['default']
                ).strip().lower()
                
                # Resume the graph with user's choice
                for resume_event in agent_graph.stream(
                    Command(resume=choice),
                    config,
                    stream_mode="updates"
                ):
                    # Print any new messages
                    if "execute_tool" in resume_event and "messages" in resume_event["execute_tool"]:
                        for msg in resume_event["execute_tool"]["messages"]:
                            if isinstance(msg, AIMessage):
                                console.print(f"\n[bold green]🤖 Agent:[/bold green] {msg.content}")
                    
                    elif "retry_or_stop" in resume_event:
                        if resume_event["retry_or_stop"].get("user_choice") == "retry":
                            console.print("\n[yellow]🔄 Retrying...[/yellow]")
                        elif resume_event["retry_or_stop"].get("user_choice") in ["cancelled", "max_retries"]:
                            console.print("\n[red]❌ Stopping execution.[/red]")
                            return
            
            # Print agent responses
            if "agent" in event and "messages" in event["agent"]:
                for msg in event["agent"]["messages"]:
                    if isinstance(msg, AIMessage) and msg.tool_calls:
                        console.print(f"\n[bold blue]🤖 Agent wants to use tool:[/bold blue] {msg.tool_calls[0]['name']}")
    
    except KeyboardInterrupt:
        console.print("\n[red]❌ Interrupted by user[/red]")
    except Exception as e:
        console.print(f"\n[red]❌ Error: {e}[/red]")

if __name__ == "__main__":
    # Test the agent
    run_agent("Share something fun!")
