# coding=utf-8
import struct, ctypes
from ctypes import c_int, c_int32, c_uint16, c_uint32, c_float

from .messages_base import AcdpAvi, AcdpMsgType, AcdpMsgLevel, AcdpPiT0Config, AcdpPiT0Data,\
    AcdpPidT1Config, AcdpPidT1Data, BaseStructure, AcdpDrvFbkData, AcdpEncData,\
        AcdpDrvCmdData, AcdpAviData

# --------------------------------------------------------------------------------------------#
# --------------------- Códigos de Mensajes propios de la aplicación -------------------------#
# --------------------------------------------------------------------------------------------#

class AcdpMsgCodes:
    
    class CfgSet:       # Seteo configuracion
        CD_MOV_POS = AcdpMsgType.CFG_SET + AcdpMsgLevel.APPLICATION + 0x01
        CD_MOV_FZA = AcdpMsgType.CFG_SET + AcdpMsgLevel.APPLICATION + 0x02
    
    class CfgReq:       # Solicitud configuracion
        CD_MOV_POS = AcdpMsgType.CFG_REQ + AcdpMsgLevel.APPLICATION + 0x01
        CD_MOV_FZA = AcdpMsgType.CFG_REQ + AcdpMsgLevel.APPLICATION + 0x02
    
    class CfgDat:       # Datos de configuracion
        CD_MOV_POS = AcdpMsgType.CFG_DAT + AcdpMsgLevel.APPLICATION + 0x01
        CD_MOV_FZA = AcdpMsgType.CFG_DAT + AcdpMsgLevel.APPLICATION + 0x02
    
    class Cmd:          # Comandos
        Cd_MovEje_EnterSafeMode         = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x01
        Cd_MovEje_ExitSafeMode          = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x02
        Cd_MovEje_PowerOn               = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x03
        Cd_MovEje_PowerOff              = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x04
        Cd_MovEje_SyncOn                = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x05     # Parametro: Param::tSyncOn
        Cd_MovEje_SyncOff               = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x06
        
        Cd_MovEje_Stop                  = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x07
        Cd_MovEje_FastStop              = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x08

        Cd_MovEje_RunZeroing            = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x09
        Cd_MovEje_RunPositioning        = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x0a
        Cd_MovEje_MovToVel              = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x0b     # Parametro: Param::tMovToVel
        Cd_MovEje_SetRefVel             = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x0c     # Parametro: Param::tSetRefVel
        Cd_MovEje_MovToPos              = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x0d     # Parametro: Param::tMovToPos
        Cd_MovEje_SetRefPos             = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x0e     # Parametro: Param::tSetRefPos
        Cd_MovEje_MovToPos_Yield        = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x0f     # Parametro: Param::tMovToPos_Yield
        Cd_MovEje_MovToPosLoad          = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x10     # Parametro: Param::tMovToPosLoad
        Cd_MovEje_SetRefPosLoad         = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x11     # Parametro: Param::tSetRefPosLoad
        Cd_MovEje_MovToPosLoad_Yield    = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x12     # Parametro: Param::tMovToPosLoad_Yield
        Cd_MovEje_MovToFza              = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x13     # Parametro: Param::tMovToFza
        Cd_MovEje_SetRefFza             = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x14     # Parametro: Param::tSetRefFza
        Cd_MovEje_MovToFza_Yield        = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x15     # Parametro: Param::tMovToFza_Yield
        Cd_MovEje_ResetDriveFault       = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x16     # Resetea fallas de driver por eje (hay que mandar id de eje)

        Cd_LocDO_Set                    = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x21     # Parametro: Param::tDO_Set
        Cd_RemDO_Set                    = AcdpMsgType.CMD + AcdpMsgLevel.APPLICATION + 0x22     # Parametro: Param::tDO_Set


# --------------------------------------------------------------------------------------------#
# ------------------------------ Parametros de los comandos ----------------------------------#
# --------------------------------------------------------------------------------------------#


class AcdpMsgParamsSyncOn(BaseStructure):
    _fields_ = [
        ('paso_eje_lineal', c_float)
    ]


class AcdpMsgParamsYield(BaseStructure):
    _fields_ = [
        ('factor_limite_elastico', c_float),
        ('correccion_pendiente', c_float),
        ('cedencia', c_float)
    ]


