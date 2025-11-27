from google.adk.agents import LlmAgent
import asyncio


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
    
    agent_event_generator = coordinator.run_async(user_query)
    async for event in agent_event_generator:
        print(event)


if __name__ == "__main__":
    asyncio.run(main())