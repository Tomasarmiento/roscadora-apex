import struct, ctypes
from ctypes import Structure, Union, c_uint16, c_uint32, c_float, c_bool, c_ulong
from apps.service.acdp.messages_base import BaseStructure

ACDP_CTRLADDR_MTR = 1
ACDP_CTRLADDR_PC  = 254


class CtrlHeaderEnums:
    FLAG_IS_RESP        = 1 << 0
    FLAG_ECHO_TIMEOUT   = 1 << 15


class CtrlHeader(BaseStructure):
    _fields_ = [
        ('device_type', c_uint16),  # Tipo de dispositivo que emite el mensaje (DARX, SACX, ASIX, etc)
        ('firmware_version', c_uint16), # Version del firmware

        ('object', c_uint16),   # Utilizado para hacer referencia a uno de varios objetos del mismo tipo

        ('flags', c_uint16),    # Bits para indicaciones varias.

        ('msg_id', c_uint32),   # Numero secuencial incremental con cada mensaje generado que no es respuesta. Las respuestas llevan el mismo ID que el mensaje que responden.
        ('timestamp', c_uint32),    # Marca de tiempo del mensaje.

        ('msg_code', c_uint16), # Codigo que identifica el proposito del mensaje.
        ('data_len8', c_uint16) # Longitud de los datos en bytes.
    ]

class IpcHeader(BaseStructure):
    _fields_ = [
        ('src_addr', c_uint16), # Emisor del mensaje (0: cuando no se utiliza)
        ('dst_addr', c_uint16), # Destinatario del mensaje (0: no se reenvia a ningun dispositivo externo)

        ('ctrl', CtrlHeader)
    ]