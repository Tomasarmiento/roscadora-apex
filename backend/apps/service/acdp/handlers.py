from datetime import datetime
from apps.service.acdp.acdp import ACDP_VERSION, ACDP_UDP_PORT, ACDP_IP_ADDR
from apps.service.acdp.acdp import AcdpHeader
from apps.service.acdp.messages_app import AcdpPc, AcdpMsgCodes, AcdpMsgParams, AcdpAxisMovementEnums
from apps.service.acdp.messages_base import AcdpMsgCmdParam, BaseStructure, AcdpMsgCxn, AcdpMsgCmd, AcdpMsgCmdParamSetZeroDrvFbk, AcdpMsgCmd, AcdpMsgData, AcdpMsgCfgSet
from apps.service.acdp import messages_base as msg_base


class AcdpMessage(BaseStructure):
    last_rx_data = AcdpPc()
    last_rx_header = AcdpHeader()

    _fields_ = [
        ('header', AcdpHeader),
        ('data', AcdpPc)
    ]

    def get_msg_id(self):
        return self.header.ctrl.msg_id

    def store_from_raw(self, raw_values):
        bytes_len = len(raw_values)
        if bytes_len == self.header.get_bytes_size():
            self.header.store_from_raw(raw_values)
            AcdpMessage.last_rx_header = self.header
        else:
            super().store_from_raw(raw_values)
            AcdpMessage.last_rx_data = self.data
    
    def process_rx_msg(self, addr=(ACDP_IP_ADDR, ACDP_UDP_PORT), transport=None):
        msg_code = self.header.get_msg_code()
        update_front = True
        
        if msg_code == AcdpMsgCxn.CD_ECHO_REQ:
            tx_header = build_msg(AcdpMsgCxn.CD_ECHO_REPLY)
            transport.sendto(tx_header.pacself(), addr)
            update_front = False
        
        else:
            msg = None
            
            if msg_code != AcdpMsgData.CD_ALL:
                msg = 'RX MESSAGE ID:' + str(self.header.get_msg_id())

            elif msg_code == AcdpMsgData.CD_ALL:
                last_data_flags = AcdpMessagesControl.last_rx_msg.data.data.flags
                new_data_flags = self.data.data.flags
                if last_data_flags != new_data_flags:
                    if new_data_flags == ~last_data_flags:
                        print('Comando recibido. ID:', self.header.get_msg_id())
                    # print('old:', f'{last_data_flags:03b}')
                    # print('new:', f'{new_data_flags:03b}')

            if msg_code == AcdpMsgCmd.CD_REJECTED:
                msg = 'RX CODE - Comando rechazado'
            
            elif msg_code == AcdpMsgCxn.CD_ECHO_TIMEOUT:
                msg = 'RX CODE - ECHO TIMEOUT'

            elif msg_code == AcdpMsgCfgSet.CD_SUCCESSFUL:
                msg = 'RX CODE - Configuración exitosa'
            
            if msg:
                AcdpMessagesControl.log_messages.append(msg)
            
        return update_front


class AcdpMessagesControl:
    last_rx_msg = AcdpMessage()
    log_messages = []

    def get_last_msg_id():
        return AcdpMessagesControl.last_rx_msg.header.get_msg_id()
    
    def get_last_msg_toggle_flags():
        return AcdpMessagesControl.last_rx_msg.data.data.flags


