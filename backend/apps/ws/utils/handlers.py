from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .variables import back_channel_name


def send_message(header, ch_info=None, data=None):        # Converts msg to bytes and sends it to ws micro connection
    
    # print('TX MSG ID:', header.get_msg_id())
    msg = header.pacself()

    if data:
        msg += data.pacself()
    
    try:
        ch_layer = get_channel_layer()
        payload = {
            'type': 'micro.command',
            'bytes_data': msg
        }
        if ch_info:
            ch_name = ch_info.name
        else:
            ch_name = back_channel_name
        async_to_sync(ch_layer.send)(
            ch_name,
            payload
        )
    
    except ch_info.DoesNotExist:
        print("Micro not connected")