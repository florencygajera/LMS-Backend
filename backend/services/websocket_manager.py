"""
WebSocket Notification Service
Agniveer Sentinel - Real-time Notifications
"""

import asyncio
from json import JSONDecodeError
from typing import Dict, Set, List
from fastapi import WebSocket
from datetime import datetime, timezone
import json


class ConnectionManager:
    """Manage WebSocket connections"""
    
    def __init__(self):
        # Active connections: user_id -> WebSocket
        self.active_connections: Dict[int, WebSocket] = {}
        # Rooms: room_name -> set of user_ids
        self.rooms: Dict[str, Set[int]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept and register a new WebSocket connection"""
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: int):
        """Remove a WebSocket connection"""
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        
        # Remove from all rooms
        for room_name in list(self.rooms.keys()):
            if user_id in self.rooms[room_name]:
                self.rooms[room_name].remove(user_id)
    
    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to a specific user"""
        if user_id in self.active_connections:
            try:
                websocket = self.active_connections[user_id]
                await websocket.send_json(message)
            except Exception as e:
                print(f"Error sending message to user {user_id}: {e}")
                self.disconnect(user_id)
    
    async def broadcast(self, message: dict, room: str = None):
        """Broadcast message to all connected users or a room"""
        targets = set()
        
        if room and room in self.rooms:
            targets = self.rooms[room]
        else:
            targets = set(self.active_connections.keys())
        
        for user_id in targets:
            await self.send_personal_message(message, user_id)
    
    def join_room(self, user_id: int, room_name: str):
        """Add user to a room"""
        if room_name not in self.rooms:
            self.rooms[room_name] = set()
        self.rooms[room_name].add(user_id)
    
    def leave_room(self, user_id: int, room_name: str):
        """Remove user from a room"""
        if room_name in self.rooms:
            self.rooms[room_name].discard(user_id)
    
    async def send_sos_alert(
        self,
        alert_message: str,
        alert_type: str,
        battalion_id: int = None
    ):
        """Send SOS alert to all connected users"""
        message = {
            "type": "sos_alert",
            "alert_type": alert_type,
            "message": alert_message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "battalion_id": battalion_id
        }
        
        # Broadcast to all
        await self.broadcast(message)
    
    async def send_notification(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: str = "info"
    ):
        """Send notification to a user"""
        message = {
            "type": "notification",
            "notification_type": notification_type,
            "title": title,
            "body": body,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.send_personal_message(message, user_id)
    
    async def send_training_schedule(
        self,
        user_id: int,
        schedule: dict
    ):
        """Send daily training schedule to a user"""
        message = {
            "type": "training_schedule",
            "schedule": schedule,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.send_personal_message(message, user_id)
    
    async def send_weather_alert(
        self,
        user_id: int,
        weather_data: dict
    ):
        """Send weather alert to a user"""
        message = {
            "type": "weather_alert",
            "weather": weather_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        await self.send_personal_message(message, user_id)


class NotificationService:
    """Notification service with WebSocket support"""
    
    def __init__(self):
        self.manager = ConnectionManager()
    
    async def handle_websocket_connection(self, websocket: WebSocket, user_id: int):
        """Handle WebSocket connection lifecycle"""
        await self.manager.connect(websocket, user_id)
        
        # Join user's personal room
        self.manager.join_room(user_id, f"user_{user_id}")
        
        # Join battalion room if applicable (would be fetched from DB)
        # self.manager.join_room(user_id, f"battalion_{battalion_id}")
        
        try:
            while True:
                # Keep connection alive and handle incoming messages
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await self.handle_message(user_id, message)
                
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            self.manager.disconnect(user_id)
    
    async def handle_message(self, user_id: int, message: dict | str):
        """Handle incoming WebSocket messages"""
        if isinstance(message, str):
            try:
                message = json.loads(message)
            except JSONDecodeError:
                await self.manager.send_personal_message(
                    {"type": "error", "detail": "Invalid JSON payload."},
                    user_id,
                )
                return

        if not isinstance(message, dict):
            await self.manager.send_personal_message(
                {"type": "error", "detail": "Invalid message format."},
                user_id,
            )
            return

        msg_type = message.get("type")
        
        if msg_type == "ping":
            await self.manager.send_personal_message({"type": "pong"}, user_id)
        
        elif msg_type == "join_room":
            room = message.get("room")
            if room:
                self.manager.join_room(user_id, room)
        
        elif msg_type == "leave_room":
            room = message.get("room")
            if room:
                self.manager.leave_room(user_id, room)
    
    async def trigger_sos_alert(
        self,
        alert_message: str,
        alert_type: str = "emergency",
        battalion_id: int = None
    ):
        """Trigger SOS alert"""
        await self.manager.send_sos_alert(alert_message, alert_type, battalion_id)
    
    async def notify_soldier(
        self,
        user_id: int,
        title: str,
        body: str,
        notification_type: str = "info",
    ):
        """Send notification to soldier"""
        await self.manager.send_notification(user_id, title, body, notification_type)
    
    async def broadcast_schedule(self, schedule: dict):
        """Broadcast training schedule update"""
        message = {
            "type": "training_schedule",
            "schedule": schedule,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.manager.broadcast(message)
    
    async def notify_weather_change(
        self,
        battalion_id: int,
        weather_data: dict
    ):
        """Notify battalion of weather change"""
        message = {
            "type": "weather_alert",
            "weather": weather_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # Send to battalion room
        room = f"battalion_{battalion_id}"
        await self.manager.broadcast(message, room)


# Singleton instance
notification_service = NotificationService()



