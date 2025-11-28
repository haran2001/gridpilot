from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.apps.app import App
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.genai import types
import asyncio
from dotenv import load_dotenv
from agents.orchestrator import orchestrator


# Load environment variables
load_dotenv()

import sys

async def main():
    # A realistic analyst query: checking the "health" of the market
    if len(sys.argv) > 1:
        user_query = sys.argv[1]
    else:
        user_query = f"Analyze the current status of the CAISO market. How is the weather in Los Angeles impacting the load?"
    print(f"User: {user_query}")
    
    # Setup services
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    credential_service = InMemoryCredentialService()
    
    # Create App and Runner
    app = App(name="GridPilot", root_agent=orchestrator)
    runner = Runner(
        app=app,
        session_service=session_service,
        artifact_service=artifact_service,
        credential_service=credential_service
    )
    
    # Create session
    session = await session_service.create_session(app_name="GridPilot", user_id="hari")
    
    # Run agent
    content = types.Content(role='user', parts=[types.Part(text=user_query)])
    async for event in runner.run_async(user_id="hari", session_id=session.id, new_message=content):
        if event.content and event.content.parts:
             print(f"[{event.author}]: {event.content.parts[0].text}")

if __name__ == "__main__":
    asyncio.run(main())