class AcdpMsgParamsMovToVel(BaseStructure):
    _fields_ = [
        ('reference', c_float)
    ]


class AcdpMsgParamsSetRefVel(BaseStructure):
    _fields_ = [
        ('reference', c_float)
    ]


class AcdpMsgParamsMovToPos(BaseStructure):
    _fields_ = [
        ('reference', c_float),
        ('ref_rate', c_float)
    ]


class AcdpMsgParamsSetRefPos(BaseStructure):
    _fields_ = [
        ('reference', c_float)
    ]


class AcdpMsgParamsMovToPosYield(BaseStructure):
    _fields_ = [
        ('mov_to_pos', AcdpMsgParamsMovToPos),
        ('yield', AcdpMsgParamsYield)
    ]


class AcdpMsgParamsMovToPosLoad(BaseStructure):
    _fields_ = [
        ('reference', c_float),
        ('ref_rate', c_float)
    ]


class AcdpMsgParamsSetRefPosLoad(BaseStructure):
    _fields_ = [
        ('reference', c_float)
    ]


class AcdpMsgParamsMovToPosLoadYield(BaseStructure):
    _fields_ = [
        ('mov_to_pos_load', AcdpMsgParamsMovToPosLoad),
        ('yield', AcdpMsgParamsYield)
    ]


class AcdpMsgParamsMovToFza(BaseStructure):
    _fields_ = [
        ('reference', c_float),
        ('ref_rate', c_float),
        ('vel_uns_max', c_float)
    ]


class AcdpMsgParamsSetRefFza(BaseStructure):
    _fields_ = [
        ('reference', c_float)
    ]


class AcdpMsgParamsMovToFzaYield(BaseStructure):
    _fields_ = [
        ('mov_to_fza', AcdpMsgParamsMovToFza),
        ('yield', AcdpMsgParamsYield)
    ]


class AcdpMsgParamsDoSet(BaseStructure):
    _fields_ = [
        ('value', c_uint16),
        ('mask', c_uint16)
    ]


class AcdpMsgParams(BaseStructure):
    _fields_ = [
        
        # Sincronismo
        # ------------------------------------------------
        ('sync_on', AcdpMsgParamsSyncOn),

        # Movimientos
        # ------------------------------------------------
        ('yield', AcdpMsgParamsYield),

        # Movimiento en velocidad
        # ------------------------------------------------
        ('mov_to_vel', AcdpMsgParamsMovToVel),
        ('set_ref_vel', AcdpMsgParamsSetRefVel),

        # Movimiento en posicion
        # ------------------------------------------------
        ('mov_to_pos', AcdpMsgParamsMovToPos),
        ('set_ref_pos', AcdpMsgParamsSetRefPos),
        ('mov_to_pos_yield', AcdpMsgParamsMovToPosYield),

        # Movimiento en posicion vista en la carga
        # ------------------------------------------------
        ('mov_to_pos_load', AcdpMsgParamsMovToPosLoad),
        ('set_ref_pos_load', AcdpMsgParamsSetRefPosLoad),
        ('mov_to_pos_load_yield', AcdpMsgParamsMovToPosLoadYield),

        # Movimiento en fuerza
        # ------------------------------------------------
        ('mov_to_fza', AcdpMsgParamsMovToFza),
        ('set_ref_fza', AcdpMsgParamsSetRefFza),
        ('mov_to_fza_yield', AcdpMsgParamsMovToFzaYield),

        # Escritura salidas digitales
        # ------------------------------------------------
        ('do_set', AcdpMsgParamsDoSet)
    ]


###############################################################################################
##################################### Estructuras #############################################
###############################################################################################


# --------------------------------------------------------------------------------------------#
# ------------------------------------- Control ----------------------------------------------#
# --------------------------------------------------------------------------------------------#

class AcdpControlEnums:
    # Analog inputs
    ID_X_AVI_FZA            = 0
    CANT_AVI                = 1

    # Encoders
    ID_X_ENC_RESERV_1       = 0
    ID_X_ENC_LOAD           = 1
    CANT_ENC                = 2

    # Drivers - Ethercat
    ID_X_DRV_ECAT_AVANCE    = 0
    ID_X_DRV_ECAT_GIRO      = 1
    ID_X_DRV_ECAT_CARGA     = 2
    CANT_DRV_ECAT           = 3

    # Drivers - Analog Reference
    ID_X_DRV_ANA_RESERV_1   = 0
    ID_X_DRV_ANA_RESERV_2   = 1
    CANT_DRV_ANA            = 2

    # Drivers - Pulse Reference
    ID_X_DRV_PULSE_RESERV_1 = 0
    CANT_DRV_PULSE          = 1


