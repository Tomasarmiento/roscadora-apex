# coding=utf-8
import struct, ctypes
from ctypes import addressof, Structure, Union, c_uint32, c_float, c_bool, c_int32


class BaseStructure(Structure):

    empty = True
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.data_length = self.get_len()
        self.bytes_length = self.get_bytes_size()

    def get_format(self):
        str_format = ''
        f = ''
        for field in self._fields_:
            field_value = field[1]

            if issubclass(field_value, ctypes._SimpleCData):
                f = field_value._type_

            elif issubclass(field_value, ctypes.Array):
                element = getattr(self, field[0])
                f = element[0].get_format() * field[1]._length_
            
            elif field_value:
                f = field_value().get_format()

            str_format = ''.join((str_format, f))
        return str_format

    def get_bytes_size(self):
        # return ctypes.sizeof(self)
        # return struct.calcsize(self.get_format())
        view = memoryview(self)
        size = view.itemsize
        view.release()
        return size

    def get_values(self):   # Returns a tuple with structure values
        values = ()
        for field in self._fields_:
            field_value = field[1]
            field_name = field[0]
            value = ()

            if issubclass(field_value, ctypes._SimpleCData):
                value = (getattr(self, field_name),)
            
            elif issubclass(field_value, ctypes.Array):
                arr = getattr(self, field_name)
                for j in range(field_value._length_):
                    if issubclass(arr[j].__class__, ctypes.Structure):
                        value = sum((value, arr[j].get_values()), ())
                    else:
                        value = sum((value, (arr[j],)), ())
            
            else:       # BaseStructure
                value = getattr(self, field_name).get_values()
            
            values = sum((values, value), ())

        return values

    def get_len(self):
        return len(self.get_values())

    def store_values(self, values):     # Receives values in tuple to store
        i = 0
        for field in self._fields_:
            field_value = field[1]
            field_name = field[0]

            if issubclass(field_value, ctypes._SimpleCData):
                value = values[i]
                setattr(self, field_name, value)
                i = i + 1

            elif issubclass(field_value, ctypes.Array):
                arr = getattr(self, field_name)
                arr_len = field_value._length_
                arr_type = arr._type_()
                arr_type_len = arr_type.get_len()
                for j in range(arr_len):
                    arr[j].store_values(values[i:(i+arr_type_len)])
                    i = i + j * arr_type_len
            
            else:
                vals = field_value()
                vals_len = vals.get_len()
                vals.store_values(values[i:(i+vals_len)])
                i = i + vals_len
                setattr(self, field_name, vals)

    def pacself(self):    # Returns structure in bytes format
        view = memoryview(self)
        raw_data = view.tobytes()
        view.release()
        return raw_data

    def unpacdata(self, raw_data):
        unpacked_data = struct.unpack(self.get_format(), raw_data)
        return unpacked_data

    def store_from_raw(self, raw_values):
        ctypes.memmove(addressof(self), raw_values, len(raw_values))

    def to_dict(self):

        dict = {}
        for field in self._fields_:
            field_type = field[1]
            key = field[0]
            value = getattr(self, key)

            if not issubclass(field_type, ctypes._SimpleCData):
                aux_dict = value.to_dict()
                value = aux_dict

            dict[key] = value

        return dict


# --------------------------------------------------------------------------------------------#
# -------------------------------- Códigos de Mensajes ---------------------------------------#
# --------------------------------------------------------------------------------------------#


class AcdpMsgType:
    SYS       = 0x0000   # Sistema
    CXN       = 0x1000   # Conexion
    CMD       = 0x2000   # Comandos
    DATA      = 0x3000   # Datos
    CFG_SET   = 0x4000   # Seteo configuracion
    CFG_REQ   = 0x5000   # Solicitud configuracion
    CFG_DAT   = 0x6000   # Datos de configuracion


class AcdpMsgLevel:
    BASE          = 0x0000
    DEVICE        = 0x0100
    APPLICATION   = 0x0200


