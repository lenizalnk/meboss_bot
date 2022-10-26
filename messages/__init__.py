from messages.messages import msgs

def get_message_text(msg_name, *args, **kwargs):
    return msgs.get(msg_name, "UNKNOWN_MESSAGE").format(*args, **kwargs)