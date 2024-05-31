import struct, ctypes
from ctypes import c_uint16, c_uint32, c_float, c_bool, c_ulong

from .ctrl_headers import CtrlHeader
from .messages_base import BaseStructure
from .tipo_datos8 import IpAddr, IpConfig, MacAddr


ACDP_IP_ADDR = '192.168.1.99' #CONTROLADOR IP

#------------------------------------------------------------------------------

ACDP_VERSION = 4

# IP Multicast
ACDP_MULTICAST_IPADDR0 = 239
ACDP_MULTICAST_IPADDR1 = 255
ACDP_MULTICAST_IPADDR2 = 255
ACDP_MULTICAST_IPADDR3 = 251

# Puerto UDP
ACDP_UDP_PORT    = 57903
# QoS_CRITICA   = 57903
# QoS_ALTA      = 57902
# QoS_MEDIA     = 57901

# Canal Broadcast
ACDP_BROADCAST_CHANNEL = 65535

#------------------------------------------------------------------------------

ACDP_CTRLCXN_IDX_MTR    = 0
ACDP_CANT_CTRLCXNS      = 8


class AcdpHeader(BaseStructure):
    _fields_ = [
        ('version', c_uint16),      # Version del protocolo.
        ('channel', c_uint16),      # Se asigna en la conexion. Se utiliza para organizar comunicaciones en la PC.
        ('ip_addr', IpAddr),        # Direccion IP del dispositivo con quien esta conectado.
        ('dest_addr', IpAddr),      # Direccion IP del destinatario del mensaje.

        ('ctrl', CtrlHeader)
    ]

    def get_msg_id(self):
        return self.ctrl.msg_id

    def set_msg_id(self, msg_id):
        setattr(self.ctrl, 'msg_id', msg_id)
    
    def set_data_len(self, data_len):
        setattr(self.ctrl, 'data_len8', data_len)
    
    def get_msg_code(self):         # Used on rx msg
        return self.ctrl.msg_code
    
    def store_from_raw(self, raw_values):
        super().store_from_raw(raw_values)
        
        self.flags = self.ctrl.flags
        self.msg_id = self.ctrl.msg_id
        self.timestamp = self.ctrl.timestamp
        self.msg_code = self.ctrl.msg_code
        self.data_len = self.ctrl.data_len8


class NetRoute(BaseStructure):
    _fields_ = [
        ('ip_addr', IpAddr),
        ('mac_addr', MacAddr),
        ('udp_port', c_uint16)
    ]


class AcdpConfigLocalNet(BaseStructure):
    _fields_ = [
        ('ip', IpConfig),
        ('mac_addr', MacAddr),
        ('ctrl_addr', c_uint16)
    ]


class AcdpConfigEcat(BaseStructure):
    _fields_ = [
        ('vlan_id', c_uint16)
    ]


class AcdpConfig(BaseStructure):
    _fields_ = [
        ('local_net', AcdpConfigLocalNet),

        ('ctrl_cxns', NetRoute * ACDP_CANT_CTRLCXNS),

        ('ecat', AcdpConfigEcat)
    ]


class AcdpConfigMsg(BaseStructure):
    _fields_ = [
        ('header', AcdpHeader),
        ('config', AcdpConfig)
    ]