from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.apps.app import App
from google.adk.sessions.in_memory_session_service import InMemorySessionService
from google.adk.artifacts.in_memory_artifact_service import InMemoryArtifactService
from google.adk.auth.credential_service.in_memory_credential_service import InMemoryCredentialService
from google.genai import types
import asyncio
from dotenv import load_dotenv

load_dotenv()


booking_agent = LlmAgent(name="Booker", description="Handles flight and hotel bookings.")
info_agent = LlmAgent(name="Info", description="Provides general information and answers questions.")

coordinator = LlmAgent(
    name="Coordinator",
    model="gemini-2.0-flash",
    instruction="You are an assistant. Delegate booking tasks to Booker and info requests to Info.",
    description="Main coordinator.",
    sub_agents=[booking_agent, info_agent]
)

async def main():
    user_query = "I need to book a flight to Tokyo"
    print(f"User: {user_query}")
    
    # Setup services
    session_service = InMemorySessionService()
    artifact_service = InMemoryArtifactService()
    credential_service = InMemoryCredentialService()
    
    # Create App and Runner
    app = App(name="TravelApp", root_agent=coordinator)
    runner = Runner(
        app=app,
        session_service=session_service,
        artifact_service=artifact_service,
        credential_service=credential_service
    )
    
    # Create session
    session = await session_service.create_session(app_name="TravelApp", user_id="user")
    
    # Run agent
    content = types.Content(role='user', parts=[types.Part(text=user_query)])
    async for event in runner.run_async(user_id="user", session_id=session.id, new_message=content):
        if event.content and event.content.parts:
             print(f"[{event.author}]: {event.content.parts[0].text}")


if __name__ == "__main__":
    asyncio.run(main())