def build_msg(code, host_ip="192.168.1.20", dest_ip=ACDP_IP_ADDR, params={}, *args, **kwargs):

    tx_header = AcdpHeader()
    tx_data = None

    tx_header.ctrl.msg_code = code

    tx_header.ctrl.msg_code = code
    tx_header.version = ACDP_VERSION
    tx_header.channel = 0
    tx_header.ip_addr.store_from_string(host_ip)
    tx_header.dest_addr.store_from_string(dest_ip)

    tx_header.ctrl.device_type = 0
    tx_header.ctrl.firmware_version = 0
    tx_header.ctrl.object = 0
    tx_header.ctrl.flags = 0
    tx_header.ctrl.timestamp = 0

    if code == AcdpMsgCxn.CD_FORCE_CONNECT or code == AcdpMsgCxn.CD_DISCONNECT \
        or code == AcdpMsgCxn.CD_CONNECT or code == AcdpMsgCxn.CD_ECHO_REPLY:     # open/close/force connection / echo reply
        tx_header.ctrl.msg_id = 0
        tx_header.ctrl.data_len8 = 0
    
    elif code == AcdpMsgCmd.CD_STOP_ALL:
        pass
    
    elif code == AcdpMsgCodes.Cmd.Cd_MovEje_RunZeroing:
        axis = kwargs['eje']
        tx_header.ctrl.object = axis
    
    else:
        tx_header.set_msg_id(msg_id=kwargs['msg_id'])
        param = None

        if code == AcdpMsgCodes.Cmd.Cd_RemDO_Set or code == AcdpMsgCodes.Cmd.Cd_LocDO_Set:
            if code == AcdpMsgCodes.Cmd.Cd_RemDO_Set:
                tx_header.ctrl.object = kwargs['group']
            mask = kwargs['mask']
            out_value = kwargs['out_value']
            param = DataBuilder.build_set_do(mask, out_value)

        else:
            tx_header.ctrl.object = kwargs['eje']

            if code == AcdpMsgCodes.Cmd.Cd_MovEje_SyncOn:
                if params:
                    paso = params['paso']
                else:
                    paso = kwargs['paso']
                param = DataBuilder.build_sync_on_data(paso)
            
            elif code == AcdpMsgCodes.Cmd.Cd_MovEje_Stop:
                tx_header.set_msg_id(msg_id=kwargs['msg_id'])
                
            elif code == AcdpMsgCodes.Cmd.Cd_MovEje_MovToVel:
                if params:
                    ref = params['ref']
                else:
                    ref = kwargs['ref']
                param = DataBuilder.build_mov_to_vel_data(ref)

            elif code == AcdpMsgCodes.Cmd.Cd_MovEje_MovToPos:
                if params:
                    ref = params['ref']
                    ref_rate = params['ref_rate']
                else:
                    ref = kwargs['ref']
                    ref_rate = kwargs['ref_rate']
                print('ref:', ref, 'ref_rate', ref_rate)
                param =  DataBuilder.build_mov_to_pos_data(ref, ref_rate)
                # print(param)
                print("REF:", param.reference,"REF_RATE:", param.ref_rate)

            elif code == AcdpMsgCodes.Cmd.Cd_MovEje_MovToPos_Yield:
                if params:
                    ref = params['ref']
                    ref_rate = params['ref_rate']
                    yield_vals = params['yield_vals']
                else:
                    ref = kwargs['ref']
                    ref_rate = kwargs['ref_rate']
                    yield_vals = kwargs['yield_vals']
                param =  DataBuilder.build_mov_to_pos_yield_data(ref, ref_rate, yield_vals)

            elif code == AcdpMsgCodes.Cmd.Cd_MovEje_MovToPosLoad:
                if params:
                    ref = params['ref']
                else:
                    ref = kwargs['ref']
                param =  DataBuilder.build_mov_to_pos_load_data(ref)

            elif code == AcdpMsgCodes.Cmd.Cd_MovEje_MovToPosLoad_Yield:
                if params:
                    ref = params['ref']
                    ref_rate = params['ref_rate']
                    yield_vals = params['yield_vals']
                else:
                    ref = kwargs['ref']
                    ref_rate = kwargs['ref_rate']
                    yield_vals = kwargs['yield_vals']
                param =  DataBuilder.build_mov_to_pos_load_yield_data(ref, ref_rate, yield_vals)

            elif code == AcdpMsgCodes.Cmd.Cd_MovEje_MovToFza:
                if params:
                    ref = params['ref']
                    ref_rate = params['ref_rate']
                    vel_uns_max = params['vel_uns_max']
                else:
                    ref = kwargs['ref']
                    ref_rate = kwargs['ref_rate']
                    vel_uns_max = kwargs['vel_uns_max']
                param =  DataBuilder.build_mov_to_fza_data(ref, ref_rate, vel_uns_max)

            elif code == AcdpMsgCodes.Cmd.Cd_MovEje_MovToFza_Yield:
                if params:
                    ref = params['ref']
                    ref_rate = params['ref_rate']
                    yield_vals = params['yield_vals']
                    vel_uns_max = params['vel_uns_max']
                else:
                    ref = kwargs['ref']
                    ref_rate = kwargs['ref_rate']
                    yield_vals = kwargs['yield_vals']
                    vel_uns_max = kwargs['vel_uns_max']
                param =  DataBuilder.build_mov_to_fza_yield_data(ref, ref_rate, yield_vals, vel_uns_max)
            
            elif code == AcdpMsgCmd.CD_DRV_FBK_SET_ZERO_ABSOLUTELY:
                if params:
                    zero = params['zero']
                else:
                    zero = kwargs['zero']
                param = DataBuilder.build_drv_set_zero_abs(zero)
                
            elif code == AcdpMsgCodes.Cmd.Cd_MovEje_PowerOn or code == AcdpMsgCodes.Cmd.Cd_MovEje_PowerOff\
                or code == AcdpMsgCodes.Cmd.Cd_MovEje_ExitSafeMode or code == AcdpMsgCodes.Cmd.Cd_MovEje_EnterSafeMode\
                    or code == AcdpMsgCodes.Cmd.Cd_MovEje_SyncOff:
                pass
            
        if param:
            tx_data = param
            tx_header.set_data_len(param.get_bytes_size())
            return tx_header, tx_data
    return tx_header