# --------------------------------------------------------------------------------------------#
# --------------------------------- Movimientos Eje ------------------------------------------#
# --------------------------------------------------------------------------------------------#


class AcdpAxisMovementEnums:
    ID_X_EJE_FIRSTROSCADO   = 0
    ID_X_EJE_PREV_ROSCADO   = ID_X_EJE_FIRSTROSCADO - 1
    ID_X_EJE_GIRO           = ID_X_EJE_PREV_ROSCADO + 1
    ID_X_EJE_AVANCE         = ID_X_EJE_GIRO + 1
    ID_X_EJE_POST_ROSCADO   = ID_X_EJE_AVANCE + 1
    ID_X_EJE_LAST_ROSCADO   = ID_X_EJE_POST_ROSCADO - 1

    ID_X_EJE_FIRST_CARGA    = ID_X_EJE_LAST_ROSCADO + 1
    ID_X_EJE_PREV_CARGA     = ID_X_EJE_FIRST_CARGA - 1
    ID_X_EJE_CARGA          = ID_X_EJE_PREV_CARGA + 1
    ID_X_EJE_POST_CARGA     = ID_X_EJE_CARGA + 1
    ID_X_EJE_LAST_CARGA     = ID_X_EJE_POST_CARGA - 1

    CANT_EJES               = ID_X_EJE_LAST_CARGA + 1


class AcdpAxisMovementsMovPosConfigFlagsBits(BaseStructure):
    _fields_ = [
        ('limit_pos_enab', c_int, 1),
        ('homing_sw_positive', c_int, 1),
        ('homing_with_index', c_int, 1)
    ]


# class AcdpAxisMovementsMovPosConfigFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpAxisMovementsMovPosConfigFlagsBits)
#     ]


class AcdpAxisMovementsMovPosConfigHoming(BaseStructure):
    _fields_ = [
        ('vel_posic', c_float),
        ('vel_cerado', c_float)
    ]


class AcdpAxisMovementsMovPosConfigLimites(BaseStructure):
    _fields_ = [
        ('pos_min', c_float),
        ('pos_max', c_float)
    ]


class AcdpAxisMovementsMovPosConfigMed(BaseStructure):
    _fields_ = [
        ('tau_filtro_pos_drv', c_float),
        ('tau_filtro_pos_load', c_float)
    ]


class AcdpAxisMovementsMovPosConfig(BaseStructure):
    _fields_ = [
        # ('flags', AcdpAxisMovementsMovPosConfigFlags),
        ('flags', c_uint32),
        ('homing', AcdpAxisMovementsMovPosConfigHoming),
        ('limites', AcdpAxisMovementsMovPosConfigLimites),
        ('med', AcdpAxisMovementsMovPosConfigMed),

        ('ctrl_vel', AcdpPiT0Config),
        ('fast_stpo_decel', c_float),       # Cero desactiva el límite

        ('ctrl_pos', AcdpPidT1Config)
    ]


class AcdpAxisMovementsMovPosDataFlagsBits(BaseStructure):
    _fields_ = [
        ('zero_switch_on', c_int, 1),
        ('pos_min_switch_on', c_int, 1),
        ('pos_max_switch_on', c_int, 1),
        ('pos_min_limit', c_int, 1),
        ('pos_max_limit', c_int, 1),
        ('vel_limit', c_int, 1)
    ]


# class AcdpAxisMovementsMovPosDataFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpAxisMovementsMovPosDataFlagsBits)
#     ]


class AcdpAxisMovementsMovPosDataHoming(BaseStructure):
    _fields_ = [
        # Maquina de Estados Secuencia de cerado. Estados en AcdpAxisMovementsMovPosDataHomingStates
        ('estado', c_int32)
    ]


