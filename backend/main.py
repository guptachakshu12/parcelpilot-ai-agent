
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent.graph import create_parcelpilot_agent


app = FastAPI(
    title="ParcelPilot AI Support Agent",
    version="1.0.0",
)


# ---------------------------------------------------------
# CORS - allow local frontend + Vercel frontend
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",

        # Production Vercel frontend
        # Production Vercel frontend
       "https://parcelpilot-ai-agent.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# Create agent once when API starts
# ---------------------------------------------------------

agent = create_parcelpilot_agent()


# ---------------------------------------------------------
# Request model
# ---------------------------------------------------------

class ChatRequest(BaseModel):
    message: str


# ---------------------------------------------------------
# Basic endpoints
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "message": "ParcelPilot AI Support Agent API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# ---------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------

@app.post("/chat")
def chat(request: ChatRequest):

    try:
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": request.message,
                    }
                ]
            }
        )

        messages = result.get("messages", [])

        if not messages:
            return {
                "answer": "The agent did not return a response.",
                "activity": [],
            }

        # ---------------------------------------------
        # Extract final answer
        # ---------------------------------------------

        final_message = messages[-1]
        content = final_message.content

        if isinstance(content, list):

            text_parts = []

            for block in content:

                if isinstance(block, dict):

                    if block.get("type") == "text":

                        text = block.get("text", "")

                        if text:
                            text_parts.append(text)

            content = "\n".join(text_parts)

        elif not isinstance(content, str):

            content = str(content)


        # ---------------------------------------------
        # Build activity list
        # ---------------------------------------------

        activity = []

        for message in messages:

            if (
                hasattr(message, "tool_calls")
                and message.tool_calls
            ):

                for tool_call in message.tool_calls:

                    tool_name = tool_call.get(
                        "name",
                        "unknown_tool"
                    )

                    activity.append({
                        "type": "tool_call",
                        "tool": tool_name,
                        "status": "completed",
                    })


        # ---------------------------------------------
        # Return successful response
        # ---------------------------------------------

        return {
            "answer": content,
            "activity": activity,
        }


    except Exception as e:

        return {
            "answer": "The agent encountered an error.",
            "error": str(e),
            "activity": [],
        }