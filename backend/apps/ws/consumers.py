from cmath import log
import json
import time

from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async
from channels.exceptions import StopConsumer
from channels.layers import get_channel_layer

from apps.ws.models import ChannelInfo
from apps.ws.utils.variables import MicroState
from apps.ws.utils import variables as ws_vars

from apps.control.utils import variables as ctrl_vars
from apps.control.utils import functions as ctrl_fun
from apps.control.utils import routines as ctrl_rtns

from apps.service.acdp import messages_base as msg_base
from apps.service.api.variables import Commands
from apps.service.acdp.handlers import build_msg



class FrontConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.set_channel_info()
        ws_vars.front_channel_name = self.channel_name
        print("FRONT WS CONNECTED")
        await self.accept()
    
    async def receive(self, text_data=None, bytes_data=None):
        print(text_data)
    
    async def disconnected(self, close_code):
        print("Front ws disconnected, code", close_code)
        await self.delete_channel_info()
        await self.close()
    
    async def front_message(self, event):
        await self.send(text_data=json.dumps(event['data']))
    
    @database_sync_to_async
    def set_channel_info(self):
        ChannelInfo.objects.create(
            source = 'front',
            name = self.channel_name,
            log = 0
        )
    
    @database_sync_to_async
    def delete_channel_info(self):
        print("dentro de delete channel info")
        channel_info = ChannelInfo.objects.get(name=self.channel_name)
        channel_info.delete()

class MicroDataConsumer(WebsocketConsumer):

    def connect(self):
        ChannelInfo.objects.create(
            source='micro',
            name = self.channel_name,
            log = 0
            )
        ws_vars.back_channel_name = self.channel_name
        self.accept()
        print('Micro WS data connected')

    def receive(self, text_data=None, bytes_data=None):
        #print("dentro de receive")
        
        h_bytes_len = MicroState.last_rx_header.bytes_length
        if len(bytes_data) > h_bytes_len:               # Longitud de datos mayor que cabecera. Si no es echo request
            MicroState.last_rx_header.store_from_raw(bytes_data[:h_bytes_len])
            MicroState.last_rx_data.store_from_raw(bytes_data[h_bytes_len:])
            ctrl_fun.update_states(micro_data=MicroState.last_rx_data)
            #print("dentro de receive",ctrl_fun.update_states(micro_data=MicroState.last_rx_data))
            
            if MicroState.turn_load_drv_off:        # Flag de apagar driver de cabezal cuando el plato está clampeado
                MicroState.turn_load_drv_off = False
                command = Commands.power_off
                axis = ctrl_vars.AXIS_IDS['carga']
                msg_id = ws_vars.MicroState.last_rx_header.get_msg_id() + 1
                ws_vars.MicroState.msg_id = msg_id
                header = build_msg(command, eje=axis, msg_id=msg_id)
                header = header.pacself()
                self.send(bytes_data=header)
            
            if MicroState.turn_turn_drv_off:        # Flag de apagar driver de husillo cuando rpm es 0
                print('APAGAR HUSILLO')

                if ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['giro']]['estado'] == 'slave':
                    print('apaga sincronismo husill')
                    axis = ctrl_vars.AXIS_IDS['avance']
                    msg_id = ws_vars.MicroState.last_rx_header.get_msg_id() + 1
                    ws_vars.MicroState.msg_id = msg_id
                    command = Commands.sync_off
                    header = build_msg(command, msg_id=msg_id, eje=axis)
                    header = header.pacself()
                    self.send(bytes_data=header)

                print('apaga enable husillo')
                axis = ctrl_vars.AXIS_IDS['giro']
                msg_id = ws_vars.MicroState.last_rx_header.get_msg_id() + 1
                ws_vars.MicroState.msg_id = msg_id
                command = Commands.power_off
                header = build_msg(command, eje=axis, msg_id=msg_id)
                header = header.pacself()
                self.send(bytes_data=header)
            
                MicroState.turn_turn_drv_off = False
                
            if ws_vars.MicroState.loc_i_states['end'] == False:     # Boton continuar presionado
                ws_vars.MicroState.end_master_routine = True
            
            elif ws_vars.MicroState.loc_i_states['continue'] == True:     # Boton continuar presionado
                if ws_vars.MicroState.master_running == True:
                    print('Master ya está ejecutándose')
                
                else:
                    ctrl_rtns.MasterHandler().start()
            

            # show_states(MicroState.last_rx_header, MicroState.last_rx_data)
        else:
            MicroState.last_rx_header.store_from_raw(bytes_data)
        
        

    def micro_command(self, event):
        self.send(bytes_data=event['bytes_data'])


    def disconnect(self, close_code):
        print("DISCONNECED CODE: ", close_code)

        channel_info = ChannelInfo.objects.get(name=self.channel_name)
        channel_info.delete()

        self.close()


class MicroLogConsumer(WebsocketConsumer):

    def connect(self):
        ChannelInfo.objects.create(
            source='micro',
            name = self.channel_name,
            log = 1
            )
        ws_vars.back_channel_name = self.channel_name
        self.accept()
        print('Micro WS log connected')
    
    def receive(self, text_data=None, bytes_data=None):
        print(text_data)

    def micro_command(self, event):
        self.send(bytes_data=event['bytes_data'])

    def disconnect(self, close_code):
        print("DISCONNECED CODE: ", close_code)

        channel_info = ChannelInfo.objects.get(name=self.channel_name)
        channel_info.delete()

        self.close()


def show_states(header, data):
    drv_fault_flag = msg_base.DrvFbkDataFlags.FAULT
    print("-"*50)
    print(ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['drv_fbk_flags'] & drv_fault_flag == drv_fault_flag)
    print(ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['drv_fbk_flags'] & drv_fault_flag == drv_fault_flag)
    print(ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['drv_fbk_flags'] & drv_fault_flag == drv_fault_flag)