class AcdpAxisMovementsMovPosDataHomingStates:
    EST_INICIAL             = 0
    EST_ACTIVACION_SWITCH   = 1
    EST_CAMBIO_DIRECCION    = 2
    EST_LIBERACION_SWITCH   = 3
    EST_INDEX_DETECTION     = 4


class AcdpAxisMovementsMovPosDataMedDrv(BaseStructure):
    _fields_ = [
        ('drv_fbk', AcdpDrvFbkData),
        ('pos_fil', c_float),
        ('vel_fil', c_float),
        ('torque_fil', c_float)
    ]


class AcdpAxisMovementsMovPosDataMedLoad(BaseStructure):
    _fields_ = [
        ('enc', AcdpEncData),
        ('pos_fil', c_float),
        ('vel_fil', c_float)
    ]


class AcdpAxisMovementsMovPosData(BaseStructure):
    _fields_ = [
        # ('flags', AcdpAxisMovementsMovPosDataFlags),
        ('flags', c_uint32),
        ('homing', AcdpAxisMovementsMovPosDataHoming),
        ('med_drv', AcdpAxisMovementsMovPosDataMedDrv),
        ('med_load', AcdpAxisMovementsMovPosDataMedLoad),

        ('ctrl_vel', AcdpPiT0Data),
        ('ctrl_pos', AcdpPidT1Data)
    ]


class AcdpAxisMovementsMovPos(BaseStructure):
    _fields_ = [
        # Config MovPos
        ('config', AcdpAxisMovementsMovPosConfig),

        # Data MovPos
        ('data', AcdpAxisMovementsMovPosData)
    ]


class AcdpAxisMovementsMovFzaConfigFlagsBits(BaseStructure):
    _fields_ = [
        ('limit_pos_enab', c_int, 1),
        ('rel_fza_pos_fija', c_int, 1),
        ('rel_fza_pos_negativa', c_int, 1)
    ]


# class AcdpAxisMovementsMovFzaConfigFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpAxisMovementsMovFzaConfigFlagsBits)
#     ]


class AcdpAxisMovementsMovFzaConfigLimites(BaseStructure):
    _fields_ = [
        ('fza_min', c_float),
        ('fza_max', c_float)
    ]


class AcdpAxisMovementsMovFzaConfigMedCalcRigidez(BaseStructure):
    _fields_ = [
        ('delta_pos', c_float)  # //[mm] Delta de posicion para el calculo de la rigidez
    ]


class AcdpAxisMovementsMovFzaConfigMed(BaseStructure):
    _fields_ = [
        ('tau_filtro_fza', c_float),    # [s] - Tau para el filtrado de las mediciones
        ('calc_rigidez', AcdpAxisMovementsMovFzaConfigMedCalcRigidez)
    ]


class AcdpAxisMovementsMovFzaConfigYield(BaseStructure):
    _fields_ = [
        ('fza_uns_min', c_float)    # [kgf] Fuerza minima utilizada para comenzar a evaluar el limite elastico
    ]


class AcdpAxisMovementsMovFzaConfig(BaseStructure):
    _fields_ = [
        # ('flags', AcdpAxisMovementsMovFzaConfigFlags),
        ('flags', c_uint32),
        ('limites', AcdpAxisMovementsMovFzaConfigLimites),
        ('med', AcdpAxisMovementsMovFzaConfigMed),
        ('yield', AcdpAxisMovementsMovFzaConfigYield),
        ('ctrl_fza', AcdpPidT1Config),
        ('rel_fza_pos_uns', c_float)    # [kgf/mm] Se usa para convertir la salida del control en velocidad
    ]


class AcdpAxisMovementsMovFzaDataFlagsBits(BaseStructure):
    _fields_ = [
        ('fza_min_limit', c_int, 1),  # 0
        ('fza_max_limit', c_int, 1),  # 1
        ('cedencia', c_int, 1)        # 2
    ]


# class AcdpAxisMovementsMovFzaDataFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpAxisMovementsMovFzaDataFlagsBits)
#     ]


class AcdpAxisMovementsMovFzaDataMed(BaseStructure):
    _fields_ = [
        ('cel', AcdpAviData),
        ('fza_fil', c_float),   # [kgf]

        ('rigidez_drive', c_float),     # [kgf/mm]
        ('rigidez_load', c_float),      # [kgf/mm]
        ('cedencia', c_float)           # [mm]
    ]


