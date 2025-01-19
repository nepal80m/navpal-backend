import json
from channels.generic.websocket import AsyncWebsocketConsumer
import os


class VoiceAssistantWebsocketConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Accept the WebSocket connection
        await self.accept()
        # self.room_name = 'self.scope["url_route"]["kwargs"]["room_name"]'
        self.room_name = "room1"
        self.room_group_name = f"file_transfer_{self.room_name}"

        # Join the group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

    async def disconnect(self, close_code):
        # Handle disconnection
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    # async def receive(self, text_data):
    #     # Handle data received from WebSocket
    #     text_data_json = json.loads(text_data)
    #     message = text_data_json.get("message", "")

    #     # Echo the message back to the WebSocket client
    #     await self.send(text_data=json.dumps({"message": message}))

    async def receive(self, text_data=None, bytes_data=None):
        # Handle received data (optional, depending on your use case)

        # Example: Send an audio file when a specific message is received
        if text_data == "send_audio_file":
            audio_file_path = (
                "/Users/anepal/workspace/navpal-backend/audio_recording.m4a"
            )

            # Ensure the file exists
            if os.path.exists(audio_file_path):
                with open(audio_file_path, "rb") as audio_file:
                    audio_data = audio_file.read()
                    await self.send(bytes_data=audio_data)
            else:
                await self.send(text_data="Error: File not found")

    async def send_audio_file(self, event):
        # Send the file to the WebSocket
        audio_file_path = event["file_path"]
        if os.path.exists(audio_file_path):
            with open(audio_file_path, "rb") as audio_file:
                audio_data = audio_file.read()
                await self.send(bytes_data=audio_data)
        else:
            await self.send(text_data="Error: File not found")