class DataBuilder:
    
    def build_sync_on_data(paso):
        param = AcdpMsgParams().sync_on
        setattr(param, 'paso_eje_lineal', paso)
        return param

    def build_yield_data(yield_vals):
        factor_limite_elastico = yield_vals['factor_limite_elastico']
        correccion_pendiente = yield_vals['correccion_pendiente']
        cedencia = yield_vals['cedencia']
        param = getattr(AcdpMsgParams(), 'yield')
        setattr(param, 'factor_limite_elastico', factor_limite_elastico)
        setattr(param, 'correccion_pendiente', correccion_pendiente)
        setattr(param, 'cedencia', cedencia)
        return param
    
    def build_mov_to_vel_data(ref):
        param = AcdpMsgParams().mov_to_vel
        param.reference = ref
        return param

    def build_mov_to_pos_data(ref, ref_rate):
        param = AcdpMsgParams().mov_to_pos
        param.reference = ref
        param.ref_rate = ref_rate
        return param

    def build_mov_to_pos_yield_data(ref, ref_rate, yield_vals):
        param = AcdpMsgParams().mov_to_pos_load_yield
        setattr(param, 'mov_to_pos', DataBuilder.build_mov_to_pos(ref, ref_rate))
        setattr(param, 'yield', DataBuilder.build_yield_data(yield_vals))
        return param

    def build_mov_to_pos_load_data(ref):
        param = AcdpMsgParams().mov_to_pos_load
        param.reference = ref
        return param

    def build_mov_to_pos_load_yield_data(ref, yield_vals):
        param = AcdpMsgParams().mov_to_pos_load_yield
        setattr(param, 'mov_to_pos_load', DataBuilder.build_mov_to_pos_load(ref))
        setattr(param, 'yield', DataBuilder.build_yield_data(yield_vals))
        return param

    def build_mov_to_fza_data(ref, ref_rate, vel_uns_max=0.0):        # REVISAR valor de vel_uns_max
        param = AcdpMsgParams().mov_to_fza
        setattr(param, 'reference', ref)
        setattr(param, 'ref_rate', ref_rate)
        setattr(param, 'vel_uns_max', vel_uns_max)
        return param

    def build_mov_to_fza_yield_data(ref, ref_rate, yield_vals, vel_uns_max=0.0):        # REVISAR valor de vel_uns_max
        param = AcdpMsgParams().mov_to_fza_yield
        setattr(param, 'mov_to_fza', DataBuilder.build_mov_to_fza_data(ref, ref_rate, vel_uns_max))
        setattr(param, 'yield', DataBuilder.build_yield_data(yield_vals))
        return param
    
    def build_set_do(mask, out_value):
        param = AcdpMsgParams().do_set
        setattr(param, 'value', out_value)
        setattr(param, 'mask', mask)
        return param
    
    def build_set_multiple_do(value, mask):
        param = AcdpMsgParams().do_set
        setattr(param, 'mask', mask)
        setattr(param, 'value', value)
        return param
    
    def build_drv_set_zero_abs(zero):
        param = AcdpMsgCmdParamSetZeroDrvFbk()
        setattr(param, 'zero', zero)
        return param