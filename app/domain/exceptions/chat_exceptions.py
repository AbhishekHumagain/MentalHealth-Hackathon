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