class AcdpAxisMovementsMovFzaData(BaseStructure):
    _fields_ = [
        # ('flags', AcdpAxisMovementsMovFzaDataFlags),
        ('flags', c_uint32),
        ('med', AcdpAxisMovementsMovFzaDataMed),
        ('ctrl_fza', AcdpPidT1Data),
        ('rel_fza_pos_uns', c_float)    # [kgf/mm]
    ]


class AcdpAxisMovementsMovFza(BaseStructure):
    _fields_ = [
        # Config MovFza
        ('config', AcdpAxisMovementsMovFzaConfig),

        # Data MovFza
        ('data', AcdpAxisMovementsMovFzaData)
    ]


class AcdpAxisMovementsMovEjeConfig(BaseStructure):
    _fields_ = [
        ('mov_pos', AcdpAxisMovementsMovPosConfig),
        ('mov_fza', AcdpAxisMovementsMovFzaConfig)
    ]


class AcdpAxisMovementsMovEjeDataMaqEst(BaseStructure):
    _fields_ = [
        ('flags_fin', c_uint32),    # Flags FinEstado. Ver AxisFlagsFin
        ('estado', c_int32)        # Maquina de Estados General. Ver StateMachine
    ]


class AxisFlagsFin:
    FLGFIN_OK                   = 1 << 0
    FLGFIN_CANCELLED            = 1 << 1
    FLGFIN_EM_STOP              = 1 << 2
    FLGFIN_DRV_HOMING_ERROR     = 1 << 3
    FLGFIN_ECHO_TIMEOUT         = 1 << 4
    FLGFIN_POS_ABS_DISABLED     = 1 << 5
    FLGFIN_UNKNOWN_ZERO         = 1 << 6
    FLGFIN_POS_FEEDBACK_ERROR   = 1 << 7
    FLGFIN_LIMIT_VEL_EXCEEDED   = 1 << 8
    FLGFIN_LIMIT_POS_EXCEEDED   = 1 << 9
    FLGFIN_LIMIT_FZA_EXCEEDED   = 1 << 10
    FLGFIN_YIELD                = 1 << 11
    FLGFIN_INVALID_STATE        = 1 << 12
    FLGFIN_DRV_NOT_ENABLED      = 1 << 13
    FLGFIN_AXIS_LIMIT_TORQUE_EXCEEDED        = 1 << 14


class StateMachine:
    EST_SAFE                = 0
    EST_PRE_INITIAL         = 1
    EST_INITIAL             = 2
    EST_POWERING_ON         = 3
    EST_POWERING_OFF        = 4
    EST_STOPPING            = 5
    EST_FAST_STOPPING       = 6
    EST_HOMING              = 7
    EST_POSITIONING         = 8
    EST_MOV_TO_VEL          = 9
    EST_MOV_TO_POS          = 10
    EST_MOV_TO_POS_LOAD     = 11
    EST_MOV_TO_FZA          = 12
    EST_SLAVE               = 13

    def get_state(state_value):
        if state_value == StateMachine.EST_SAFE:
            return 'safe'
        if state_value == StateMachine.EST_PRE_INITIAL:
            return 'pre_initial'
        if state_value == StateMachine.EST_INITIAL:
            return 'initial'
        if state_value == StateMachine.EST_POWERING_ON:
            return 'powering_on'
        if state_value == StateMachine.EST_POWERING_OFF:
            return 'powering_off'
        if state_value == StateMachine.EST_STOPPING:
            return 'stopping'
        if state_value == StateMachine.EST_FAST_STOPPING:
            return 'fast_stopping'
        if state_value == StateMachine.EST_HOMING:
            return 'homing'
        if state_value == StateMachine.EST_POSITIONING:
            return 'positioning'
        if state_value == StateMachine.EST_MOV_TO_VEL:
            return 'mov_to_vel'
        if state_value == StateMachine.EST_MOV_TO_POS:
            return 'mov_to_pos'
        if state_value == StateMachine.EST_MOV_TO_POS_LOAD:
            return 'mov_to_pos_load'
        if state_value == StateMachine.EST_MOV_TO_FZA:
            return 'mov_to_fza'
        if state_value == StateMachine.EST_SLAVE:
            return 'slave'


