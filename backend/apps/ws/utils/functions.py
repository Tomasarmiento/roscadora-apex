from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from apps.ws.utils import variables as ws_vars

def init_channel_info(ch_model):
    chs = ch_model.objects.filter(source='front')
    for ch in chs:
        ch.delete()
    
    chs = ch_model.objects.filter(source='micro')
    for ch in chs:
        ch.delete()


def get_ch_info(ch_model, source):
    try:
        return ch_model.objects.filter(source=source).get(log=0)
    
    except ch_model.DoesNotExist:
        return False
    

def send_front_message(data):
    ch_name = ws_vars.front_channel_name
    if ch_name:
        ch_layer = get_channel_layer()
        payload = {
            'type': 'front.message',
            'data': data
        }
        async_to_sync(ch_layer.send)(
            ch_name,
            payload
        )
    
    else:
        # print("Front not connected")
        pass
