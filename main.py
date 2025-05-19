# Imports
from dotenv import load_dotenv
from typing import Annotated, Literal
from langgraph.graph import StateGraph, START,END
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from pydantic import BaseModel,Field
from typing_extensions import TypedDict
# from api import GOOGLE_API_KEY

load_dotenv()

# LLM
llm = init_chat_model(
    "google_genai:gemini-2.0-flash"
)

class MessageClassifier(BaseModel):
    message_type: Literal["emotional","logical"] = Field(
        ...,
        description="Classify if the message requires an emotional (therapist) or logical response"
    )


class State(TypedDict):
    messages: Annotated[list,add_messages]
    message_type: str|None


def classify_message(state:State):
    last_message=state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier)
    result = classifier_llm.invoke([
        {'role':"system",
         "content":"""Classify the user message as either:
         -'emotional': if it asks for emotional support, therapy, deals with feelings or personal problems
         -'logical': if it asks for facts, information, logical analysis or practical solutions
         """
         },
         {"role":"user","content":last_message.content}
    ])
    return {"message_type":result.message_type}


def router(state:State):
    message_type = state.get("message_type","logical")
    if message_type == "emotional":
        return {"next":"therapist"}
    return {"next":"logical"}


def therapist_agent(state:State):
    last_message = state['messages'][-1]

    messages = [
        {"role": "system",
         "content": """You are a compassionate therapist. Focus on the emotional aspects of the user's message.
                        Show empathy, validate their feelings, and help them process their emotions.
                        Ask thoughtful questions to help them explore their feelings more deeply.
                        Avoid giving logical solutions unless explicitly asked."""
         },
        {
            "role": "user",
            "content": last_message.content
        }
    ]

    reply = llm.invoke(messages)
    return {"messages": [{"role": "assistant", "content": reply.content}]}

def logical_agent(state: State):
    last_message = state["messages"][-1]

    messages = [
        {"role": "system",
         "content": """You are a purely logical assistant. Focus only on facts and information.
            Provide clear, concise answers based on logic and evidence and reasoning think step by step.
            Do not address emotions or provide emotional support.
            Be direct and straightforward in your responses."""
         },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    reply = llm.invoke(messages)
    return {"messages": [{"role": "assistant", "content": reply.content}]}


graph_builder = StateGraph(State)
graph_builder.add_node("classifier",classify_message)
graph_builder.add_node("router",router)
graph_builder.add_node("therapist",therapist_agent)
graph_builder.add_node("logical",logical_agent)

graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier","router")

graph_builder.add_conditional_edges(
    "router",
    lambda state: state.get("next"),
    {"therapist":"therapist","logical":"logical"}
)

graph_builder.add_edge("therapist",END)
graph_builder.add_edge("logical",END)

graph = graph_builder.compile()


# def run_chatbot():
#     state = {"messages": [], "message_type": None}

#     while True:
#         user_input = input("Message: ")
#         if user_input == "exit":
#             print("Bye")
#             break

#         state["messages"] = state.get("messages", []) + [
#             {"role": "user", "content": user_input}
#         ]

#         state = graph.invoke(state)

#         if state.get("messages") and len(state["messages"]) > 0:
#             last_message = state["messages"][-1]
#             print(f"Assistant: {last_message.content}")

from langchain.schema import HumanMessage, AIMessage

def format_message(msg):
    """Convert LangChain message objects to plain JSON-serializable dicts."""
    if isinstance(msg, HumanMessage):
        return {"role": "user", "content": msg.content}
    elif isinstance(msg, AIMessage):
        return {"role": "assistant", "content": msg.content}
    elif isinstance(msg, dict):
        return msg  # already plain
    return {"role": "unknown", "content": str(msg)}

def run_chatbot(user_input: str, previous_messages=None) -> dict:
    if previous_messages is None:
        previous_messages = []

    # Convert previous messages back into LangChain message objects
    messages = []
    for m in previous_messages:
        if m["role"] == "user":
            messages.append(HumanMessage(content=m["content"]))
        elif m["role"] == "assistant":
            messages.append(AIMessage(content=m["content"]))
        else:
            continue  # Skip unknown roles

    # Add the new user message
    messages.append(HumanMessage(content=user_input))

    # Build state for LangGraph
    state = {
        "messages": messages,
        "message_type": None
    }

    # Run the graph
    state = graph.invoke(state)

    # Format all messages for the frontend (convert to plain dicts)
    plain_history = [format_message(m) for m in state["messages"]]

    # Find the assistant's response
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage):
            return {
                "response": msg.content,
                "state": plain_history
            }

    return {
        "response": "Sorry, no response generated.",
        "state": plain_history
    }


# if __name__ == "__main__":
#     run_chatbot()