class AcdpMsgCxn:       # Connection
    CD_CONNECT             = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x01
    CD_DISCONNECT          = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x02
    CD_CONNECTION_STAT     = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x03
    CD_FORCE_CONNECT       = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x04
    CD_ECHO_REQ            = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x05
    CD_ECHO_REPLY          = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x06
    CD_ECHO_TIMEOUT        = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x07
    CD_RTCSYNC_REQ         = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x08
    CD_RTCSYNC_REPLY       = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x09
    CD_CONFIG_REQ          = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x0A
    CD_CONFIG_DAT          = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x0B
    CD_CONFIG_SET_DEFAULT  = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x0C
    CD_IPCONFIG_SET        = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x0D
    CD_CTRL_CONFIG_SET     = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x0E
    CD_CTRL_CONFIG_CLR     = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x0F
    CD_RTC_OFFSET_SET      = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x10
    CD_ECAT_VLAN_ID_SET    = AcdpMsgType.CXN + AcdpMsgLevel.BASE + 0x11


class AcdpMsgCfgSet:
    CD_SUCCESSFUL          = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x01
    CD_REJECTED            = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x02
    CD_DEFAULT             = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x03
    CD_RESTORE_FROM_FLASH  = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x04
    CD_SAVE_TO_FLASH       = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x05
    CD_AVI                 = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x06      # Parametro: Acdp::Avi::tConfig
    CD_ENC                 = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x07      # Parametro: Acdp::Enc::tConfig
    CD_DRV_FBK             = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x08      # Parametro: Acdp::DrvFbk::tConfig
    CD_DRV_ECAT            = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x09      # Parametro: Acdp::DrvCmd::tConfig
    CD_DRV_ANA             = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x0a      # Parametro: Acdp::DrvCmd::tConfig
    CD_DRV_PULSE           = AcdpMsgType.CFG_SET + AcdpMsgLevel.BASE + 0x0b      # Parametro: Acdp::DrvCmd::tConfig


class AcdpMsgCfgReq:
    kCd_Rejected    = AcdpMsgType.CFG_REQ + AcdpMsgLevel.BASE + 0x01
    kCd_Avi         = AcdpMsgType.CFG_REQ + AcdpMsgLevel.BASE + 0x02
    kCd_Enc         = AcdpMsgType.CFG_REQ + AcdpMsgLevel.BASE + 0x03
    kCd_DrvFbk      = AcdpMsgType.CFG_REQ + AcdpMsgLevel.BASE + 0x04
    kCd_DrvEcat     = AcdpMsgType.CFG_REQ + AcdpMsgLevel.BASE + 0x05
    kCd_DrvAna      = AcdpMsgType.CFG_REQ + AcdpMsgLevel.BASE + 0x06
    kCd_DrvPulse    = AcdpMsgType.CFG_REQ + AcdpMsgLevel.BASE + 0x07


class AcdpMsgCfgDat:
    CD_AVI         = AcdpMsgType.CFG_DAT + AcdpMsgLevel.BASE + 0x01     # Dato: Acdp::Avi::tConfig
    CD_ENC         = AcdpMsgType.CFG_DAT + AcdpMsgLevel.BASE + 0x02     # Dato: Acdp::Enc::tConfig
    CD_DRVFBK      = AcdpMsgType.CFG_DAT + AcdpMsgLevel.BASE + 0x03     # Dato: Acdp::DrvFbk::tConfig
    CD_DRVECAT     = AcdpMsgType.CFG_DAT + AcdpMsgLevel.BASE + 0x04     # Dato: Acdp::DrvCmd::tConfig
    CD_DRVANA      = AcdpMsgType.CFG_DAT + AcdpMsgLevel.BASE + 0x05     # Dato: Acdp::DrvCmd::tConfig
    CD_DRVPULSE    = AcdpMsgType.CFG_DAT + AcdpMsgLevel.BASE + 0x06     # Dato: Acdp::DrvCmd::tConfig


