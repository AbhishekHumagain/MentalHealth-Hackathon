class ChatRequestNotFound(Exception):
    pass


class ChatRoomNotFound(Exception):
    pass


class ChatRequestAlreadyExists(Exception):
    pass


class NotARoomMember(Exception):
    pass


class ChatRequestAlreadyHandled(Exception):
    pass


class ChatRequestForbidden(Exception):
    pass


class DirectChatAlreadyExists(Exception):
    def __init__(self, room_id):
        self.room_id = room_id
        super().__init__("Direct chat already exists.")
