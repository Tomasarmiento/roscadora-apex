from distutils import command
from distutils.log import error
import json
import time

from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

import apps.service.acdp.handlers as service_handlers
from apps.service.acdp.messages_app import AcdpAxisMovementEnums, StateMachine
from apps.service.acdp.messages_base import AcdpMsgCmd

from apps.service.api.variables import Commands
from apps.ws.utils.handlers import send_message
from apps.ws.utils.functions import get_ch_info
from apps.ws.utils.variables import MicroState
from apps.ws.models import ChannelInfo

from apps.control.utils.variables import COMMAND_DEFAULT_VALUES
from apps.control.utils.routines import RoutineHandler, MasterHandler
from apps.control.utils.functions import check_init_conditions_neumatic_test,check_init_conditions_neumatic_load,check_init_conditions_neumatic_unload,check_init_conditions_neumatic_cabezal
from apps.control.utils import variables as ctrl_vars
from apps.control.utils import functions as ctrl_func
from apps.control.models import RoutineInfo

from apps.parameters.utils.functions import update_roscado_params
from apps.parameters.models import Parameter
from apps.parameters.utils import variables as param_vars


@csrf_exempt
def manual_lineal(request):

    post_req = request.POST
    print(post_req)
    ch_info = get_ch_info(ChannelInfo, 'micro')
    req_data = []
    params = {}
    MicroState.msg_id += 1
    msg_id = MicroState.msg_id
    error_flag = False
    
    for item in post_req.items():   # Item is in (key, value) format
        req_data.append(item)

    command = int(req_data[0][1])
    axis = int(req_data[1][1])
    print("axis", axis)
    ref_rate = None
    print("ref rate", ref_rate)
    print(params)
    if command != Commands.stop:
        for item in req_data[2:]:
            key = item[0]
            value = item[1]
            if key != 'abs':
                params[key] = float(value)
            else:
                params[key] = bool(value)
        
        if axis == AcdpAxisMovementEnums.ID_X_EJE_AVANCE:
            if 'ref_rate' in params.keys() and params['ref_rate'] != 0 :
                ref_rate = params['ref_rate']
            else:
                ref_rate = COMMAND_DEFAULT_VALUES['vel_avance']

        elif axis == AcdpAxisMovementEnums.ID_X_EJE_CARGA:
            if 'ref_rate' in params.keys() and params['ref_rate'] != 0 :
                ref_rate = params['ref_rate']
            else:
                ref_rate = COMMAND_DEFAULT_VALUES['vel_carga']
                
        if ref_rate:
            params['ref_rate'] = ref_rate
            if not params['abs']:
                pass

        #ACA CHECKEA
        if MicroState.neumatic_safe_mode == True:
            if ctrl_func.check_init_conditions_motores(axis):
                print('\nError en condiciones iniciales de EJE')
                error_flag = True
                err_msg = 'Error en condiciones iniciales de EJE'
                MicroState.err_messages.append(err_msg)
                for err in ctrl_func.check_init_conditions_motores(axis):
                    MicroState.err_messages.append(err)
                    print(err)

        if error_flag != True: 
            header, data = service_handlers.build_msg(command, params=params, msg_id=msg_id, eje=axis)


    else:
        header = service_handlers.build_msg(command, msg_id=msg_id, eje=axis)
        data = None

    if ch_info:
        if error_flag != True: 
            send_message(header, ch_info, data)
    
    return JsonResponse({})


