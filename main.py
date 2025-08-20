from typing_extensions import TypedDict
from typing import Annotated
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
from langgraph.graph import START,END,StateGraph
from dotenv import load_dotenv
from langgraph.checkpoint.mongodb import MongoDBSaver

load_dotenv()

# Create a graph
class State(TypedDict):
    messages: Annotated[list,add_messages]
llm = init_chat_model(model_provider='openai',model='gpt-5')
DB_URI = "mongodb://localhost:27017/"

def chat_model(state:State):
    response = llm.invoke(state['messages'])
    return {"messages":[response]}

def graph_with_checkpointer(graph_builder,checkpointer):
    return graph_builder.compile(checkpointer=checkpointer)

graph_builder = StateGraph(State)

graph_builder.add_node("chat_model",chat_model)
graph_builder.add_edge(START,"chat_model")
graph_builder.add_edge("chat_model",END)

graph = graph_builder.compile()

def main():
    config = {
        "configurable": {
            "thread_id": "1"
        }
    }
    with MongoDBSaver.from_conn_string(DB_URI) as mongo_checkpointer:
        query = input("> ")
        graph = graph_with_checkpointer(graph_builder=graph_builder,checkpointer=mongo_checkpointer)
        # res = graph.invoke({
        #     "messages":[{"role":"user","content":query}]
        # },config=config)
        for event in graph.stream({
            "messages":[{"role":"user","content":query}]
        }):
            print(event)

if __name__ == "__main__":
    main()