class AcdpMsgData:
    CD_ALL     = AcdpMsgType.DATA + AcdpMsgLevel.BASE + 0x01    # Dato: Acdp::tData
    CD_AVI     = AcdpMsgType.DATA + AcdpMsgLevel.BASE + 0x02    # Dato: Acdp::Avi::tData
    CD_ENC     = AcdpMsgType.DATA + AcdpMsgLevel.BASE + 0x03    # Dato: Acdp::Enc::tData
    CD_DRVFBK  = AcdpMsgType.DATA + AcdpMsgLevel.BASE + 0x04    # Dato: Acdp::DrvFbk::tData
    CD_DRVCMD  = AcdpMsgType.DATA + AcdpMsgLevel.BASE + 0x05    # Dato: Acdp::DrvCmd::tData


class AcdpMsgCmdParamSetTareAvi(BaseStructure):
    _fields_ = [
        ('tare', c_float)
    ]


class AcdpMsgCmdParamSetZeroEnc(BaseStructure):
    _fields_ = [
        ('zero', c_float)
    ]


class AcdpMsgCmdParamSetZeroDrvFbk(BaseStructure):
    _fields_ = [
        ('zero', c_float)
    ]


class AcdpMsgCmdParam(BaseStructure):
    _fields_ = [
        ('set_tare_avi', AcdpMsgCmdParamSetTareAvi),
        ('set_zero_enc', AcdpMsgCmdParamSetZeroEnc),
        ('set_zero_drvFbk', AcdpMsgCmdParamSetZeroDrvFbk)
    ]


class AcdpMsgCmd:
    CD_REJECTED                     = AcdpMsgType.CMD + AcdpMsgLevel.BASE + 0X01
    CD_ENTER_SAFE_MODE              = AcdpMsgType.CMD + AcdpMsgLevel.BASE + 0X02
    CD_EXIT_SAFE_MODE               = AcdpMsgType.CMD + AcdpMsgLevel.BASE + 0X03
    CD_STOP_ALL                     = AcdpMsgType.CMD + AcdpMsgLevel.BASE + 0X04
    CD_AVI_SET_TARE                 = AcdpMsgType.CMD + AcdpMsgLevel.BASE + 0X05   # Parametro: Param::tSetTare
    CD_ENC_SET_ZERO_RELATIVELY      = AcdpMsgType.CMD + AcdpMsgLevel.BASE + 0X06   # Parametro: Param::tSetZero
    CD_ENC_SET_ZERO_ABSOLUTELY      = AcdpMsgType.CMD + AcdpMsgLevel.BASE + 0X07   # Parametro: Param::tSetZero
    CD_DRV_FBK_SET_ZERO_RELATIVELY  = AcdpMsgType.CMD + AcdpMsgLevel.BASE + 0X08   # Parametro: Param::tSetZero
    CD_DRV_FBK_SET_ZERO_ABSOLUTELY  = AcdpMsgType.CMD + AcdpMsgLevel.BASE + 0X09   # Parametro: Param::tSetZero
    CD_RESET_FAULTS                 = AcdpMsgType.CMD + AcdpMsgLevel.BASE + 0X10   # Resetea fallas de drivers general (todos los ejes)

    Param                           = AcdpMsgCmdParam


class AcdpMsg:
    kTypeMsk    = 0xf000
    kLevelMsk   = 0x0f00
    Type        = AcdpMsgType
    Level       = AcdpMsgLevel
    Cxn         = AcdpMsgCxn
    CfgSet      = AcdpMsgCfgSet
    CfgReq      = AcdpMsgCfgReq
    CfgDat      = AcdpMsgCfgDat
    Data        = AcdpMsgData
    Cmd         = AcdpMsgCmd


# --------------------------------------------------------------------------------------------#
# -------------------------------- Entrada Analogica -----------------------------------------#
# --------------------------------------------------------------------------------------------#


class AcdpAviConfigFlagsBits(BaseStructure):
    _fields_ = [
        ('inv_sign', c_bool)
    ]

# class AcdpAviConfigFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('flags', AcdpAviConfigFlagsBits)
#     ]


class AcdpAviConfigCalib(BaseStructure):
    _fields_ = [
        ('m', c_float),
        ('zero', c_float)
    ]


class AcdpAviConfig(BaseStructure):
    _fields_ = [
        # ('flags', AcdpAviConfigFlags),
        ('flags', c_uint32),
        ('calib', AcdpAviConfigCalib)
    ]