class AcdpAxisMovementsMovEjeDataFlagsBits:
    slave       = 1 << 0
    sync_on     = 1 << 1
    em_stop     = 1 << 2


class AcdpAxisMovementsMovEjeDataSincroMedDrv(BaseStructure):
    _fields_ = [
        ('modulo', c_float),
        ('pos_dif', c_float),
        ('vel_dif', c_float)
    ]


class AcdpAxisMovementsMovEjeDataSincro(BaseStructure):
    _fields_ = [
        ('rel_master', c_float),
        ('set_point_dif', c_float),

        ('med_drv', AcdpAxisMovementsMovEjeDataSincroMedDrv)
    ]


class AcdpAxisMovementsMovEjeData(BaseStructure):
    _fields_ = [
        # ('flags', AcdpAxisMovementsMovEjeDataFlags),
        ('flags', c_uint32),
        ('maq_est', AcdpAxisMovementsMovEjeDataMaqEst),

        ('mov_pos', AcdpAxisMovementsMovPosData),
        ('sincro', AcdpAxisMovementsMovEjeDataSincro),  # Informacion sincronismo
        ('mov_fza', AcdpAxisMovementsMovFzaData),

        ('drive', AcdpDrvCmdData)
    ]


class AcdpAxisMovementsMovEje(BaseStructure):
    _fields_ = [
        # Configuracion Movimiento Eje
        ('config', AcdpAxisMovementsMovEjeConfig),

        # Datos Movimiento Eje
        ('data', AcdpAxisMovementsMovEjeData)
    ]


class AcdpAxisMovements(BaseStructure):
    _fields_ = [
        # Movimiento Posicion
        ('mov_pos', AcdpAxisMovementsMovPos),

        # Movimiento Fuerza
        ('mov_fza', AcdpAxisMovementsMovFza),

        # Movimiento Eje
        ('mov_eje', AcdpAxisMovementsMovEje)
    ]


class AcdpPcDataFlagsBits(BaseStructure):
    _fields_ = [
        ('cmd_toggle', c_int, 1),     # 0
        ('cmd_received', c_int, 1)    # 1
    ]


# class AcdpPcDataFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpPcDataFlagsBits)
#     ]


class AcdpPcDataCtrlFlagsBits(BaseStructure):
    _fields_ = [
        ('ctrl_ok', c_int, 1),      # 0
        ('running', c_int, 1),      # 1
        ('em_stop', c_int, 1),      # 2
        ('fast_stop', c_int, 1),    # 3
    ]


# class AcdpPcDataCtrlFlags(BaseUnion):
#     _fields_ = [
#         ('all', c_uint32),
#         ('bits', AcdpPcDataCtrlFlagsBits)
#     ]


class AcdpPcDataCtrlLocIODI16Pins(BaseStructure):
    _fields_ = [
        ('run_test', c_int, 1),
        ('move_up_crossbar', c_int, 1),
        ('move_down_crossbar', c_int, 1),
        ('move_to_start', c_int, 1)
    ]


# class AcdpPcDataCtrlLocIODI16(BaseUnion):
#     _fields_ = [
#         ('all', c_uint16),
#         ('pins', AcdpPcDataCtrlLocIODI16Pins)
#     ]


class AcdpPcDataCtrlLocIODO16Pins(BaseStructure):
    _fields_ = [
        ('test_cancelled_ind', c_int, 1),
        ('test_out_of_tolerance_ind', c_int, 1),
        ('test_ok_ind', c_int, 1),
        ('test_running_ind', c_int, 1)
    ]


# class AcdpPcDataCtrlLocIODO16(BaseUnion):
#     _fields_ = [
#         ('all', c_uint16),
#         ('pins', AcdpPcDataCtrlLocIODO16Pins)
#     ]


class AcdpPcDataCtrlLocIO(BaseStructure):
    _fields_ = [
        # ('di16', AcdpPcDataCtrlLocIODI16),
        ('di16', c_uint16),
        # ('do16', AcdpPcDataCtrlLocIODO16)
        ('do16', c_uint16)
    ]


class AcdpPcDataCtrlRemIODI16Enums:     # Remote Digital Inputs
    ID_X_DI_0    = 0
    ID_X_DI_1    = 1
    CANT_DIS   = 2


