#!/usr/bin/env python3
"""
Test WebSocket streaming endpoint
"""
import asyncio
import websockets
import json
import requests

# Get auth token
response = requests.post(
    "http://localhost:8000/api/auth/login",
    json={"email": "kb@test.com", "password": "testpass123"}
)
token = response.json()["access_token"]
print(f"✅ Got token: {token[:30]}...")

# Get agent ID
response = requests.get(
    "http://localhost:8000/api/custom-agents",
    headers={"Authorization": f"Bearer {token}"}
)
agent_id = response.json()[0]["id"]
print(f"✅ Using agent: {agent_id}")

async def test_websocket():
    uri = f"ws://localhost:8000/ws/agent-chat/{agent_id}?token={token}"
    
    async with websockets.connect(uri) as websocket:
        # Wait for connection message
        msg = await websocket.recv()
        print(f"📡 Connected: {msg}")
        
        # Send test message
        test_msg = {
            "type": "message",
            "content": "Hello! Can you tell me a short joke?"
        }
        await websocket.send(json.dumps(test_msg))
        print(f"📤 Sent: {test_msg['content']}")
        
        # Receive streaming response
        print("\n📥 Streaming response:")
        full_response = ""
        async for message in websocket:
            data = json.loads(message)
            
            if data["type"] == "start":
                print("🚀 Starting...")
            elif data["type"] == "stream":
                content = data["content"]
                print(content, end="", flush=True)
                full_response += content
            elif data["type"] == "end":
                print("\n✅ Complete!")
                break
            elif data["type"] == "error":
                print(f"\n❌ Error: {data['error']}")
                break

if __name__ == "__main__":
    asyncio.run(test_websocket())