class AcdpAviData(BaseStructure):
    _fields_ = [
        ('tare', c_float),
        ('value', c_float)
    ]


class AcdpAvi(BaseStructure):
    _fields_ = [
        ('t_config', AcdpAviConfig),
        ('t_data', AcdpAviData)
    ]


# --------------------------------------------------------------------------------------------#
# -------------------------------------- Encoder ---------------------------------------------#
# --------------------------------------------------------------------------------------------#


class AcdpEncConfigFlagsBits(BaseStructure):
    _fields_ = [
        ('inv_med', c_uint32),
        ('modulo', c_uint32),
        ('absolute', c_uint32),
        ('non_volatile_zero', c_uint32),
        ('absolute_zero_settled', c_uint32)
    ]


# class AcdpEncConfigFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpEncConfigFlagsBits)
#     ]


class AcdpEncConfig(BaseStructure):
    _fields_ = [
        # ('flags', AcdpEncConfigFlags),
        ('flags', c_uint32),
        ('resolution', c_uint32),
        ('range', c_float),
        ('zero', c_float),
        ('offset', c_float)
    ]


class AcdpEncDataFlagsBits(BaseStructure):
    _fields_ = [
        ('ready', c_bool),
        ('enabled', c_bool),
        ('fault', c_bool),
        ('positive_0t', c_bool),
        ('negative_0t', c_bool),
        ('home_switch', c_bool),
        ('homing_ended_ok', c_bool),
        ('homing_error', c_bool),
        ('zero_settled', c_bool),
        ('unknown_zero', c_bool),
        ('pos_dec', c_bool),
        ('time_0v_pulso', c_bool),
    ]

# class AcdpEncDataFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpEncDataFlagsBits)
#     ]

class AcdpEncData(BaseStructure):
    _fields_ = [
        # ('flags', AcdpEncDataFlags),
        ('flags', c_uint32),

        ('int_stamp', c_uint32),
        ('int_pos_abs', c_int32),
        ('int_pos_abs_cross', c_int32),

        ('config', AcdpEncConfig),
        ('pos_abs', c_float),
        ('pos', c_float),
        ('vel', c_float)
    ]


class AcdpEnc:
    _fields_ = [
        ('config', AcdpEncConfig),
        ('data', AcdpEncData)
    ]


# --------------------------------------------------------------------------------------------#
# ----------------------------------- Drive Feedback -----------------------------------------#
# --------------------------------------------------------------------------------------------#


class AcdpDrvFbkConfigFlagsBits(BaseStructure):
    _fields_ = [
        ('inv_med', c_bool),
        ('modulo', c_bool),
        ('absolute', c_bool),
        ('non_volatile_zero', c_bool),
        ('absolute_zero_settled', c_bool),
    ]


# class AcdpDrvFbkConfigFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpDrvFbkConfigFlagsBits)
#     ]


class AcdpDrvFbkConfigPos(BaseStructure):
    _fields_ = [
        ('rsl', c_int32),        # Resolution
        ('range', c_float),
        ('zero', c_float),
        ('offset', c_float)
    ]


class AcdpDrvFbkConfigVel(BaseStructure):
    _fields_ = [
        ('rsl', c_uint32),      # Resolution
        ('range', c_float)
    ]


class AcdpDrvFbkConfig(BaseStructure):
    _fields_ = [
        # ('flags', AcdpDrvFbkConfigFlags),
        ('flags', c_uint32),
        ('pos', AcdpDrvFbkConfigPos),
        ('vel', AcdpDrvFbkConfigVel),
        ('torque', AcdpDrvFbkConfigVel)
    ]

class DrvFbkDataFlags:
    READY               = 1 << 0
    ENABLED             = 1 << 1
    FAULT               = 1 << 2
    POSITIVE_OT         = 1 << 3
    NEGATIVE_OT         = 1 << 4
    HOME_SWITCH         = 1 << 5
    HOMMING_ENDED_OK    = 1 << 6
    HOMMING_ERROR       = 1 << 7
    ZERO_SETTLED        = 1 << 8
    UNKNOWN_ZERO        = 1 << 9

