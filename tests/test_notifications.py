import pytest

from services.notification_service.services.websocket_manager import NotificationService


class DummyWebSocket:
    def __init__(self):
        self.messages = []

    async def send_json(self, message):
        self.messages.append(message)


@pytest.mark.asyncio
async def test_handle_message_rejects_invalid_json():
    service = NotificationService()
    socket = DummyWebSocket()
    service.manager.active_connections[1] = socket

    await service.handle_message(1, "not-json")

    assert socket.messages[-1]["type"] == "error"


@pytest.mark.asyncio
async def test_notify_soldier_supports_notification_type():
    service = NotificationService()
    socket = DummyWebSocket()
    service.manager.active_connections[1] = socket

    await service.notify_soldier(1, "Alert", "Body", "warning")

    assert socket.messages[-1]["notification_type"] == "warning"
