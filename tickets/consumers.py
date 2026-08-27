import json
from channels.generic.websocket import AsyncWebsocketConsumer

class BoardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.project_slug = self.scope['url_route']['kwargs']['project_slug']
        self.room_group_name = f"board_{self.project_slug}"

        # Reject unauthenticated connections
        if self.scope["user"].is_anonymous:
            await self.close(code=4001)
            return

        # Join the project board group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Event handler for broadcasted board updates
    async def board_update(self, event):
        await self.send(text_data=json.dumps({
            "type": "board.updated",
            "data": event["payload"]
        }))