class AcdpDrvFbkDataFlagsBits(BaseStructure):
    _fields_ = [
        ('ready', c_bool),
        ('enabled', c_bool),
        ('fault', c_bool),
        ('positive_ot', c_bool),
        ('negative_ot', c_bool),
        ('home_switch', c_bool),
        ('homming_ended_ok', c_bool),
        ('homming_error', c_bool),
        ('zero_settled', c_bool),
        ('unknown_zero', c_bool)
    ]


# class AcdpDrvFbkDataFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpDrvFbkDataFlagsBits)
#     ]


class AcdpDrvFbkData(BaseStructure):
    _fields_ = [
        # ('flags', AcdpDrvFbkDataFlags),
        ('flags', c_uint32),

        ('config', AcdpDrvFbkConfig),
        ('pos_abs', c_float),           # Pos sin cerar
        ('pos', c_float),
        ('vel', c_float),               # [mm/s]
        ('torque', c_float)
    ]


class AcdpDrvFbk(BaseStructure):
    _fields_ = [
        ('config', AcdpDrvFbkConfig),
        ('data', AcdpDrvFbkData)
    ]


# --------------------------------------------------------------------------------------------#
# ------------------------------------ Drive Comando -----------------------------------------#
# --------------------------------------------------------------------------------------------#


class AcdpDrvCmdConfigFlagsBits(BaseStructure):
    _fields_ = [
        ('ana_ref_bipolar', c_bool),
        ('invertir_sentido', c_bool),
        ('chk_fbk_enab', c_bool),
        ('homing_enabled', c_bool),
    ]


# class AcdpDrvCmdConfigFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpDrvCmdConfigFlagsBits)
#     ]


class AcdpDrvCmdConfigUnionAna(BaseStructure):
    _fields_ = [
        ('vel_fsd', c_float)    # [mm/s] - [Hz] - Para ref analogica
    ]


class AcdpDrvCmdConfigUnionPulse(BaseStructure):
    _fields_ = [
        ('paso_pos', c_float),          # [mm] - Para ref de pulsos
        ('prd_pulso_max', c_float)      # [s] - Para ref de pulsos (para evitar que el tiempo de pulso genere inestabilidad en el control)
    ]


class AcdpDrvCmdConfigUnionEcatVel(BaseStructure):
    _fields_ = [
        ('rsl', c_uint32),
        ('range', c_float)
    ]


class AcdpDrvCmdUnionEcat(BaseStructure):
    _fields_ = [
        ('ecat', AcdpDrvCmdConfigUnionEcatVel)
    ]


# class AcdpDrvCmdConfigUnion(BaseUnion):
#     _fields_ = [
#         ('ana', AcdpDrvCmdConfigUnionAna),
#         ('pulse', AcdpDrvCmdConfigUnionPulse),
#         ('vel', AcdpDrvCmdUnionEcat)
#     ]
class AcdpDrvCmdConfigUnion(BaseStructure):
    _fields_ = [
        ('float', c_float),
        ('float_2', c_float)
    ]


class AcdpDrvCmdConfigChkFbk(BaseStructure):
    _fields_ = [
        ('error_max', c_float),
        ('delta_t', c_float)
    ]


class AcdpDrvCmdConfig(BaseStructure):      # Configuracion Drive
    _fields_ = [
        # ('flags', AcdpDrvCmdConfigFlags),
        ('flags', c_uint32),
        ('union', AcdpDrvCmdConfigUnion),
        ('chk_fbk', AcdpDrvCmdConfigChkFbk),
        ('tau_filtro', c_float)
    ]


class AcdpDrvCmdDataFlagsBits(BaseStructure):
    _fields_ = [
        ('pow_enabled', c_bool),
        ('homing', c_bool),
        ('pos_feedback_error', c_bool),
        ('limit_vel_max', c_bool),
        ('limit_vel_min', c_bool)
    ]


# class AcdpDrvCmdDataFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpDrvCmdDataFlagsBits)
#     ]


class AcdpDrvCmdData(BaseStructure):        # Datos Drive
    _fields_ = [
        # ('flags', AcdpDrvCmdDataFlags),
        ('flags', c_uint32),
        ('actuacion', c_float)
    ]


