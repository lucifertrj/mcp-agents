import os
import asyncio
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters

os.environ['GOOGLE_API_KEY'] = "<YOUR_API_KEY>"

async def get_agent_async():
    tools, exit_stack = await MCPToolset.from_server(
        connection_params=StdioServerParameters(
            command='npx',
            args=["-y",
                  "@openbnb/mcp-server-airbnb",
                  "--ignore-robots-txt"],
        )
    )
    print(f"Fetched {len(tools)} tools from MCP server.")
    root_agent = LlmAgent(
        model='gemini-2.0-flash',
        name='booking_assistant',
        instruction='Help user with booking listing on Airbnb',
        tools=tools,
    )
    return root_agent, exit_stack

async def async_main():
    session_service = InMemorySessionService()
    session = session_service.create_session(
        state={}, app_name='mcp_booking_app', user_id='user_airbnb'
    )

    query = "What listings are available in Gujrat- Ahmedabad for 2 people for 3 nights from 1 to 4 June 2025?"
    print(f"User Query: '{query}'")

    content = types.Content(role='user', parts=[types.Part(text=query)])
    root_agent, exit_stack = await get_agent_async()

    runner = Runner(
        app_name='mcp_booking_app',
        agent=root_agent,
        session_service=session_service,
    )

    print("Running agent...")
    events_async = runner.run_async(
        session_id=session.id, user_id=session.user_id, new_message=content
    )

    async for event in events_async:
      print(f"Event received: {event.content.parts[0].text}")

    print("Closing MCP server connection...")
    await exit_stack.aclose()
    print("Cleanup complete.")

if __name__ == '__main__':
    try:
        asyncio.run(async_main())
    except Exception as e:
        print(f"An error occurred: {e}")