class AcdpPcDataCtrlRemIODI16Inputs(BaseStructure):
    _fields_ = [
        ('i0', c_int, 1)  # 0
    ]


# class AcdpPcDataCtrlRemIODI16(BaseUnion):
#     _fields_ = [
#         ('all', c_uint16),
#         ('di', AcdpPcDataCtrlRemIODI16Inputs)
#     ]


class AcdpPcDataCtrlRemIODO16Enums:     # Remote Digital Outputs
    ID_X_DO_0   = 0
    ID_X_DO_1   = 1
    CANT_DOS    = 2


class AcdpPcDataCtrlRemIODO16DO(BaseStructure):
    _fields_ = [
        ('o0', c_int, 1)  # 0
    ]


# class AcdpPcDataCtrlRemIODO16(BaseUnion):
#     _fields_ = [
#         ('all', c_uint16),
#         ('do', AcdpPcDataCtrlRemIODO16DO)
#     ]


class AcdpPcDataCtrlRemIODI16Array(ctypes.Array):
    _length_ = AcdpPcDataCtrlRemIODI16Enums.CANT_DIS
    # _type_ = AcdpPcDataCtrlRemIODI16
    _type_ = c_uint16


class AcdpPcDataCtrlRemIODO16Array(ctypes.Array):
    _length_ = AcdpPcDataCtrlRemIODO16Enums.CANT_DOS
    # _type_ = AcdpPcDataCtrlRemIODO16
    _type_ = c_uint16


class AcdpPcDataCtrlRemIO(BaseStructure):
    _fields_ = [
        # ('di16', AcdpPcDataCtrlRemIODI16Array),
        # ('do16', AcdpPcDataCtrlRemIODO16Array)
        ('di16', c_uint16 * AcdpPcDataCtrlRemIODI16Enums.CANT_DIS),
        ('do16', c_uint16 * AcdpPcDataCtrlRemIODO16Enums.CANT_DOS)
    ]


class AcdpAxisMovementsMovEjeDataArray(ctypes.Array):
    _length_ = AcdpAxisMovementEnums.CANT_EJES
    _type_ = AcdpAxisMovementsMovEjeData


class AcdpPcDataCtrl(BaseStructure):
    _fields_ = [
        # ('flags', AcdpPcDataCtrlFlags),
        ('flags', c_uint32),
        ('loc_io', AcdpPcDataCtrlLocIO),    # Local Inputs/Outpus
        ('rem_io', AcdpPcDataCtrlRemIO),    # Remote Inputs/Outputs

        ('eje', AcdpAxisMovementsMovEjeDataArray)
    ]


class AcdpPcData(BaseStructure):
    _fields_ = [
        ('flags', c_uint32),
        ('ctrl', AcdpPcDataCtrl)
    ]