class AcdpDrvCmd(BaseStructure):
    _fields_ = [
        ('config', AcdpDrvCmdConfig),
        ('data', AcdpDrvCmdData)
    ]


# --------------------------------------------------------------------------------------------#
# --------------- Control automatico PI Tipo 0 ([Actuacion/Referencia] = 1) ------------------#
# --------------------------------------------------------------------------------------------#


class AcdpPiT0ConfigFf(BaseStructure):  # Factor Feedforward (Rango de 0 a 1)
    _fields_ = [
        ('k', c_float)
    ]


class AcdpPiT0ConfigPid(BaseStructure):
    _fields_ = [
        ('tau', c_float),   # [s]
        ('k', c_float)      # [-]
    ]


class AcdpPiT0ConfigOut(BaseStructure):
    _fields_ = [
        ('max', c_float)
    ]


class AcdpPiT0Config(BaseStructure):    # Configuracion control automatico PI Tipo 0
    _fields_ = [
        ('ff', AcdpPiT0ConfigFf),
        ('pid', AcdpPiT0ConfigPid),
        ('tiempo_fin', c_float),
        ('out', AcdpPiT0ConfigOut)
    ]


class AcdpPiT0DataFf(BaseStructure):
    _fields_ = [
        ('out', c_float)
    ]


class AcdpPiT0DataPid(BaseStructure):
    _fields_ = [
        ('integ_out', c_float),
        ('prop_out', c_float)
    ]


class AcdpPiT0Data(BaseStructure):    # Datos control automatico PI Tipo 0
    _fields_ = [
        ('ref', c_float),
        ('ff', AcdpPiT0DataFf),
        ('pid', AcdpPiT0DataPid),
        ('out', c_float)
    ]


class AcdpPiT0(BaseStructure):
    _fields_ = [
        ('config', AcdpPiT0Config),
        ('data', AcdpPiT0Data)
    ]


# --------------------------------------------------------------------------------------------#
# ------------ Control automatico PID Tipo 1 ([Actuacion/Referencia] = 1/s) ------------------#
# --------------------------------------------------------------------------------------------#


class AcdpPiT1ConfigRef(BaseStructure):     # Cero desactiva el limite (Limite para la derivada de la referencia)
    _fields_ = [
        ('slope_max_deriv', c_float)
    ]


class AcdpPiT1ConfigFf(BaseStructure):
    _fields_ = [
        ('k', c_float)                      # Factor Feedforward (Rango de 0 a 1)
    ]


class AcdpPiT1ConfigPid(BaseStructure):
    _fields_ = [
        ('tau_i', c_float),                 # [s]
        ('tau_p', c_float),                 # [s]
        ('k', c_float)                      # [-]
    ]


class AcdpPidT1Config(BaseStructure):        # Configuracion control automatico PID Tipo 1
    _fields_= [
        ('ref', AcdpPiT1ConfigRef),
        ('ff', AcdpPiT1ConfigFf),
        ('pid', AcdpPiT1ConfigPid),
        ('tiempo_fin', c_float),
        ('error_final', c_float)
    ]


class AcdpPiT1DataFf(BaseStructure):
    _fields_ = [
        ('out', c_float)
    ]


class AcdpPiT1DataPid(BaseStructure):
    _fields_ = [
        ('integ_out', c_float),
        ('prop_out', c_float),
        ('deriv_out', c_float)
    ]


class AcdpPidT1Data(BaseStructure):          # Datos control automatico PID Tipo 1
    _fields_= [
        ('ref', c_float),
        ('ff', AcdpPiT1DataFf),             # Derivada de la referencia
        ('pid', AcdpPiT1DataPid),
        ('out', c_float)
    ]


class AcdpPidT1(BaseStructure):
    _fields_ = [
        ('config', AcdpPidT1Config),
        ('data', AcdpPidT1Data)
    ]


# ------------------------------------------------------------------------------------#

class Acpd:
    Msg     = AcdpMsg
    Avi     = AcdpAvi
    Enc     = AcdpEnc
    DrvFbk  = AcdpDrvFbk
    DrvCmd  = AcdpDrvCmd