@method_decorator(csrf_exempt, name='dispatch')
class ManualPneumatic(View):

    def post(self, request):
        post_req = request.POST
        error_flag = False

        
        req_data = []
        
        for item in post_req.items():   # Item is in (key, value) format
            req_data.append(item)

        if req_data[0][1] != 'exit_safe_mode' and req_data[0][1] != 'enter_safe_mode':
            command = int(req_data[0][1])
            menu = req_data[1][1]
            name = req_data[2][1]
            btn = req_data[3][1]
            send_msg = True
            print("COMANDO",command)
            print("MENU",menu)
            print('NOMBRE:', name)
            print('BOTON:', btn)
        else:
            command = req_data[0][1]
            menu = req_data[1][1]
            name = req_data[2][1]
            btn = req_data[3][1]
            send_msg = True
            print("COMANDO",command)
            print("MENU",menu)
            print('NOMBRE:', name)
            print('BOTON:', btn)


        if menu == 'carga':
            if name == 'horizontalCarga':
                keys = ['contraer_puntera_carga', 'expandir_puntera_carga']
                group = 0
                if btn == 'On':
                    bool_value_1  = 0
                    bool_value_2  = 1
                
                else:
                    bool_value_1  = 1
                    bool_value_2  = 0
                    
                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_load('contraer_puntera_carga'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_load('contraer_puntera_carga'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    if bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_load('expandir_puntera_carga'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_load('expandir_puntera_carga'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False

            elif name == 'verticalCarga':
                key = 'expandir_vertical_carga'
                group = 0
                if btn == 'On':
                    bool_value  = 1
                
                else:
                    bool_value  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if check_init_conditions_neumatic_load('expandir_vertical_carga'):
                        print('\nError en condiciones iniciales de carga')
                        err_msg = 'Error en condiciones iniciales de carga'
                        MicroState.err_messages.append(err_msg)
                        for err in check_init_conditions_neumatic_load('expandir_vertical_carga'):
                            MicroState.err_messages.append(err)
                            print(err)
                        error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, key, group, bool_value)
                    send_msg = False

            elif name == 'BoquillaCarga':
                key = 'contraer_boquilla_carga'
                group = 0
                if btn == 'On':
                    bool_value  = 1
                
                else:
                    bool_value  = 0
                #chekear aca gripper de arriba

                if MicroState.neumatic_safe_mode == True:
                    if check_init_conditions_neumatic_load('contraer_boquilla_carga'):
                        print('\nError en condiciones iniciales de carga')
                        err_msg = 'Error en condiciones iniciales de carga'
                        MicroState.err_messages.append(err_msg)
                        for err in check_init_conditions_neumatic_load('contraer_boquilla_carga'):
                            MicroState.err_messages.append(err)
                            print(err)
                        error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, key, group, bool_value)
                    send_msg = False

            elif name =='giroCarga':
                keys = ['contraer_brazo_cargador', 'expandir_brazo_cargador']
                group = 0
                if btn == 'On':
                    bool_value_1  = 1
                    bool_value_2  = 0
                
                else:
                    bool_value_1  = 0
                    bool_value_2  = 1


                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_load('contraer_brazo_cargador'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_load('contraer_brazo_cargador'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    if bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_load('expandir_brazo_cargador'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_load('expandir_brazo_cargador'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False
                        
        elif menu == 'descarga':
            if name == 'horizontalDesc':
                keys = ['contraer_puntera_descarga', 'expandir_puntera_descarga']
                group = 0
                if btn == 'On':
                    bool_value_1  = 0
                    bool_value_2  = 1
                
                else:
                    bool_value_1  = 1
                    bool_value_2  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_unload('contraer_puntera_descarga'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_unload('contraer_puntera_descarga'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    if bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_unload('expandir_puntera_descarga'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_unload('expandir_puntera_descarga'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False
                
            elif name == 'giroDesc':
                keys = ['contraer_brazo_descargador', 'expandir_brazo_descargador']
                group = 0
                if btn == 'On':
                    bool_value_1  = 1
                    bool_value_2  = 0
                
                else:
                    bool_value_1  = 0
                    bool_value_2  = 1
                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_unload('contraer_brazo_descargador'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_unload('contraer_brazo_descargador'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    if bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_unload('expandir_brazo_descargador'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_unload('expandir_brazo_descargador'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False

            elif name == 'horizontalGr':
                keys = ['expandir_horiz_pinza_desc','contraer_horiz_pinza_desc']
                group = 1
                if btn == 'On':
                    bool_value_1  = 1
                    bool_value_2  = 0
                
                else:
                    bool_value_1  = 0
                    bool_value_2  = 1
                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_unload('expandir_horiz_pinza_desc'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_unload('expandir_horiz_pinza_desc'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    if bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_unload('contraer_horiz_pinza_desc'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_unload('contraer_horiz_pinza_desc'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False

            elif name == 'verticalGr':
                keys = ['expandir_vert_pinza_desc','contraer_vert_pinza_desc']
                group = 1
                if btn == 'On':
                    bool_value_1  = 1
                    bool_value_2  = 0
                
                else:
                    bool_value_1  = 0
                    bool_value_2  = 1
                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_unload('expandir_vert_pinza_desc'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_unload('expandir_vert_pinza_desc'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    if bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_unload('contraer_vert_pinza_desc'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_unload('contraer_vert_pinza_desc'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False

            elif name == 'BoquillaDesc':
                key = 'contraer_boquilla_descarga'
                group = 0
                if btn == 'On':
                    bool_value  = 1
                
                else:
                    bool_value  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if check_init_conditions_neumatic_unload('contraer_boquilla_descarga'):
                        print('\nError en condiciones iniciales de carga')
                        err_msg = 'Error en condiciones iniciales de carga'
                        MicroState.err_messages.append(err_msg)
                        for err in check_init_conditions_neumatic_unload('contraer_boquilla_descarga'):
                            MicroState.err_messages.append(err)
                            print(err)
                        error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, key, group, bool_value)
                    send_msg = False

            elif name == 'gripperDesc':
                keys = ['cerrar_pinza_descargadora', 'abrir_pinza_descargadora']
                group = 0
                if btn == 'On':
                    bool_value_1  = 1
                    bool_value_2  = 0
                
                else:
                    bool_value_1  = 0
                    bool_value_2  = 1
                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_unload('cerrar_pinza_descargadora'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_unload('cerrar_pinza_descargadora'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    if bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_unload('abrir_pinza_descargadora'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_unload('abrir_pinza_descargadora'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False
        
        elif menu == 'cabezal':
            if name == 'cerramiento':
                key = 'expandir_cerramiento_roscado'
                group = 0
                if btn == 'On':
                    bool_value  = 1
                
                else:
                    bool_value  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if check_init_conditions_neumatic_cabezal('expandir_cerramiento_roscado'):
                        print('\nError en condiciones iniciales de carga')
                        err_msg = 'Error en condiciones iniciales de carga'
                        MicroState.err_messages.append(err_msg)
                        for err in check_init_conditions_neumatic_cabezal('expandir_cerramiento_roscado'):
                            MicroState.err_messages.append(err)
                            print(err)
                        error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, key, group, bool_value)
                    send_msg = False
                    
            elif name == 'clampeo':
                keys = ['contraer_clampeo_plato', 'expandir_clampeo_plato']
                group = 1
                if btn == 'On':
                    bool_value_1  = 0
                    bool_value_2  = 1
                
                else:
                    bool_value_1  = 1
                    bool_value_2  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_cabezal('contraer_clampeo_plato'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_cabezal('contraer_clampeo_plato'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_cabezal('expandir_clampeo_plato'):
                            print('\nError en condiciones iniciales de carga')
                            err_msg = 'Error en condiciones iniciales de carga'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_cabezal('expandir_clampeo_plato'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False

            elif name == 'presion':
                key = 'presurizar'
                group = 1
                if btn == 'On':
                    bool_value  = 1
                
                else:
                    bool_value  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if check_init_conditions_neumatic_cabezal('presurizar'):
                        print('\nError en condiciones iniciales de carga')
                        err_msg = 'Error en condiciones iniciales de carga'
                        MicroState.err_messages.append(err_msg)
                        for err in check_init_conditions_neumatic_cabezal('presurizar'):
                            MicroState.err_messages.append(err)
                            print(err)
                        error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, key, group, bool_value)
                    send_msg = False

            elif name == 'boquilla1':
                keys = ['cerrar_boquilla_1', 'abrir_boquilla_1']
                group = 1
                if btn == 'On':
                    bool_value_1  = 1
                    bool_value_2  = 0
                    print(btn)
                
                elif btn == 'Off':
                    bool_value_1  = 0
                    bool_value_2  = 1
                
                else:
                    bool_value_1  = 0
                    bool_value_2  = 0
                
                # self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                # send_msg = False
                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_cabezal('cerrar_boquilla_1'):
                            print('\nError en condiciones iniciales de cabezal')
                            err_msg = 'Error en condiciones iniciales de cabezal'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_cabezal('cerrar_boquilla_1'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    elif bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_cabezal('abrir_boquilla_1'):
                            print('\nError en condiciones iniciales de cabezal')
                            err_msg = 'Error en condiciones iniciales de cabezal'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_cabezal('abrir_boquilla_1'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    else:
                        self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                        send_msg = False
                        error_flag = True #Para que no mande 2 veces el comando
                        
                if error_flag != True : #and (bool_value_1 !=0 or bool_value_2 != 0)
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False

            elif name == 'boquilla2':
                keys = ['cerrar_boquilla_2', 'abrir_boquilla_2']
                group = 1
                if btn == 'On':
                    bool_value_1  = 1
                    bool_value_2  = 0
                
                elif btn == 'Off':
                    bool_value_1  = 0
                    bool_value_2  = 1
                
                else:
                    bool_value_1  = 0
                    bool_value_2  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_cabezal('cerrar_boquilla_2'):
                            print('\nError en condiciones iniciales de cabezal')
                            err_msg = 'Error en condiciones iniciales de cabezal'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_cabezal('cerrar_boquilla_2'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    elif bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_cabezal('abrir_boquilla_2'):
                            print('\nError en condiciones iniciales de cabezal')
                            err_msg = 'Error en condiciones iniciales de cabezal'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_cabezal('abrir_boquilla_2'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    else:
                        self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                        send_msg = False
                        error_flag = True #Para que no mande 2 veces el comando
                        
                if error_flag != True:  #and (bool_value_1 !=0 or bool_value_2 != 0)
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False

            elif name == 'boquilla3':
                keys = ['cerrar_boquilla_3', 'abrir_boquilla_3']
                group = 1
                if btn == 'On':
                    bool_value_1  = 1
                    bool_value_2  = 0
                
                elif btn == 'Off':
                    bool_value_1  = 0
                    bool_value_2  = 1
                
                else:
                    bool_value_1  = 0
                    bool_value_2  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if bool_value_1 == 1 and bool_value_2 == 0:
                        if check_init_conditions_neumatic_cabezal('cerrar_boquilla_3'):
                            print('\nError en condiciones iniciales de cabezal')
                            err_msg = 'Error en condiciones iniciales de cabezal'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_cabezal('cerrar_boquilla_3'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    elif bool_value_1 == 0 and bool_value_2 == 1:
                        if check_init_conditions_neumatic_cabezal('abrir_boquilla_3'):
                            print('\nError en condiciones iniciales de cabezal')
                            err_msg = 'Error en condiciones iniciales de cabezal'
                            MicroState.err_messages.append(err_msg)
                            for err in check_init_conditions_neumatic_cabezal('abrir_boquilla_3'):
                                MicroState.err_messages.append(err)
                                print(err)
                            error_flag = True
                    else:
                        self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                        send_msg = False
                        error_flag = True #Para que no mande 2 veces el comando
                        
                        
                if error_flag != True:  #and (bool_value_1 !=0 or bool_value_2 != 0)
                    self.set_rem_do(command, keys[0], group, bool_value_1, keys[1], bool_value_2)
                    send_msg = False

            elif name == 'acoplaSol':
                key = 'expandir_acople_lubric'
                group = 1
                if btn == 'On':
                    bool_value  = 1
                
                else:
                    bool_value  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if check_init_conditions_neumatic_cabezal('expandir_acople_lubric'):
                        print('\nError en condiciones iniciales de carga')
                        err_msg = 'Error en condiciones iniciales de carga'
                        MicroState.err_messages.append(err_msg)
                        for err in check_init_conditions_neumatic_cabezal('expandir_acople_lubric'):
                            MicroState.err_messages.append(err)
                            print(err)
                        error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, key, group, bool_value)
                    send_msg = False

            elif name == 'bombaSol':
                key = 'encender_bomba_soluble'
                group = 1
                if btn == 'On':
                    bool_value  = 1
                
                else:
                    bool_value  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if check_init_conditions_neumatic_cabezal('encender_bomba_soluble'):
                        print('\nError en condiciones iniciales de carga')
                        err_msg = 'Error en condiciones iniciales de carga'
                        MicroState.err_messages.append(err_msg)
                        for err in check_init_conditions_neumatic_cabezal('encender_bomba_soluble'):
                            MicroState.err_messages.append(err)
                            print(err)
                        error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, key, group, bool_value)
                    send_msg = False
            
            elif name == 'bombaHidr':
                key = 'encender_bomba_hidraulica'
                group = 1
                if btn == 'On':
                    bool_value  = 1
                
                else:
                    bool_value  = 0
                
                if MicroState.neumatic_safe_mode == True:
                    if check_init_conditions_neumatic_cabezal('encender_bomba_hidraulica'):
                        print('\nError en condiciones iniciales de carga')
                        err_msg = 'Error en condiciones iniciales de carga'
                        MicroState.err_messages.append(err_msg)
                        for err in check_init_conditions_neumatic_cabezal('encender_bomba_hidraulica'):
                            MicroState.err_messages.append(err)
                            print(err)
                        error_flag = True

                if error_flag != True: 
                    self.set_rem_do(command, key, group, bool_value)
                    send_msg = False

        elif menu == 'exit_safe_mode':
            if command == 'exit_safe_mode':
                if name == 'exit_safe_mode':
                    if btn == 'Off':
                        MicroState.neumatic_safe_mode = False
                        print(MicroState.neumatic_safe_mode)

        elif menu == 'enter_safe_mode':
            if command == 'enter_safe_mode':
                if name == 'enter_safe_mode':
                    if btn == 'On':
                        MicroState.neumatic_safe_mode = True
                        print(MicroState.neumatic_safe_mode)

        if send_msg:
            print("send_msg false")
        #     self.send_message(header, data)
        #     print(header.get_values(), data.get_values())
            
        return JsonResponse({})

    def send_message(self, header, data):
        ch_info = get_ch_info(ChannelInfo, 'micro')
        if ch_info:
            send_message(header, ch_info, data)
            return True
        return False


    def set_rem_do(self, command, key, group, bool_value, second_key=None, second_bool_value=None):
        header, data = ctrl_func.set_rem_do(command, key, group, bool_value)
        if not self.send_message(header, data):
            return False
        if second_key:
            header, data = ctrl_func.set_rem_do(command, second_key, group, second_bool_value)
            return self.send_message(header, data)
        return True

@csrf_exempt
def stop_axis(request):
    post_req = request.POST
    print("la post request",post_req)
    ch_info = get_ch_info(ChannelInfo, 'micro')
    req_data = []
    MicroState.msg_id += 1
    msg_id = MicroState.msg_id
    
    for item in post_req.items():   # Item is in (key, value) format
        req_data.append(item)

    command = int(req_data[0][1])
    axis = int(req_data[1][1])
    header = service_handlers.build_msg(command, msg_id=msg_id, eje=axis)
    print(command, axis)

    if ch_info:
        send_message(header, ch_info)
    
    return JsonResponse({})


@csrf_exempt
def enter_exit_safe(request):
    command = None
    command_2 = None
    ch_info = get_ch_info(ChannelInfo, 'micro')
    axis_count = ctrl_vars.AXIS_IDS['axis_amount']
    for axis_id in range(0, axis_count):
        if MicroState.axis_flags[axis_id]['estado'] != 'safe':
            command = AcdpMsgCmd.CD_ENTER_SAFE_MODE
        else:
            command = AcdpMsgCmd.CD_EXIT_SAFE_MODE
            if axis_id != ctrl_vars.AXIS_IDS['avance']:
                command_2 = Commands.power_off
            else:
                command_2 = None
        msg_id = MicroState.msg_id
        header = service_handlers.build_msg(command, msg_id=msg_id, eje=axis_id)
        header_2 = None
        if command_2:
            header_2 = service_handlers.build_msg(command_2, msg_id=msg_id, eje=axis_id)
        if ch_info:
            send_message(header, ch_info)
            if header_2:
                send_message(header_2, ch_info)
        if MicroState.routine_ongoing == True:
            MicroState.routine_stopped = True
        MicroState.master_stop = True
    return JsonResponse({})

@csrf_exempt
def stop_all(request):
    print('stop all')
    ch_info = get_ch_info(ChannelInfo, 'micro')
    msg_id = MicroState.msg_id
    command = AcdpMsgCmd.CD_STOP_ALL
    header = service_handlers.build_msg(command, msg_id=msg_id)
    if ch_info:
        send_message(header, ch_info)
    if MicroState.routine_ongoing == True:
        MicroState.routine_stopped = True
    MicroState.master_stop = True
    ctrl_func.reset_routines_info()
    return JsonResponse({})


@csrf_exempt
def end_master_routine(request):
    MicroState.end_master_routine = True
    print('END MASTER FLAG LEVANTADO')
    return JsonResponse({})

@csrf_exempt
def exit_tapping(request):
    handler = RoutineHandler()
    handler.routine_exit_tapping()
    print("exit tapping button")
    return JsonResponse({})



@csrf_exempt
def reset_cuplas_count(request):
    MicroState.reset_cuplas_count = True
    print('FLAG CONTADOR RESETEADO LEVANTADO')
    # contable = Parameter.objects.get(name='roscado_contador')
    params = Parameter.objects.all()
    part_model = param_vars.SELECTED_MODEL
    contable = params.filter(part_model=part_model).get(name='roscado_contador')
    if(MicroState.reset_cuplas_count == True):
        if (contable):
            contable.value = 0
            contable.save()
    MicroState.reset_cuplas_count = False
    print('roscado contador: ', contable)  #ctrl_vars.ROSCADO_CONSTANTES['roscado_contador']
    update_roscado_params()
    return JsonResponse({})

@csrf_exempt
def safe_mode(request):
    post_req = request.POST
    cmd = post_req["command"]
    if int(cmd) == 1:
        MicroState.neumatic_safe_mode = False
    else:
        MicroState.neumatic_safe_mode = True
    return JsonResponse({})


@csrf_exempt
def semiauto(request):
    post_req = request.POST
    print(post_req)
    routine = int(post_req['routine'])

    if ctrl_func.check_routine_allowed(routine):
        MicroState.routine_stopped = False
        RoutineHandler(routine).start()
    
    return JsonResponse({})


@csrf_exempt
def enable_axis(request):
    post_req = request.POST
    axis = int(post_req['eje'])
    cmd = int(post_req['command'])
    print(cmd, axis)
    msg_id = MicroState.last_rx_header.get_msg_id() + 1
    header = service_handlers.build_msg(cmd, msg_id=msg_id, eje=axis)
    ch_info = get_ch_info(ChannelInfo, 'micro')
    if ch_info:
        send_message(header, ch_info)
    return JsonResponse({})


@csrf_exempt
def sync_axis(request):
    post_req = request.POST
    msg_id = MicroState.last_rx_header.get_msg_id() + 1
    cmd = int(post_req['command'])
    ch_info = get_ch_info(ChannelInfo, 'micro')
    paso = None
    data = None
    header = None
    if 'paso' in post_req.keys() and cmd == Commands.sync_on:
        paso = float(post_req['paso'])
        header, data = service_handlers.build_msg(cmd, msg_id=msg_id, paso=paso, eje=ctrl_vars.AXIS_IDS['avance'])
    elif cmd == Commands.sync_off:
        header = service_handlers.build_msg(cmd, msg_id=msg_id, eje=ctrl_vars.AXIS_IDS['avance'])
    if header:
        if ch_info:
            send_message(header, ch_info, data)
    return JsonResponse({})


@method_decorator(csrf_exempt, name='dispatch')
class StartRoutine(View):

    def get(self, request):
        print('GET req auto')
        return JsonResponse({})
    
    def post(self, request):
        if MicroState.master_running == True:
            print('Master ya está ejecutándose')
        
        else:
            MasterHandler().start()
        
        return JsonResponse({})
    
    def get_running_routines(self):
        running_routines = []
        for routine in RoutineInfo.objects.all():
            if routine.running == 1:
                running_routines.append(ctrl_vars.ROUTINE_IDS[routine.name])
        return running_routines