class AcdpPc(BaseStructure):
    _fields_ = [
        ('data', AcdpPcData)
    ]
    
    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.set_states()

    def store_from_raw(self, raw_values):
        super().store_from_raw(raw_values)
        # self.set_states()
    
    def set_states(self):
        # Command flags
        self.cmd_toggle = self.data.flags
        self.cmd_received = self.data.flags

        # Control flags
        self.ctrl_ok = self.data.ctrl.flags
        self.running = self.data.ctrl.flags
        self.em_stop = self.data.ctrl.flags
        self.fast_stop = self.data.ctrl.flags

        # Local digital inpunts/outputs
        self.run_test = self.data.ctrl.loc_io.di16
        self.move_up_crossbar = self.data.ctrl.loc_io.di16
        self.move_down_crossbar = self.data.ctrl.loc_io.di16
        self.move_to_start = self.data.ctrl.loc_io.di16
        
        self.test_cancelled_ind = self.data.ctrl.loc_io.do16
        self.test_out_of_tolerance_ind = self.data.ctrl.loc_io.do16
        self.test_ok_ind = self.data.ctrl.loc_io.do16
        self.test_running_ind = self.data.ctrl.loc_io.do16

        # Remote digital inputs/outputs
        self.rem_di = []
        for i in range(self.data.ctrl.rem_io.di16._length_):
            self.rem_di.append(self.data.ctrl.rem_io.di16[i])
        
        self.rem_do = []
        for i in range(self.data.ctrl.rem_io.do16._length_):
            self.rem_do.append(self.data.ctrl.rem_io.do16[i])

        # Axis
        self.axis = []
        for i in range(self.data.ctrl.eje._length_):
            axis = self.get_axis(i)
            self.axis.append({
                # Flags
                'flags': axis.flags,
                
                # States machine
                'flags_fin': axis.maq_est.flags_fin,
                'state': axis.maq_est.estado,

                # Position movement
                'pos_flags': axis.mov_pos.flags,
                'pos_homing_states': axis.mov_pos.homing.estado,
                'pos_fil': axis.mov_pos.med_drv.pos_fil,
                'vel_fil': axis.mov_pos.med_drv.vel_fil,
                # Load
                'load_pos_fil': axis.mov_pos.med_load.pos_fil,
                'load_vel_fil': axis.mov_pos.med_load.vel_fil,
            })
    
    def get_states(self):
        states = {}
        # Command flags
        states['cmd_toggle'] = self.data.flags
        states['cmd_received'] = self.data.flags

        # Control flags
        states['ctrl_ok'] = self.data.ctrl.flags
        states['running'] = self.data.ctrl.flags
        states['em_stop'] = self.data.ctrl.flags
        states['fast_stop'] = self.data.ctrl.flags

        # Local digital inpunts/outputs
        states['run_test'] = self.data.ctrl.loc_io.di16
        states['move_up_crossbar'] = self.data.ctrl.loc_io.di16
        states['move_down_crossbar'] = self.data.ctrl.loc_io.di16
        states['move_to_start'] = self.data.ctrl.loc_io.di16
        
        states['test_cancelled_ind'] = self.data.ctrl.loc_io.do16
        states['test_out_of_tolerance_ind'] = self.data.ctrl.loc_io.do16
        states['test_ok_ind'] = self.data.ctrl.loc_io.do16
        states['test_running_ind'] = self.data.ctrl.loc_io.do16

        # Remote digital inputs/outputs
        rem_di = []
        rem_do = []

        for i in range(self.data.ctrl.rem_io.di16._length_):
            rem_di.append(self.data.ctrl.rem_io.di16[i])
        
        for i in range(self.data.ctrl.rem_io.do16._length_):
            rem_do.append(self.data.ctrl.rem_io.do16[i])

        states['rem_di'] = rem_di
        states['rem_do'] = rem_do

        # Axis
        axis_arr = []
        for i in range(self.data.ctrl.eje._length_):
            axis = self.get_axis(i)
            axis_arr.append({
                # Flags
                'flags': axis.flags,
                'em_stop_flag': axis.flags,
                'disabled_flag': axis.flags,
                'sync_on_flag': axis.flags,
                
                # States machine
                'flags_fin': axis.maq_est.flags_fin,
                'state': axis.maq_est.estado,

                # Position movement
                'pos_flags': axis.mov_pos.flags,
                'pos_homing_states': axis.mov_pos.homing.estado,
                'pos_fil': axis.mov_pos.med_drv.pos_fil,
                'vel_fil': axis.mov_pos.med_drv.vel_fil,
                'torque': axis.mov_pos_med_drv.torque_fil
            })
        states['axis'] = axis_arr
        return states

    def get_load_axis(self):
        return self.data.ctrl.eje[AcdpAxisMovementEnums.ID_X_EJE_CARGA]
    
    def get_turn_axis(self):
        return self.data.ctrl.eje[AcdpAxisMovementEnums.ID_X_EJE_GIRO]
    
    def get_lineal_axis(self):
        return self.data.ctrl.eje[AcdpAxisMovementEnums.ID_X_EJE_AVANCE]
    
    def get_axis(self, axis):
        if axis == AcdpAxisMovementEnums.ID_X_EJE_CARGA:
            return self.get_load_axis()

        elif axis == AcdpAxisMovementEnums.ID_X_EJE_GIRO:
            return self.get_turn_axis()
        
        elif axis == AcdpAxisMovementEnums.ID_X_EJE_AVANCE:
            return self.get_lineal_axis()
        
        else:
            print("Eje no encontrado")
            return False
    
    def get_axis_states(self, axis):
        states = self.get_axis(axis).maq_est
        return states
    
    def get_axis_flags(self, axis):
        flags = self.get_axis(axis).flags
        return flags