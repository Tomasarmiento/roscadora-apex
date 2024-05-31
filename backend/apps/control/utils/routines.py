from asyncio import sleep
import threading
import time
import pymsgbox
import tkinter as tk
from datetime import datetime

from apps.control.models import RoutineInfo
from apps.control.utils import functions as ctrl_fun
from apps.control.utils import variables as ctrl_vars

from apps.service.api.variables import Commands, COMMANDS
from apps.service.acdp.handlers import build_msg
from apps.service.acdp import messages_app as msg_app
from apps.service.acdp import messages_base as msg_base

from apps.ws.models import ChannelInfo
from apps.ws.utils import variables as ws_vars
from apps.ws.utils.handlers import send_message
from apps.ws.utils.functions import get_ch_info

from apps.graphs.models import Graph

from apps.parameters.models import Parameter
from apps.parameters.utils.functions import update_roscado_params
from apps.parameters.utils import variables as param_vars

class RoutineHandler(threading.Thread):

    def __init__(self, routine=None, **kwargs):
        self.running_routines = []
        self.runnng_routines = ctrl_fun.get_running_routines()
        self.current_routine = routine
        self.ch_info = get_ch_info(ChannelInfo, 'micro')
        super(RoutineHandler, self).__init__(**kwargs)
        self._stop_event = threading.Event()
        self.wait_time = 0.05
        self.err_msg = []
    


    def run(self):
        routine = self.current_routine
        print('INICIO DE RUTINA ID', routine)
        if routine:
            routine_ok = None
            
            start_time = datetime.now()
            
            try:
                routine_info = RoutineInfo.objects.get(name=ctrl_vars.ROUTINE_NAMES[routine])
                print('RUTINA', ctrl_vars.ROUTINE_NAMES[routine])
            except RoutineInfo.DoesNotExist:
                print('ID de rutina inválido')
                ws_vars.MicroState.err_messages.append('Error - ID de rutina inválido')
                return False

            if routine_info.running == 1:
                print('La rutina ya se está ejecutando')
                ws_vars.MicroState.err_messages.append('Error - La rutina ya se está ejecutando')
                return False
            
            self.set_routine_ongoing_flag()

            if routine == ctrl_vars.ROUTINE_IDS['cerado']:
                if ws_vars.MicroState.routine_ongoing == True:
                    print('Rutina en proceso. No se puede cerar')
                    ws_vars.MicroState.err_messages.append('Error - Rutina en proceso. No se puede cerar')
                    return False
                ws_vars.MicroState.homing_ongoing = True
                ws_vars.MicroState.routine_ongoing = True
                routine_info.running = 1
                routine_info.save()
                routine_ok = self.routine_homing()

            elif routine == ctrl_vars.ROUTINE_IDS['cerado_lineal']:
                if ws_vars.MicroState.routine_ongoing == True:
                    print('Rutina en proceso. No se puede cerar Lineal')
                    ws_vars.MicroState.err_messages.append('Error - Rutina en proceso. No se puede cerar Lineal')
                    return False
                ws_vars.MicroState.routine_ongoing = True
                routine_info.running = 1
                routine_info.save()
                routine_ok = self.routine_homing_avance()
            

            elif routine == ctrl_vars.ROUTINE_IDS['cabezal_indexar']:
                if ws_vars.MicroState.routine_ongoing == True:
                    print('Rutina en proceso. No se puede indexar')
                    ws_vars.MicroState.err_messages.append('Error - Rutina en proceso. No se puede indexar')
                    return False
                ws_vars.MicroState.routine_ongoing = True
                routine_info.running = 1
                routine_info.save()
                print('RUTINA CABEZAL')
                ws_vars.MicroState.log_messages.append('INDEXAR')
                routine_ok = self.routine_cabezal_indexar()
                

            else:
                routine_info.running = 1
                routine_info.save()
                ws_vars.MicroState.routine_ongoing = True
                
                if routine == ctrl_vars.ROUTINE_IDS['carga']:
                    print('CARGA')
                    ws_vars.MicroState.log_messages.append('CARGA')
                    routine_ok = self.routine_carga()
                
                elif routine == ctrl_vars.ROUTINE_IDS['descarga']:
                    print('DESCARGA')
                    ws_vars.MicroState.log_messages.append('DESCARGA')
                    routine_ok = self.routine_descarga()
                
                elif routine == ctrl_vars.ROUTINE_IDS['roscado']:
                    print('ROSCADO')
                    ws_vars.MicroState.log_messages.append('ROSCADO')
                    routine_ok = self.routine_roscado()
            
            routine_info.running = 0
            routine_info.save()
            end_time = datetime.now()
            ws_vars.MicroState.routine_ongoing = self.check_running_routines()
            if routine_ok:
                duration = end_time - start_time
                print('Routine OK')
                print('ROUTINE DURATION:', duration)

                # agregado por AP - manda a el cuadro de mensajes el Nro d eiteracion
                mensaje =  'ROUTINE DURATION: ' + str(duration.seconds)
                ws_vars.MicroState.log_messages.append(mensaje)

                if ws_vars.MicroState.graph_flag == True and routine == ctrl_vars.ROUTINE_IDS['roscado']:
                    ws_vars.MicroState.graph_flag = False
                    ws_vars.MicroState.graph_duration = duration
                    start_graph = datetime.now()
                    Graph.objects.create(
                        graph_data = {
                            'position': ws_vars.MicroState.position_values,
                            'torque': ws_vars.MicroState.torque_values
                        }
                    )
                    max_torque_value_abs = [(num) for num in ws_vars.MicroState.torque_values]
                    ws_vars.MicroState.max_torque_value = max(max_torque_value_abs)

                    max_torque_lineal_value_abs = [abs(num) for num in ws_vars.MicroState.torque_lineal_values]
                    ws_vars.MicroState.max_torque_lineal_value = max(max_torque_lineal_value_abs)

                    end_graph = datetime.now()
                    print(end_graph - start_graph)
                return True
            else:
                ws_vars.MicroState.graph_flag = False
                ws_vars.MicroState.graph_duration = -1
                ws_vars.MicroState.master_stop = True
                ws_vars.MicroState.homing_ongoing = False
                ws_vars.MicroState.roscado_ongoing = False

                print('Error en rutina de', ctrl_vars.ROUTINE_NAMES[self.current_routine])
                for msg in self.err_msg:
                    print('MENSAJE DE ERROR:', msg)
                
                return False
        else:
            print('Rutina no especificada')
    


# ******************** INDEXAR ********************
    def routine_cabezal_indexar(self):
        # Paso 0 - Chequear condiciones iniciales
        init_conditions_error_messages = ctrl_fun.check_init_conditions_index()
        if init_conditions_error_messages:
            print('\nError en condiciones iniciales de indexado')
            err_msg = 'Error en condiciones iniciales de indexado'
            ws_vars.MicroState.err_messages.append(err_msg)
            for err in init_conditions_error_messages:
                ws_vars.MicroState.err_messages.append(err)
                print(err)
            return False
        print('INDEXAR - Paso 0 - Chequear condiciones iniciales')
        ws_vars.MicroState.log_messages.append('INDEXAR - Inicio de rutina')

        # Paso 1 - Liberar plato
        key_1 = 'contraer_clampeo_plato'
        key_2 = 'expandir_clampeo_plato'
        if not self.send_pneumatic(key_1, 1, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - INDEXAR - Paso 1 - Liberar plato')
            return False
        
        if not self.wait_for_remote_in_flag('clampeo_plato_contraido', 1):
            ws_vars.MicroState.err_messages.append('Error Flag - INDEXAR - Paso 1 - Liberar plato')
            return False
        print('INDEXAR - Paso 1 - Liberar plato')


        # Paso 2 - Power on servo carga
        command = Commands.power_on
        axis = ctrl_vars.AXIS_IDS['carga']
        msg_id = self.get_message_id()
        header = build_msg(command, eje=axis, msg_id=msg_id)

        if not self.send_message(header):
            ws_vars.MicroState.err_messages.append('Error Comando - INDEXAR - Paso 2 - Power on servo carga')
            return False
    
        if not self.wait_for_axis_state(msg_app.StateMachine.EST_INITIAL, axis):
            ws_vars.MicroState.err_messages.append('Error Flag - INDEXAR - Paso 2 - Servo no pasa a estado ENABLE')
            return False

        print('INDEXAR - Paso 2 - Power on servo carga')
       

        # Paso 3 - Avanza 120° al siguiente paso
        eje_avance = ctrl_vars.AXIS_IDS['avance']
        turn_init_flags = [
            ws_vars.MicroState.rem_i_states[1]['acople_lubric_contraido'],      # acople_lubricante_contraido
            ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'],   # puntera_descarga_contraida
            ws_vars.MicroState.rem_i_states[0]['puntera_carga_contraida'],      # puntera_carga_contraida
            round(ws_vars.MicroState.axis_measures[eje_avance]['pos_fil'], 0) >= round(ctrl_vars.ROSCADO_CONSTANTES['posicion_de_inicio'], 0)   # Eje avance en posición de inicio
        ]

        if False in turn_init_flags:
            ws_vars.MicroState.err_messages.append('Error - INDEXAR - Paso 3 - Condiciones de giro indexado')
            return False

        if not self.move_step_load_axis():
            ws_vars.MicroState.err_messages.append('Error - INDEXAR - Paso 3 - Avanza 120° al siguiente paso')
            return False
        print('INDEXAR - Paso 3 - Avanza 120° al siguiente paso')


        # Paso 4 - Clampea plato
        key_1 = 'expandir_clampeo_plato'
        key_2 = 'contraer_clampeo_plato'
        group = 1
        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - INDEXAR - Paso 4 - Clampea plato')
            return False
        
        if not self.wait_for_remote_in_flag('clampeo_plato_expandido', group):
            ws_vars.MicroState.err_messages.append('Error Flag - INDEXAR - Paso 4 - Clampea plato')
            return False
        print('INDEXAR - Paso 4 - Clampea plato')


        # Paso 5 - Power off
        command = Commands.power_off
        msg_id = self.get_message_id()
        drv_flag = msg_base.DrvFbkDataFlags.ENABLED
        header = build_msg(command, eje=axis, msg_id=msg_id)
        if not self.send_message(header):
            ws_vars.MicroState.err_messages.append('Error Comando - INDEXAR - Paso 5 - Power off servo')
            return False
        
        if not self.wait_for_drv_flag(drv_flag, axis, 0):
            ws_vars.MicroState.err_messages.append('Error Flag - INDEXAR - Paso 5 - Power off servo')
            return False
        print('INDEXAR - Paso 5 - Power off servo')


        print('INDEXAR - FIN RUTINA')
        ws_vars.MicroState.log_messages.append('INDEXAR - Fin de rutina')
        return True



# ******************** CARGA ********************
    def routine_carga(self):

        # Paso 0 - Chequear condiciones iniciales - Todos los valores deben ser True par que empiece la rutina
        init_conditions_error_messages = ctrl_fun.check_init_conditions_load()
        if init_conditions_error_messages:
            print('\nError en condiciones iniciales de carga')
            err_msg = 'Error en condiciones iniciales de carga'
            ws_vars.MicroState.err_messages.append(err_msg)
            for err in init_conditions_error_messages:
                ws_vars.MicroState.err_messages.append(err)
                print(err)
            return False
        print('CARGA - Paso 0 - Chequear condiciones iniciales - Todos los valores deben ser True par que empiece la rutina')
        ws_vars.MicroState.log_messages.append('CARGA - Inicio de rutina')

        if ws_vars.MicroState.master_running == True:
            step = self.check_part_present_carga()
        else:
            step = 0

        
        if step is False:
            ws_vars.MicroState.err_messages.append('Error en rutina de carga inicia master')
            return False
            
        
        if step != 8:
            # Paso 0.1 - Chequear presencia de cupla
            if ws_vars.MicroState.rem_i_states[1]['presencia_cupla_en_cargador'] == 0:

                ws_vars.MicroState.err_messages.append('**********************')
                ws_vars.MicroState.err_messages.append('**** CARGAR CUPLA ****')
                ws_vars.MicroState.err_messages.append('**********************')

                wait_key = 'presencia_cupla_en_cargador'
                wait_group = 1

                if not self.wait_flag_presencia_cupla_en_cargador(wait_key, wait_group):
                    ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 0.1 - Presencia de cupla en cargador')
                    return False
            print('CARGA - Paso 0.1 - Cupla cargada en vertical')
            



            # Paso 1 - Expandir vertical carga
            key = 'expandir_vertical_carga'
            wait_key = 'vertical_carga_expandido'
            group = 0
            wait_group = 0
            if not self.send_pneumatic(key, group, 1):
                ws_vars.MicroState.err_messages.append('Error Comando - CARGA - Paso 1 - Expandir vertical carga')
                return False

            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 1 - Expandir vertical carga')
                return False
            print('CARGA - Paso 1 - Expandir vertical carga')
            
            


            # Paso 1.1 - Abrir válvula de boquilla hidráulica
            boquilla = self.get_current_boquilla_carga()
            key_1 = 'cerrar_boquilla_' + str(boquilla)
            key_2 = 'abrir_boquilla_' + str(boquilla)
            group = 1
            self.send_pneumatic(key_1, group, 0, key_2, 1)
            print('CARGA - Paso 1.1 - Abrir válvula de boquilla hidráulica')



            # Paso 2 - Expandir horizontal puntera carga
            key_1 = 'expandir_puntera_carga'
            key_2 = 'contraer_puntera_carga'
            #wait_key = 'puntera_carga_contraida'
            wait_key = 'puntera_carga_expandida'
            group = 0

            print("EXPANDIR PUNTERA CARGA")
            if not self.send_pneumatic(key_1, group, 1, key_2, 0):
                ws_vars.MicroState.err_messages.append('Error Comando - CARGA - Paso 2 - Expandir horizontal puntera carga')
                return False

            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 2 - Expandir horizontal puntera carga')
                return False

            time.sleep(3)
            print('CARGA - Paso 2 - Expandir horizontal puntera carga')



            # Paso 3 - Boquilla carga contraida
            key = 'contraer_boquilla_carga'
            wait_key = 'boquilla_carga_contraida'
            group = 0
            wait_group = 0
            if not self.send_pneumatic(key, group, 1):
                ws_vars.MicroState.err_messages.append('Error Comando - CARGA - Paso 3 - Boquilla carga contraida')
                return False

            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 3 - Boquilla carga contraida')
                return False
            
            print('CARGA - Paso 3 - Boquilla carga contraida')
            


            # Paso 4 - Verificar flags pieza en boquilla carga
            key = 'pieza_en_boquilla_carga'
            if ws_vars.MicroState.rem_i_states[1][key]:
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 4 - Verificar flags pieza en boquilla carga')
                return False

            print("PIEZA EN BOQUILLA", ws_vars.MicroState.rem_i_states[1][key])
            print('CARGA - Paso 4 - Verificar flags pieza en boquilla carga')



            # Paso 5 - Contraer horizontal puntera carga
            key_1 = 'contraer_puntera_carga'
            key_2 = 'expandir_puntera_carga'
            wait_key = 'puntera_carga_contraida'
            group = 0
            wait_group = 0

            if not self.send_pneumatic(key_1, group, 1, key_2, 0):
                ws_vars.MicroState.err_messages.append('Error Comnando - CARGA - Paso 5 - Contraer horizontal puntera carga')
                return False

            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 5 - Contraer horizontal puntera carga')
                return False

            print('CARGA - Paso 5 - Contraer horizontal puntera carga')



            # Paso 6 - Contraer vertical y giro brazo cargador
            key = 'expandir_vertical_carga'
            group = 0

            if not self.send_pneumatic(key, group, 0):
                ws_vars.MicroState.err_messages.append('Error Comnando - CARGA - Paso 6 - Contraer vertical')
                return False

            key_1 = 'contraer_brazo_cargador'
            key_2 = 'expandir_brazo_cargador'
            group = 0

            if not self.send_pneumatic(key_1, group, 1, key_2, 0):
                ws_vars.MicroState.err_messages.append('Error Comnando - CARGA - Paso 6 - Contraer giro brazo cargador')
                return False
            
            wait_key = 'vertical_carga_contraido'
            wait_group = 0

            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 6 - Contraer vertical')
                return False

            print('VERTICAL CARGA CONTRAIDO')

            wait_key = 'brazo_cargador_contraido'

            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 6 - Contraer giro brazo cargador')
                return False

            print('BRAZO CARGA CONTRAIDO')
            print('CARGA - Paso 6 - Contraer vertical y giro brazo cargador')



            # Paso 7 - Verificar pieza en boquilla carga
            if ws_vars.MicroState.rem_i_states[1]['pieza_en_boquilla_carga']:
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 7 - Verificar pieza en boquilla carga')
                return False
            else:
                print('PIEZA EN BOQUILLA CARGA')
            print('CARGA - Paso 7 - Verificar pieza en boquilla carga')


        # Paso 8 - Avanza horizontal puntera carga en boquilla
        key_1 = 'expandir_puntera_carga'
        key_2 = 'contraer_puntera_carga'
        wait_key = 'puntera_carga_contraida'
        wait_group = 0
        group = 0

        load_init_flags = [
            ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'],          # Plato clampeado
        ]

        if False in load_init_flags:
            ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 8 - Verificar clampeo plato')
            return False
        
        pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
        if pos not in ctrl_vars.LOAD_STEPS:
            ws_vars.MicroState.err_messages.append('Error - CARGA - Paso 8 - Verificar posicion de cabezal')
            print('Error en posicion de cabezal')
            return False
        
        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - CARGA - Paso 8 - Avanza horizontal puntera carga en boquilla')
            return False

        if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - Paso 8 - Avanza horizontal puntera carga en boquilla')
            return False

        time.sleep(2)
        print('PUNTERA EXPANDIDA')
        print('CARGA - Paso 8 - Avanza horizontal puntera carga en boquilla')



        # Paso 9 - Boquilla carga extendida
        key = 'contraer_boquilla_carga'
        wait_key = 'boquilla_carga_expandida'
        group = 0
        wait_group = 0
        if not self.send_pneumatic(key, group, 0):
            ws_vars.MicroState.err_messages.append('Error Comnando - CARGA - Paso 9 - Boquilla carga extendida')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 9 - Boquilla carga extendida')
            return False
        print('CARGA - Paso 9 - Boquilla carga extendida')



        # Paso 10 - Presurizar ON
        ws_vars.MicroState.load_allow_presure_off = False
        key = 'presurizar'
        group = 1
        self.send_pneumatic(key, group, 1)
        print('CARGA - Paso 10 - Presurizar ON')
        


        # Paso 11 - Poner en ON cerrar boquilla hidráulica
        boquilla = self.get_current_boquilla_carga()
        key_1 = 'cerrar_boquilla_' + str(boquilla)
        key_2 = 'abrir_boquilla_' + str(boquilla)
        group = 1
        self.send_pneumatic(key_1, group, 1, key_2, 0)
        time.sleep(2)
        print('CARGA - Paso 11 - Poner en ON cerrar boquilla hidráulica')



        # Paso 12 - Puntera horizontal contraído
        key_1 = 'contraer_puntera_carga'
        key_2 = 'expandir_puntera_carga'
        wait_key = 'puntera_carga_contraida'
        group = 0
        wait_group = 0

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comnando - CARGA - Paso 12 - Puntera horizontal contraído')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 12 - Puntera horizontal contraído')
            return False

        print('CARGA - Paso 12 - Puntera horizontal contraído')



        # Paso 13 - Verificar que no haya pieza en boquilla carga. Levanta flag cupla presente en boquilla
        if not ws_vars.MicroState.rem_i_states[1]['pieza_en_boquilla_carga']:
            print('Estado sensor boquilla: ',ws_vars.MicroState.rem_i_states[1]['pieza_en_boquilla_carga'])
            ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 13 - Verificar no pieza en boquilla carga.')
            return False
        ctrl_vars.part_present_indicator[boquilla] = True
        print('CARGA - Paso 13 - Verificar no pieza en boquilla carga. Levanta flag cupla presente en boquilla')



        # CARGA - Paso 14 - Cerrar boquilla hidráulica. Poner abrir y cerrar en OFF
        key_1 = 'cerrar_boquilla_' + str(boquilla)
        key_2 = 'abrir_boquilla_' + str(boquilla)
        group = 1
        self.send_pneumatic(key_1, group, 0, key_2, 0)
        print('CERRAR VALVULA HIDRAULICA')
        print('CARGA - Paso 14 - Cerrar boquilla hidráulica. Poner abrir y cerrar en OFF')
        time.sleep(1)



        # Paso 15 - Presurizar OFF
        ws_vars.MicroState.load_allow_presure_off = True
        
        #espera tener el flag allow_presure_off de roscado en true
        roscado_id = ctrl_vars.ROUTINE_IDS['roscado']
        roscado_running = (RoutineInfo.objects.get(name=ctrl_vars.ROUTINE_NAMES[roscado_id]).running == 1)
        print('ROSCADO EN PROCESO:', roscado_running)

        if roscado_running:
            if self.wait_presure_off_allowed(roscado_id) == False:
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 15 - Presurizar OFF, no tiene flag allow_presure_off de roscado')
                return False
        
        key = 'presurizar'
        group = 1
        self.send_pneumatic(key, group, 0)
        print('CARGA - Paso 15 - Presurizar OFF')



        # Paso 16 - Expandir giro brazo cargador
        key_1 = 'expandir_brazo_cargador'
        key_2 = 'contraer_brazo_cargador'
        wait_key = 'brazo_cargador_expandido'
        group = 0
        wait_group = 0
    
        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comnando - CARGA - Paso 16 - Expandir giro brazo cargador')
            return False
        
        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - CARGA - Paso 16 - Expandir giro brazo cargador')
            return False
        print('CARGA - Paso 16 - Expandir giro brazo cargador')



        ws_vars.MicroState.log_messages.append('CARGA - Fin de rutina')
        print('CARGA - FIN RUTINA')
        return True



# ******************** DESCARGA ********************
    def routine_descarga(self):
        # Paso 0 - Chequear condiciones iniciales - Todos los valores deben ser True par que empiece la rutina
        init_conditions_error_messages = ctrl_fun.check_init_conditions_unload()
        if init_conditions_error_messages:
            print('\nError en condiciones iniciales de descarga')
            err_msg = 'Error en condiciones iniciales de descarga'
            ws_vars.MicroState.err_messages.append(err_msg)
            for err in init_conditions_error_messages:
                ws_vars.MicroState.err_messages.append(err)
                print(err)
            return False
        print('DESCARGA - Paso 0 - Chequear condiciones iniciales - Todos los valores deben ser True par que empiece la rutina')
        ws_vars.MicroState.log_messages.append('DESCARGA - Inicio de rutina')

        # Paso 0.1a - Espera liberacion de cupla en tobogan
        wait_key = 'cupla_por_tobogan_descarga'
        wait_group = 1

        if self.wait_for_not_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Descarga llena, liberar tobogan de descarga')
            if not self.wait_flag_presencia_cupla_en_cargador(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - 0.1a - No se libero tobogan de descarga')
                return False

        print('DESCARGA - 0.1a - Espera liberacion de cupla en tobogan')



        # Paso 0.1b - Abrir válvula de boquilla hidráulica
        boquilla = self.get_current_boquilla_descarga()
        key_1 = 'abrir_boquilla_' + str(boquilla)
        key_2 = 'cerrar_boquilla_' + str(boquilla)
        group = 1
        self.send_pneumatic(key_1, group, 1, key_2, 0)
        time.sleep(4)
        self.send_pneumatic(key_2, group, 1, key_1, 0)
        time.sleep(4)
        self.send_pneumatic(key_1, group, 1, key_2, 0)
        print('DESCARGA - Paso 0.1 - Abrir válvula de boquilla hidráulica')


        if ws_vars.MicroState.master_running == True:
            step = self.check_part_present_descarga()
        else:
            step = 0


        if step is False:
            ws_vars.MicroState.err_messages.append('Error en rutina de descarga inicia master')
            return False
        
        if step is True:
            # cupla no presente, no se ejecuta rutina de descarga
            print('DESCARGA INICIA - FIN RUTINA')
            ws_vars.MicroState.log_messages.append('DESCARGA INICIA - Fin de rutina')
            return True

        
        # si step == 0 es decir que hay cupla, tengo que hacer los movimientos de la garra y el giro cargador (estoy atras con el horizontal y con cupla)
        # si step != 0 es decir que no hay cupla, no hago nada ya que no tengo q descargar nada, la boquilla del plato estaba vacia

        # Paso 0.2 - expandir_horiz_pinza_desc, luego chequeamos los flags de que se haya movido
        key_1 = 'expandir_horiz_pinza_desc'
        key_2 = 'contraer_horiz_pinza_desc'
        group = 1

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comnando - DESCARGA - Paso 0.2 - expandir horizontal pinza')
            return False

        print('expandir_horiz_pinza_desc')
        print('DESCARGA - Paso 0.2 - expandir horizontal pinza')
        
        if step == 0:
            # Paso 1 - Expandir horizontal puntera descarga
            unload_init_flags = [
                ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'],          # Plato clampeado
            ]

            if False in unload_init_flags:
                ws_vars.MicroState.err_messages.append('Error - DESCARGA - Paso 1 - Verificar clampeo plato')
                return False
            
            pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
            if pos not in ctrl_vars.LOAD_STEPS:
                # print('Error en posicion de cabezal')
                ws_vars.MicroState.err_messages.append('Error - DESCARGA - Paso 1 - Verificar posicion de cabezal')
                return False

            key_1 = 'expandir_puntera_descarga'
            key_2 = 'contraer_puntera_descarga'
            wait_key = 'puntera_descarga_contraida'
            group = 0
            wait_group = 0
            print("EXPANDIR HORIZONTAL PUNTERA DESCARGA")

            if not self.send_pneumatic(key_1, group, 1, key_2, 0):
                ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 1 - Expandir horizontal puntera descarga')
                return False

            if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 1 - Expandir horizontal puntera descarga')
                return False

            time.sleep(5)
            print('DESCARGA - Paso 1 - Expandir horizontal puntera descarga')


        # Paso 1.1 - Verifica FLAG expandir horizontal pinza, comando en paso 0.2 
        wait_key = 'horiz_pinza_desc_expandido'
        wait_group = 1

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 1.1 - Verifica expandir horizontal pinza')
            return False

        print('DESCARGA - Paso 1.1 - Verifica FLAG expandir horizontal pinza, comando en paso 0.2')



        # Paso 2 - expandir_vert_pinza_desc, luego chequeamos los flags de que se haya movido
        key_1 = 'expandir_vert_pinza_desc'
        key_2 = 'contraer_vert_pinza_desc'
        group = 1

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - PASO 2 - expandir vertical pinza')
            return False

        print('DESCARGA - PASO 2 - expandir vertical pinza')


        if step == 0:
            # Paso 3 - Boquilla descarga contraida
            key = 'contraer_boquilla_descarga'
            wait_key = 'boquilla_descarga_expandida'
            group = 0
            wait_group = 0
            if not self.send_pneumatic(key, group, 1):
                ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 3 - Boquilla descarga contraida')
                return False
            if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 3 - Boquilla descarga contraida')
                return False

            time.sleep(4) #timer ts : espera a que termine de abrir la boquilla
            print('contraer_boquilla_descarga')
            print('DESCARGA - Paso 3 - Boquilla descarga contraida')


        # Paso 4 - Verifica FLAG expandir vertical pinza, comando en paso 2
        wait_key = 'vert_pinza_desc_expandido'
        wait_group = 1

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 4 - Verifica expandir vertical pinza')
            return False

        print('expandir_vert_pinza_desc')
        print('DESCARGA - Paso 4 - Verifica FLAG expandir vertical pinza, comando en paso paso 2')



        if step == 0:
            # Paso 5 - Puntera horizonal descarga contraída
            key_1 = 'contraer_puntera_descarga'
            key_2 = 'expandir_puntera_descarga'
            wait_key = 'puntera_descarga_contraida'
            group = 0
            wait_group = 0

            if not self.send_pneumatic(key_1, group, 1, key_2, 0):
                ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 5 - Puntera horizonal descarga contraída')
                return False

            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 5 - Puntera horizonal descarga contraída')
                return False

            print("DESCARGA - Paso 5 - PUNTERA HORIZONTAL DESCARGA CONTRAIDA")



            # Paso 6.1 - Verificar cupla en boquilla descarga. Si no está hace segundo intento
            if ws_vars.MicroState.rem_i_states[1]['pieza_en_boquilla_descarga']:
                
                ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 6.1 - No tomó cupla de boquilla hidraulica, hace segundo intento')

                # Paso 6.1 A - Abrir boquilla descarga
                key = 'contraer_boquilla_descarga'
                wait_key = 'boquilla_descarga_expandida'
                group = 0
                wait_group = 0

                if not self.send_pneumatic(key, group, 0):
                    ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 13 - Abrir boquilla descarga')
                    return False

                if not self.wait_for_remote_in_flag(wait_key, wait_group):
                    ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 13 - Abrir boquilla descarga')
                    return False
                time.sleep(4)
                print('DESCARGA - PASO 6.1 A - Abrir boquilla descarga')


                # Paso 6.1 B - Expandir horizontal puntera descarga
                key_1 = 'expandir_puntera_descarga'
                key_2 = 'contraer_puntera_descarga'
                wait_key = 'puntera_descarga_contraida'
                group = 0
                wait_group = 0
                print("EXPANDIR HORIZONTAL PUNTERA DESCARGA")

                if not self.send_pneumatic(key_1, group, 1, key_2, 0):
                    ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 6.1 B - Expandir horizontal puntera descarga')
                    return False

                if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
                    ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 6.1 B - Expandir horizontal puntera descarga')
                    return False

                time.sleep(1)
                print('DESCARGA - Paso 6.1 B - Expandir horizontal puntera descarga')


                # Paso 6.1 C - Boquilla descarga contraida
                key = 'contraer_boquilla_descarga'
                wait_key = 'boquilla_descarga_expandida'
                group = 0
                wait_group = 0

                if not self.send_pneumatic(key, group, 1):
                    ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 6.1 C - Boquilla descarga contraida')
                    return False

                if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
                    ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 6.1 C - Boquilla descarga contraida')
                    return False

                time.sleep(4)  # espera a que termine de abrir la boquilla hidraulica
                print('DESCARGA - Paso 6.1 C - Boquilla descarga contraida')


                # Paso 6.1 D - Puntera horizonal descarga contraída
                key_1 = 'contraer_puntera_descarga'
                key_2 = 'expandir_puntera_descarga'
                wait_key = 'puntera_descarga_contraida'
                group = 0
                wait_group = 0

                if not self.send_pneumatic(key_1, group, 1, key_2, 0):
                    ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 6.1 D - Puntera horizonal descarga contraída')
                    return False

                if not self.wait_for_remote_in_flag(wait_key, wait_group):
                    ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 6.1 D - Puntera horizonal descarga contraída')
                    return False

                print("DESCARGA - Paso 6.1 D - PUNTERA HORIZONTAL DESCARGA CONTRAIDA")

            print("Paso 6.1 - Verificar cupla en boquilla descarga. Si no está hace segundo intento")



            # Paso 6.2 - Verificar cupla en boquilla descarga. Baja flag cupla presente en boquilla
            if ws_vars.MicroState.rem_i_states[1]['pieza_en_boquilla_descarga']:
                ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 6 - Verificar cupla en boquilla descarga')
                return False
        
            print('CUPLA PRESENTE')
            print('DESCARGA - Paso 6.2 - Verificar cupla en boquilla descarga. Baja flag cupla presente en boquilla')

        ctrl_vars.part_present_indicator[boquilla] = False



        # Paso 7 - Contraer giro brazo descargador
        key_1 = 'contraer_brazo_descargador'
        key_2 = 'expandir_brazo_descargador'
        wait_key = 'brazo_descarga_contraido'
        group = 0
        wait_group = 0
        
        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 7 - Contraer giro brazo descargador')
            return False
        
        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 7 - Contraer giro brazo descargador')
            return False

        print('DESCARGA - Paso 7 - Contraer giro brazo descargador')



        # Paso 8 - Expandir horizontal puntera descarga
        key_1 = 'expandir_puntera_descarga'
        key_2 = 'contraer_puntera_descarga'
        wait_key = 'puntera_descarga_expandida'
        group = 0
        wait_group = 0
        print("EXPANDIR HORIZONTAL PUNTERA DESCARGA")

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 8 - Expandir horizontal puntera descarga')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 8 - Expandir horizontal puntera descarga')
            return False

        print('DESCARGA - Paso 8 - Expandir horizontal puntera descarga')
        


        # Paso 9 - Verificar cupla en boquilla descarga
        if ws_vars.MicroState.rem_i_states[1]['pieza_en_boquilla_descarga']:
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 9 - Verificar cupla en boquilla descarga')
            return False

        print('CUPLA PRESENTE')
        print('DESCARGA - Paso 9 - Verificar cupla en boquilla descarga')



        # Paso 12 - Pinza descargadora cerrada
        key_1 = 'cerrar_pinza_descargadora'
        key_2 = 'abrir_pinza_descargadora'
        group = 0
        wait_key = 'pinza_descargadora_abierta'
        wait_group = 0

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 12 - Pinza descargadora cerrada')
            return False

        # if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
        #     ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 12 - Pinza descargadora cerrada')
        #     return False

        time.sleep(1)
        print('DESCARGA - Paso 12 - Pinza descargadora cerrada')



        # Paso 13 - Abrir boquilla descarga
        key = 'contraer_boquilla_descarga'
        wait_key = 'boquilla_descarga_expandida'
        group = 0
        wait_group = 0

        if not self.send_pneumatic(key, group, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 13 - Abrir boquilla descarga')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 13 - Abrir boquilla descarga')
            return False
        time.sleep(1)

        print('DESCARGA - PASO 13 - Abrir boquilla descarga')



        # Paso 14 - Puntera descargador horizontal contraído
        key_1 = 'contraer_puntera_descarga'
        key_2 = 'expandir_puntera_descarga'
        wait_key = 'puntera_descarga_contraida'
        group = 0
        wait_group = 0

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 14 - Puntera descargador horizontal contraído')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 14 - Puntera descargador horizontal contraído')
            return False

        print('DESCARGA - Paso 14 - Puntera descargador horizontal contraído')



        # Paso 14.1 - contraer vertical pinza descargadora
        key_1 = 'contraer_vert_pinza_desc'
        key_2 = 'expandir_vert_pinza_desc'
        group = 1

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - PASO 14.1 - contraer vertical pinza descargadora')
            return False

        print('Paso 14.1 - contraer vertical pinza descargadora')
        


        # Paso 15 - Verifica cupla no presente en boquilla descarga
        if not ws_vars.MicroState.rem_i_states[1]['pieza_en_boquilla_descarga']:
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 15 - Verifica cupla no presente en boquilla descarga')
            return False
        print('DESCARGA - Paso 15 - Verifica cupla no presente en boquilla descarga')
        

        
        # Paso 16 - Expandir giro brazo descargador
        key_1 = 'expandir_brazo_descargador'
        key_2 = 'contraer_brazo_descargador'
        group = 0
        
        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 16 - Expandir giro brazo descargador')
            return False

        print('DESCARGA - Paso 16 - Expandir giro brazo descargador')



        # Paso 16.1 - Verifica contraer vertical pinza descargadora, comando en paso 14.1
        wait_key = 'vert_pinza_desc_contraido'
        wait_group = 1
        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 16.1 - Verifica contraer vertical pinza descargadora')
            return False
        print('contraer_vert_pinza_desc')
        print('DESCARGA - Paso 16.1 - Verifica contraer vertical pinza descargadora, comando en paso 14.1')



        # Paso 16.2 - contraer horizontal pinza descargadora
        key_1 = 'contraer_horiz_pinza_desc'
        key_2 = 'expandir_horiz_pinza_desc'
        group = 1
        wait_key = 'horiz_pinza_desc_contraido'
        wait_group = 1

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 16.2 - contraer horizontal pinza descargadora')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 16.2 - contraer horizontal pinza descargadora')
            return False

        print('DESCARGA - Paso 16.2 - contraer horizontal pinza descargadora')



        # Paso 16.3 - Verifica Expandir giro brazo descargador, comando en paso 16
        wait_key = 'brazo_descarga_expandido'
        wait_group = 0
        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 16.3 - Verifica Expandir giro brazo descargador')
            return False
        print('DESCARGA - Paso 16.3 - Verifica Expandir giro brazo descargador, comando en paso 16')



        # Paso 19 - expandir vertical pinza descargadora
        key_1 = 'expandir_vert_pinza_desc'
        key_2 = 'contraer_vert_pinza_desc'
        group = 1
        wait_key = 'vert_pinza_desc_expandido'
        wait_group = 1

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 19 - expandir vertical pinza descargadora')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 19 - expandir vertical pinza descargadora')
            return False

        print('DESCARGA - Paso 19 - expandir vertical pinza descargadora')



        # Paso 20 - abrir pinza descargadora
        key_1 = 'abrir_pinza_descargadora'
        key_2 = 'cerrar_pinza_descargadora'
        group = 0
        wait_key = 'pinza_descargadora_abierta'
        wait_group = 0

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 20 - abrir pinza descargadora')
            return False

        #se comenta por que no estan puestos los sensores de pinza abierta y cerrada
        # if not self.wait_for_remote_in_flag(wait_key, wait_group):
        #     ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 20 - abrir pinza descargadora')
        #     return False

        print('DESCARGA - Paso 20 - abrir pinza descargadora')



        # Paso 21 - contraer vertical pinza descargadora
        key_1 = 'contraer_vert_pinza_desc'
        key_2 = 'expandir_vert_pinza_desc'
        group = 1
        wait_key = 'vert_pinza_desc_contraido'
        wait_group = 1

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 21 - contraer vertical pinza descargadora')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 21 - contraer vertical pinza descargadora')
            return False

        print('DESCARGA - Paso 21 - contraer vertical pinza descargadora')



        # Paso 22 - Espera presencia de cupla en tobogan
        wait_key = 'cupla_por_tobogan_descarga'
        wait_group = 1

        # if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
        #     ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 22 - Espera presencia de cupla en tobogan')
        #     return False

        if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Cupla no paso por tobogan de descarga')
            if not self.wait_for_not_flag_tobogan_descargador(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 22 - Espera presencia de cupla en tobogan')
                return False

        print('DESCARGA - Paso 22 - Espera presencia de cupla en tobogan')



        print('DESCARGA - FIN RUTINA')
        ws_vars.MicroState.log_messages.append('DESCARGA - Fin de rutina')
        return True



# ******************** ROSCADO ********************
    def routine_roscado(self):

        # time.sleep(10)
        # return True

        # *** Paso 0 - Chequear condiciones iniciales - Todos los valores deben ser True par que empiece la rutina
        init_conditions_error_messages = ctrl_fun.check_init_conditions_tapping()
        if init_conditions_error_messages:
            print('\nError en condiciones iniciales de roscado')
            err_msg = 'Error en condiciones iniciales de roscado'
            ws_vars.MicroState.err_messages.append(err_msg)
            for err in init_conditions_error_messages:
                ws_vars.MicroState.err_messages.append(err)
                print(err)
            return False

        roscado_start_time = datetime.now() # es para sacar los tiempos de cada paso de la rutina roscado

        ws_vars.MicroState.position_values = []
        ws_vars.MicroState.torque_values = []
        ws_vars.MicroState.torque_lineal_values = []
        ws_vars.MicroState.roscado_ongoing = True #Levanta flag de roscado en 1 para chequeo de apagar enable de husillo

        print("ROSCADO - Paso 0 - Chequear condiciones iniciales - Todos los valores deben ser True par que empiece la rutina")
        ws_vars.MicroState.log_messages.append('ROSCADO - Inicio de rutina')



        # *** Paso 1 - Acopla lubricante
        roscado_init_flags = [
            ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'],          # Plato clampeado
        ]
        if False in roscado_init_flags:
            ws_vars.MicroState.err_messages.append('Error - ROSCADO - Paso 1 - Verificar clampeo plato')
            return False
        
        #VERIFICA POSICIÓN CABEZAL INDEXADOR
        pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
        if pos not in ctrl_vars.LOAD_STEPS:
            ws_vars.MicroState.err_messages.append('Error - ROSCADO - Paso 1 - Verificar posicion de cabezal')
            return False
        
        key = 'expandir_acople_lubric'
        wait_key = 'acople_lubric_expandido'
        group = 1
        wait_group = 1

        if not self.send_pneumatic(key, group, 1):
            ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 1 - Acopla lubricante')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 1 - Acopla lubricante')
            return False

        roscado_delta_time_paso1=datetime.now()-roscado_start_time
        print('Delta Time Paso 1: ', roscado_delta_time_paso1)

        print("ROSCADO - Paso 1 - Acopla lubricante")



        # *** Paso 1.5 - Expandir cerramiento de roscado
        key = 'expandir_cerramiento_roscado'
        wait_key = 'cerramiento_roscado_contraido'
        group = 0
        wait_group = 1

        if not self.send_pneumatic(key, group, 1):
            ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 1.5 - Expandir cerramiento de roscado')
            return False

        
        if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 17 - Expandir cerramiento roscado')
            return False

        time.sleep(1) # Espera 1 seg para prender bomba soluble
        
        roscado_delta_time_paso_1_5 = datetime.now()-roscado_start_time
        print('Delta Time Paso 1.5: ', roscado_delta_time_paso_1_5)

        print("ROSCADO - Paso 1.5 - Expandir cerramiento roscado")



        # *** Paso 2 - Encender bomba solube
        key = 'encender_bomba_soluble'
        group = 1

        if not self.send_pneumatic(key, group, 1):
            ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 2 - Encender bomba solube')
            return False
        
        roscado_delta_time_paso2=datetime.now()-roscado_start_time
        print('Delta Time Paso 2: ', roscado_delta_time_paso2)

        print("ROSCADO - Paso 2 - Encender bomba solube")



        # *** Paso 3 - Presurizar ON
        ws_vars.MicroState.roscado_allow_presure_off = False
        key = 'presurizar'
        group = 1

        if not self.send_pneumatic(key, group, 1):
            ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 3 - Presurizar ON')
            return False

        roscado_delta_time_paso3=datetime.now()-roscado_start_time
        print('Delta Time Paso 3: ', roscado_delta_time_paso3)
        
        print("ROSCADO - Paso 3 - Presurizar ON")



        # *** Paso 4 - accionar cerrar para presurizar boquilla hidráulica
        boquilla = self.get_current_boquilla_roscado()
        key_1 = 'cerrar_boquilla_' + str(boquilla)
        key_2 = 'abrir_boquilla_' + str(boquilla)
        group = 1
        self.send_pneumatic(key_1, group, 1, key_2, 0)

        roscado_delta_time_paso4=datetime.now()-roscado_start_time
        print('Delta Time Paso 4: ', roscado_delta_time_paso4)

        print("ROSCADO - Paso 4 - accionar cerrar para presurizar boquilla hidráulica")



        # # *** Paso 5 - Avanzar a pos y vel de aproximacion
        # # ARMA EL MENSAJE
        # axis = ctrl_vars.AXIS_IDS['avance']
        # command = Commands.mov_to_pos
        # msg_id = self.get_message_id()
        # ref = ctrl_vars.ROSCADO_CONSTANTES['posicion_de_aproximacion']
        # header, data = build_msg(
        #     command,
        #     ref = ref,
        #     ref_rate = ctrl_vars.ROSCADO_CONSTANTES['velocidad_en_vacio'],
        #     msg_id = msg_id,
        #     eje = axis)
        # # MANDA EL MENSAJE
        # if not self.send_message(header, data):
        #     return False
        
        # # VERIFICA POSICIÓN
        # if not self.wait_for_lineal_mov(ref):
        #     return False
        
        # roscado_delta_time_paso5=datetime.now()-roscado_start_time
        # print('Delta Time Paso 5: ', roscado_delta_time_paso5)

        # print("ROSCADO - Paso 5 - Avanzar a pos y vel de aproximacion")

   
        # *** Paso 7 - Pone en Enable el husillo
        if ws_vars.MicroState.master_running == False or ws_vars.MicroState.iteration <= 1:
            command = Commands.power_on
            axis = ctrl_vars.AXIS_IDS['giro']
            msg_id = self.get_message_id()
            header = build_msg(command, eje=axis, msg_id=msg_id)

            if not self.send_message(header):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 7 - Pone en Enable el husillo')
                return False
            
            # VERIFICA EL ESTADO DEL EJE
            target_state = msg_app.StateMachine.EST_INITIAL
            if not self.wait_for_axis_state(target_state, axis):
                ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 7 - Pone en Enable el husillo')
                return False

            roscado_delta_time_paso7=datetime.now()-roscado_start_time
            print('Delta Time Paso 7: ', roscado_delta_time_paso7)

            print('ROSCADO - Paso 7 - Pone en Enable el husillo')



        # *** Paso 8 - Pone Sincronizado ON
        if ws_vars.MicroState.master_running == False or ws_vars.MicroState.iteration <= 1:
            command = Commands.sync_on
            axis = ctrl_vars.AXIS_IDS['avance']
            paso = ctrl_vars.ROSCADO_CONSTANTES['paso_de_rosca']
            header, data = build_msg(command, eje=axis, msg_id=msg_id, paso=paso)

            if not self.send_message(header, data):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 8 - Pone Sincronizado ON')
                return False
            print("SYNC ON SENT")
            
            # VERIFICA EL ESTADO DEL EJE
            # *** REVISAR *** NO AVISA SI DA ERROR EL SYNC OM
            state = ws_vars.MicroState.axis_flags[axis]['sync_on']
            while not state:
                state = ws_vars.MicroState.axis_flags[axis]['sync_on']
                time.sleep(self.wait_time)
            
            if self.wait_for_axis_state(msg_app.StateMachine.EST_INITIAL, axis) == False:
                ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 8 - Error en condicion inical de eje de avance')
                print('ROSCADO PASO 8 - Error en condicion inical de eje de avance')
                return False

            roscado_delta_time_paso8=datetime.now()-roscado_start_time
            print('Delta Time Paso 8: ', roscado_delta_time_paso8)

            print("ROSCADO - PASO 8 - Pone Sincronizado ON")



        # *** Paso 9.0 - Avanzar a pos y vel final roscando

        # comienza a graficar
        ws_vars.MicroState.graph_flag = True 
        
        # ARMA EL MENSAJE
        axis = ctrl_vars.AXIS_IDS['avance']
        command = Commands.mov_to_pos
        msg_id = self.get_message_id()
        time.sleep(0.25)  # timer TS
        ref = ctrl_vars.ROSCADO_CONSTANTES['posicion_final_de_roscado']
        header, data = build_msg(
            command,
            ref = ref,
            ref_rate = ctrl_vars.ROSCADO_CONSTANTES['velocidad_de_roscado'],
            msg_id = msg_id,
            eje = axis)
        
        # MANDA EL MENSAJE
        if not self.send_message(header, data):
            ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 9.0 - Avanzar a pos y vel final roscando')
            return False
        
        roscado_delta_time_paso90=datetime.now()-roscado_start_time
        print('Delta Time Paso 9.0: ', roscado_delta_time_paso90)

        print("ROSCADO - PASO 9.0 - Avanzar a pos y vel final roscando")



        # *** Paso 9.1 - Dejar boquilla en centro cerrado

        # espera que se llene el pistón
        time.sleep(2)

        # manda comando para aislar el pistón
        boquilla = self.get_current_boquilla_roscado()
        key_1 = 'cerrar_boquilla_' + str(boquilla)
        key_2 = 'abrir_boquilla_' + str(boquilla)
        group = 1
        self.send_pneumatic(key_1, group, 0, key_2, 0)
        
        time.sleep(2) #espera que se accione las EV que dejan el pistón aislado

        roscado_delta_time_paso_9_1=datetime.now()-roscado_start_time
        print('Delta Time Paso 9.1: ', roscado_delta_time_paso_9_1)

        print("ROSCADO - PASO 9.1 - Dejar boquilla en centro cerrado")



        # *** Paso 9.2 - Presurizar OFF
        ws_vars.MicroState.roscado_allow_presure_off = True

        #espera tener el flag allow_presure_off de carga en true
        load_id = ctrl_vars.ROUTINE_IDS['carga']
        load_running = RoutineInfo.objects.get(name=ctrl_vars.ROUTINE_NAMES[load_id]).running == 1

        if load_running:
            if self.wait_presure_off_allowed(load_id) == False:
                ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 9.2 - Presurizar OFF, no tiene flag allow_presure_off de carga')
                return False

        key = 'presurizar'
        group = 1
        self.send_pneumatic(key, group, 0)

        roscado_delta_time_paso_9_2=datetime.now()-roscado_start_time
        print('Delta Time Paso 9.2: ', roscado_delta_time_paso_9_2)

        print('ROSCADO - Paso 9.2 - Presurizar OFF')



        # *** Paso 9.3 - VERIFICA POS FINAL DE ROSCADO (PASO 9.0)
        if not self.wait_for_lineal_mov(ref):
            ws_vars.MicroState.err_messages.append('Error POS - ROSCADO - Paso 9.3 - VERIFICA POS FINAL DE ROSCADO (PASO 9.0)')
            return False
        
        roscado_delta_time_paso10=datetime.now()-roscado_start_time
        print('Delta Time Paso 9.3: ', roscado_delta_time_paso10)

        print("ROSCADO - PASO 9.3 - VERIFICA POS FINAL DE ROSCADO (PASO 9.0)")

        # *** Paso 11 - Avanzar a pos y vel de salida de rosca
        # ARMA EL MENSAJE
        print("ROSCADO - Paso 11 - Avanzar a pos y vel de salida de rosca")
        axis = ctrl_vars.AXIS_IDS['avance']
        command = Commands.mov_to_pos
        msg_id = self.get_message_id()
        ref = ctrl_vars.ROSCADO_CONSTANTES['posicion_salida_de_roscado']
        header, data = build_msg(
            command,
            ref = ref,
            ref_rate = ctrl_vars.ROSCADO_CONSTANTES['velocidad_de_retraccion'],
            msg_id = msg_id,
            eje = axis)

        # MANDA EL MENSAJE
        #time.sleep(20)
        print("mando mensaje en paso 11")
        if not self.send_message(header, data):
            ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 11 - Avanzar a pos y vel de salida de rosca')
            return False
        
        # VERIFICA POSICION
        print("verifica posicion en paso 11")
        if not self.wait_for_lineal_mov(ref):
            ws_vars.MicroState.err_messages.append('Error POS - ROSCADO - Paso 11 - Verifica pos de salida de rosca')
            return False
        
        roscado_delta_time_paso11=datetime.now()-roscado_start_time
        print('Delta Time Paso 11: ', roscado_delta_time_paso11)

        



        print("ROSCADO - Paso 11 - Avanzar a pos y vel de salida de rosca")



        # *** Paso 12 - Sincronizado OFF
        if ws_vars.MicroState.master_running == False:
            command = Commands.sync_off
            axis = ctrl_vars.AXIS_IDS['avance']
            header = build_msg(command, eje=axis, msg_id=msg_id)

            if not self.send_message(header):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 12 - Sincronizado OFF')
                return False

            # VERIFICA EL ESTADO DEL EJE
            # *** REVISAR *** NO AVISA SI DA ERROR EL SYNC OFF
            state = ws_vars.MicroState.axis_flags[axis]['sync_on']
            while state:
                state = ws_vars.MicroState.axis_flags[axis]['sync_on']
                time.sleep(self.wait_time)
            
            roscado_delta_time_paso12=datetime.now()-roscado_start_time
            print('Delta Time Paso 12: ', roscado_delta_time_paso12)

            print('ROSCADO - Paso 12 - Sincronizado OFF')



        # *** Paso 13 - Enable husillo OFF
        if ws_vars.MicroState.master_running == False:
            command = Commands.power_off
            axis = ctrl_vars.AXIS_IDS['giro']
            drv_flag = msg_base.DrvFbkDataFlags.ENABLED
            msg_id = self.get_message_id()
            header = build_msg(command, eje=axis, msg_id=msg_id)

            if not self.send_message(header):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 13 - Enable husillo OFF')
                return False
        
            # VERIFICA EL ESTADO DEL EJE
            if not self.wait_for_drv_flag(drv_flag, axis, 0):
                ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 13 - Enable husillo OFF')
                return False

            roscado_delta_time_paso13=datetime.now()-roscado_start_time
            print('Delta Time Paso 13: ', roscado_delta_time_paso13)

            print('ROSCADO - Paso 13 - Enable husillo OFF')



        # *** Paso 13.1 - Abrir válvula de boquilla hidráulica
        boquilla = self.get_current_boquilla_roscado()
        key_1 = 'abrir_boquilla_' + str(boquilla)
        key_2 = 'cerrar_boquilla_' + str(boquilla)
        group = 1
        self.send_pneumatic(key_1, group, 1, key_2, 0)

        roscado_delta_time_paso131=datetime.now()-roscado_start_time
        print('Delta Time Paso 13.1: ', roscado_delta_time_paso131)

        print('ROSCADO - Paso 13.1 - Abrir válvula de boquilla hidráulica')



        # # *** Paso 14 - Avance a posicion de inicio

        # # ARMA EL MENSAJE
        # axis = ctrl_vars.AXIS_IDS['avance']
        # command = Commands.mov_to_pos
        # msg_id = self.get_message_id()
        # ref = ctrl_vars.ROSCADO_CONSTANTES['posicion_de_inicio']
        # header, data = build_msg(
        #     command,
        #     ref = ref,
        #     ref_rate = ctrl_vars.ROSCADO_CONSTANTES['velocidad_en_vacio'],
        #     msg_id = msg_id,
        #     eje = axis)
        
        # # MANDA EL MENSAJE
        # if not self.send_message(header, data):
        #     return False

        # # VERIFICA POSICION
        # if not self.wait_for_lineal_mov(ref):
        #     return False

        # roscado_delta_time_paso14=datetime.now()-roscado_start_time
        # print('Delta Time Paso 14: ', roscado_delta_time_paso14)

        # print('ROSCADO - Paso 14 - Avance a posicion de inicio')



        # *** Paso 15 - Apagar bomba solube si está en semiautomático o configurado por paramtreo
        if ws_vars.MicroState.master_running == False or ctrl_vars.ROSCADO_CONSTANTES['soluble_intermitente'] == 1:
            key = 'encender_bomba_soluble'
            group = 1

            if not self.send_pneumatic(key, group, 0):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 15 - Apagar bomba solube')
                return False

            roscado_delta_time_paso15 = datetime.now() - roscado_start_time
            print('Delta Time Paso 15: ', roscado_delta_time_paso15)

            print("ROSCADO - Paso 15 - Apagar bomba solube si está en semiautomático")



        # *** Paso 16 - Retira acople lubricante
        key = 'expandir_acople_lubric'
        wait_key = 'acople_lubric_contraido'
        group = 1
        wait_group = 1

        if not self.send_pneumatic(key, group, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 16 - Retira acople lubricante')
            return False
        
        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 16 - Retira acople lubricante')
            return False

        roscado_delta_time_paso16=datetime.now()-roscado_start_time
        print('Delta Time Paso 16: ', roscado_delta_time_paso16)

        print("ROSCADO - Paso 16 - Retira acople lubricante")



        # *** Paso 17 - Contraer cerramiento de roscado
        key = 'expandir_cerramiento_roscado'
        wait_key = 'cerramiento_roscado_contraido'
        group = 0
        wait_group = 1

        if not self.send_pneumatic(key, group, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 17 - Contraer cerramiento roscado')
            return False
        
        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 17 - Contraer cerramiento roscado')
            return False

        roscado_delta_time_paso17 = datetime.now() - roscado_start_time
        print('Delta Time Paso 17: ', roscado_delta_time_paso17)

        print("ROSCADO - Paso 17 - Contraer cerramiento de roscado")


        # *** Paso 18 - Cerrar boquilla hidráulica. Poner abrir y cerrar en OFF
        # key_1 = 'cerrar_boquilla_' + str(boquilla)
        # key_2 = 'abrir_boquilla_' + str(boquilla)
        # group = 1
        # self.send_pneumatic(key_1, group, 0, key_2, 0)
        # print('CERRAR VALVULA HIDRAULICA')
        # print('CARGA - Paso 18 - Cerrar boquilla hidráulica. Poner abrir y cerrar en OFF')
        # time.sleep(1)



        #**** CONTADOR DE CUPLAS ROSCADAS ***
        roscado_contador = int(ctrl_vars.ROSCADO_CONSTANTES['roscado_contador'])
        params = Parameter.objects.all()
        part_model = param_vars.SELECTED_MODEL
        cont = params.filter(part_model=part_model).get(name='roscado_contador')
        cont.value += 1
        print('cont: ', roscado_contador)
        cont.save()
        update_roscado_params()
       #**** CONTADOR DE CUPLAS ROSCADAS ***

        ws_vars.MicroState.roscado_ongoing = False #baja flag de rutina roscado corriendo


        
        print("ROSCADO - FIN RUTINA")
        ws_vars.MicroState.log_messages.append('ROSCADO - Fin de rutina')
        return True



# ******************** HOMING ********************
    def routine_homing(self):

        # Paso 0 - Condiciones iniciales
        init_conditions_error_messages = ctrl_fun.check_init_conditions_homing()
        if init_conditions_error_messages:
            print('\nError en condiciones iniciales de homing')
            err_msg = 'Error en condiciones iniciales de homing'
            ws_vars.MicroState.err_messages.append(err_msg)
            for err in init_conditions_error_messages:
                ws_vars.MicroState.err_messages.append(err)
                print(err)
            return False

        print('HOMING - Paso 0 - Condiciones iniciales')
        ws_vars.MicroState.log_messages.append('HOMING - Inicio rutina')



        # Paso 0.1 - Encender bomba hidráulica
        key = 'encender_bomba_hidraulica'
        group = 1
        if not self.send_pneumatic(key, group, 1):
            ws_vars.MicroState.err_messages.append('Error Comnando - HOMING - Paso 0.1 - Encender bomba hidráulica')
            return False
        ws_vars.MicroState.log_messages.append('HOMING - Paso 0.1 - Encender bomba hidráulica')
        print('HOMING - Paso 0.1 - Encender bomba hidráulica')



        # Paso 1 - Cerado eje avance
        command = Commands.run_zeroing
        axis = ctrl_vars.AXIS_IDS['avance']
        msg_id = self.get_message_id()
        header = build_msg(command, msg_id=msg_id, eje=axis)

        if not self.send_message(header):
            ws_vars.MicroState.err_messages.append('Error Comnando - HOMING - Paso 1 - Cerado eje avance')
            return False

        state = ws_vars.MicroState.axis_flags[axis]['home_switch']
        while not state:
            state = ws_vars.MicroState.axis_flags[axis]['home_switch']
            time.sleep(self.wait_time)
        print('HOME SW ACTIVADO')

        ws_vars.MicroState.log_messages.append('HOMING - Paso 1 - Cerado eje avance')
        print('HOMING - Paso 1 - Cerado eje avance')



        # Paso 1.1 - Chequeo cero
        print('Paso 1.1 - En la instrucción que sigue se suele parar la primera ves que se ejecuta')
        
        if not self.wait_for_lineal_mov(0):
            ws_vars.MicroState.err_messages.append('Error POS - HOMING - Paso 1.1 - Chequeo cero')
            time.sleep(1)
            return False

        print('Paso 1.1 - Pasó bien instrucción con problema')

        time.sleep(10)
        print('sleep')

        ws_vars.MicroState.log_messages.append('HOMING - Paso 1.1 - Chequeo cero')
        print('HOMING - Paso 1.1 - Chequeo cero')
        


        # Paso 1.2 - Mover a posición de inicio
        eje_avance = ctrl_vars.AXIS_IDS['avance']
        pos_inicio = ctrl_vars.ROSCADO_CONSTANTES['posicion_de_inicio']

        if not self.mov_to_pos_lineal(pos_inicio):
            ws_vars.MicroState.err_messages.append('Error Comando - HOMING - Paso 1.2 - Mover a posición de inicio')
            return False

        print('Mov to pos')
        time.sleep(2)
        print('Posicion actual de paso 1.2:', ws_vars.MicroState.axis_measures[eje_avance]['pos_fil'])

        if not self.wait_for_lineal_mov(pos_inicio):
            ws_vars.MicroState.err_messages.append('Error POS - HOMING - Paso 1.2 - Mover a posición de inicio')
            return False

        ws_vars.MicroState.log_messages.append('HOMING - Paso 1.2 - Mover a posición de inicio')
        print('HOMING - Paso 1.2 - Mover a posición de inicio')



        # Paso 2 - Liberar plato
        key_1 = 'contraer_clampeo_plato'
        key_2 = 'expandir_clampeo_plato'

        if not self.send_pneumatic(key_1, 1, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - HOMING - Paso 2 - Liberar plato')
            return False
        
        if not self.wait_for_remote_in_flag('clampeo_plato_contraido', 1):
            ws_vars.MicroState.err_messages.append('Error Flag - HOMING - Paso 2 - Liberar plato')
            return False

        ws_vars.MicroState.log_messages.append('HOMING - Paso 2 - Liberar plato')
        print('HOMING - Paso 2 - Liberar plato')



        # Paso 2.1 - Encender servo
        command = Commands.power_on
        axis = ctrl_vars.AXIS_IDS['carga']
        msg_id = self.get_message_id()
        header = build_msg(command, eje=axis, msg_id=msg_id)

        if not self.send_message(header):
            ws_vars.MicroState.err_messages.append('Error Comando - HOMING - Paso 2.1 - Encender servo')
            return False
        
        target_state = msg_app.StateMachine.EST_INITIAL

        if not self.wait_for_axis_state(target_state, axis):
            ws_vars.MicroState.err_messages.append('Error Flag - HOMING - Paso 2.1 - Encender servo')
            return False

        ws_vars.MicroState.log_messages.append('HOMING - Paso 2.1 - Encender servo')
        print('HOMING - Paso 2.1 - Encender servo')



        # Paso 3 - Cerado eje carga
        print("CERAR EJE CARGA")
        command = Commands.run_zeroing
        axis = ctrl_vars.AXIS_IDS['carga']
        msg_id = self.get_message_id()
        header = build_msg(command, msg_id=msg_id, eje=axis)

        if not self.send_message(header):
            ws_vars.MicroState.err_messages.append('Error Comando - HOMING - Paso 3 - Cerado eje carga')
            return False

        ws_vars.MicroState.log_messages.append('HOMING - Paso 3 - Cerado eje carga')
        print('HOMING - Paso 3 - Cerado eje carga')



        # Paso 4.1 - Home switch activado
        state = ws_vars.MicroState.axis_flags[axis]['home_switch']
        while not state:
            state = ws_vars.MicroState.axis_flags[axis]['home_switch']
            # print(state)
            time.sleep(0.01)

        ws_vars.MicroState.log_messages.append('HOMING - Paso 4.1 - Home switch activado')
        print('HOMING - Paso 4.1 - Home switch activado')



        # Paso 4.2 - Home switch desactivado
        while state:
            state = ws_vars.MicroState.axis_flags[axis]['home_switch']
            time.sleep(0.01)

        ws_vars.MicroState.log_messages.append('HOMING - Paso 4.2 - Home switch desactivado')
        print('HOMING - Paso 4.2 - Home switch desactivado')



        # Paso 4.3 - Fin comando homing
        time.sleep(1)
        current_pos = round(ws_vars.MicroState.axis_measures[axis]['pos_abs'], 2)
        prev_pos = -1.0
        while current_pos != prev_pos:
            print(current_pos, prev_pos)
            prev_pos = current_pos
            time.sleep(self.wait_time*3)
            current_pos = round(ws_vars.MicroState.axis_measures[axis]['pos_abs'], 2)
        print(current_pos)
        
        ws_vars.MicroState.log_messages.append('HOMING - Paso 4.3 - Fin comando homing')
        time.sleep(2)
        print('HOMING - Paso 4.3 - Fin comando homing')



        # Paso 4.4 - Gira posición buscando leva
        command = Commands.mov_to_pos
        msg_id = self.get_message_id()
        header, data = build_msg(command, ref=45, ref_rate=5, msg_id=msg_id, eje=axis)

        if not self.send_message(header, data):
            ws_vars.MicroState.err_messages.append('Error Comando - HOMING - Paso 4.4 - Gira posición buscando leva')
            return False
        
        ws_vars.MicroState.log_messages.append('HOMING - Paso 4.4 - Gira posición buscando leva')
        print('HOMING - Paso 4.4 - Gira posición buscando leva')



        # Paso 4.5 - Posición en leva
        state = ws_vars.MicroState.axis_flags[axis]['home_switch']
        while not state:
            state = ws_vars.MicroState.axis_flags[axis]['home_switch']
            time.sleep(self.wait_time)
        pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
        print('Espera sensor home activado')
        print("POSICION EN CHAPA", pos)

        ws_vars.MicroState.log_messages.append('HOMING - Paso 4.5 - Posición en leva')
        print('HOMING - Paso 4.5 - Posición en leva')



        # Paso 4.6 - Detener eje
        command = Commands.stop
        msg_id = self.get_message_id()
        header = build_msg(command, msg_id=msg_id, eje=axis)

        if not self.send_message(header):
            ws_vars.MicroState.err_messages.append('Error Comando - HOMING - Paso 4.6 - Detener eje')
            return False

        time.sleep(0.5)
        print('Detener eje')
        ws_vars.MicroState.log_messages.append('HOMING - Paso 4.6 - Detener eje')
        print('HOMING - Paso 4.6 - Detener eje')



        # Paso 4.7 - Configura offset cero
        header = None
        data = None
        if pos > ctrl_vars.HOMING_CONSTANTES['position_positive_7']:
            print('Caso 1, p0=7.2')
            command = Commands.drv_set_zero_abs
            msg_id = self.get_message_id()
            header, data = build_msg(command, msg_id=msg_id, zero=7.2, eje=axis)
        elif pos >= ctrl_vars.HOMING_CONSTANTES['position_mid_low'] and pos <= ctrl_vars.HOMING_CONSTANTES['position_mid_high']:
            print('Caso 2, p0=0')
        elif pos < ctrl_vars.HOMING_CONSTANTES['position_negative_7']:
            print('Caso 3, p0=-7.2')
            command = Commands.drv_set_zero_abs
            msg_id = self.get_message_id()
            header, data = build_msg(command, msg_id=msg_id, zero=-7.2, eje=axis)
        if header:
            print("SENDING P0")
            print(data, data.zero)

            if not self.send_message(header, data):
                ws_vars.MicroState.err_messages.append('Error Comando - HOMING - Paso 4.7 - Configura offset cero')
                return False

        time.sleep(2)
        command = Commands.mov_to_pos
        msg_id = self.get_message_id()
        header, data = build_msg(command, ref=0, ref_rate=40, msg_id=msg_id, eje=axis)

        if not self.send_message(header, data):
            ws_vars.MicroState.err_messages.append('Error Comando - HOMING - Paso 4.7 - Mueve eje a pos 0')
            return False
        

        ws_vars.MicroState.log_messages.append('HOMING - Paso 4.7 - Configura offset cero')
        print('HOMING - Paso 4.7 - Configura offset cero')



        # Paso 5 - Clampea plato
        key_1 = 'expandir_clampeo_plato'
        key_2 = 'contraer_clampeo_plato'
        group = 1
        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - HOMING - Paso 5 - Clampea plato')
            return False
        
        if not self.wait_for_remote_in_flag('clampeo_plato_expandido', group):
            ws_vars.MicroState.err_messages.append('Error Flag - HOMING - Paso 5 - Clampea plato')
            return False

        ws_vars.MicroState.log_messages.append('HOMING - Paso 5 - Clampea plato')
        print('HOMING - Paso 5 - Clampea plato')



        # Paso 6 - Power off servo indexado
        command = Commands.power_off
        drv_flag = msg_base.DrvFbkDataFlags.ENABLED
        axis = ctrl_vars.AXIS_IDS['carga']
        msg_id = self.get_message_id()
        header = build_msg(command, eje=axis, msg_id=msg_id)
        if not self.send_message(header):
            ws_vars.MicroState.err_messages.append('Error Comando - HOMING - Paso 6 - Power off servo indexado')
            return False
        
        if not self.wait_for_drv_flag(drv_flag, axis, 0):
            ws_vars.MicroState.err_messages.append('Error Flag - HOMING - Paso 6 - Power off servo indexado')
            return False

        ws_vars.MicroState.log_messages.append('HOMING - Paso 6 - Power off servo indexado')
        print('HOMING - Paso 6 - Power off servo indexado')



        print('HOMING - FIN RUTINA')
        ws_vars.MicroState.log_messages.append('HOMING - Fin rutina')
        ws_vars.MicroState.homing_ongoing = False
        return True
       


    def send_message(self, header, data=None):
        if self.ch_info:
            if data:
                send_message(header, self.ch_info, data)
            else:
                send_message(header, self.ch_info)
            return True
        print('send msg false')
        return False


# ******************** Chequea cupla presente en carga ********************
    def check_part_present_carga(self):
        if ws_vars.MicroState.first_run_load == False:
            return 0

        # Paso 1.1 - Abrir válvula de boquilla hidráulica
        boquilla = self.get_current_boquilla_carga()
        key_1 = 'cerrar_boquilla_' + str(boquilla)
        key_2 = 'abrir_boquilla_' + str(boquilla)
        group = 1
        self.send_pneumatic(key_1, group, 0, key_2, 1)
        print('CARGA - Paso 1.1 - Abrir válvula de boquilla hidráulica')


        #giro a boquilla plato
        key_1 = 'contraer_brazo_cargador'
        key_2 = 'expandir_brazo_cargador'
        wait_key = 'brazo_cargador_contraido'
        group = 0
        wait_group = 0

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comnando - CARGA INICIA - Paso 6 - Contraer giro brazo cargador')
            return False
        

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - CARGA INICIA - Paso 6 - Contraer giro brazo cargador')
            return False
        

        # Paso 2 - Expandir horizontal puntera carga
        key_1 = 'expandir_puntera_carga'
        key_2 = 'contraer_puntera_carga'
        wait_key = 'puntera_carga_contraida'
        group = 0

        print("EXPANDIR PUNTERA CARGA")
        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - CARGA INICIA - Paso 2 - Expandir horizontal puntera carga')
            return False

        if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - CARGA INICIA - Paso 2 - Expandir horizontal puntera carga')
            return False

        time.sleep(3)
        print('CARGA - Paso 2 - Expandir horizontal puntera carga')


        # Paso 3 - Boquilla carga contraida
        key = 'contraer_boquilla_carga'
        wait_key = 'boquilla_carga_contraida'
        group = 0
        wait_group = 0
        if not self.send_pneumatic(key, group, 1):
            ws_vars.MicroState.err_messages.append('Error Comando - CARGA INICIA - Paso 3 - Boquilla carga contraida')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - CARGA INICIA - Paso 3 - Boquilla carga contraida')
            return False
        
        print('CARGA - Paso 3 - Boquilla carga contraida')
        time.sleep(2)


        # Paso 5 - Contraer horizontal puntera carga
        key_1 = 'contraer_puntera_carga'
        key_2 = 'expandir_puntera_carga'
        wait_key = 'puntera_carga_contraida'
        group = 0
        wait_group = 0

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comnando - CARGA INICIA - Paso 5 - Contraer horizontal puntera carga')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - CARGA INICIA - Paso 5 - Contraer horizontal puntera carga')
            return False

        print('CARGA - Paso 5 - Contraer horizontal puntera carga')


        # Paso 4 - Verificar flags pieza en boquilla carga
        key = 'pieza_en_boquilla_carga'
        if ws_vars.MicroState.rem_i_states[1][key]:
            #CHEQUEA PIEZA EN BOQUILLA
            # ws_vars.MicroState.err_messages.append('Error Flag - CARGA INICIA - Paso 4 - Verificar flags pieza en boquilla carga')
            #si no tiene pieza hace giro hacia el vertical de carga empieza rutina de carga
            # Paso 16 - Expandir giro brazo cargador
            key_1 = 'expandir_brazo_cargador'
            key_2 = 'contraer_brazo_cargador'
            wait_key = 'brazo_cargador_expandido'
            group = 0
            wait_group = 0
        
            if not self.send_pneumatic(key_1, group, 1, key_2, 0):
                ws_vars.MicroState.err_messages.append('Error Comnando - CARGA INICIA - Paso 16 - Expandir giro brazo cargador')
                return False
            
            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA INICIA - Paso 16 - Expandir giro brazo cargador')
                return False
            print('CARGA - Paso 16 - Expandir giro brazo cargador')

            # Paso 9 - Boquilla carga extendida
            key = 'contraer_boquilla_carga'
            wait_key = 'boquilla_carga_expandida'
            group = 0
            wait_group = 0
            if not self.send_pneumatic(key, group, 0):
                ws_vars.MicroState.err_messages.append('Error Comnando - CARGA INICIA - Paso 9 - Boquilla carga extendida')
                return False

            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - CARGA INICIA - Paso 9 - Boquilla carga extendida')
                return False
            print('CARGA - Paso 9 - Boquilla carga extendida')

            # Create a Tkinter window
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.attributes('-topmost', True)  # Set the window to be always on top
            root.update()  # Update the window to apply the topmost attribute

            # Show the pymsgbox confirmation dialog
            response = pymsgbox.confirm('No se detecto pieza en plato, desea ejecutar rutina de carga?', 'Confirmation', buttons=['Yes', 'No'])

            # Check the response and take action accordingly
            if response == 'Yes':
                print('You selected Yes.')
                step = 0
                # name = pymsgbox.prompt('What is your name?')
                # print(f'Your name is {name}.')
            else:
                print('You selected No.')
                ws_vars.MicroState.err_messages.append('Pieza en plato confirmada por usuario, no se ejecuta rutina de carga')
                return False

            # Destroy the Tkinter window
            root.destroy()

        else:
            print("PIEZA EN BOQUILLA carga")
            #va a paso 8 si hay cupla, para que la vuelva a meter}
            step = 8

        
        ws_vars.MicroState.first_run_load = False
        return step


# ******************** Chequea cupla presente en descarga ********************
    def check_part_present_descarga(self):
        if ws_vars.MicroState.first_two_runs_unload > 2:
            return 0


        # Paso 1 - Expandir horizontal puntera descarga
        unload_init_flags = [
            ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'],          # Plato clampeado
        ]

        if False in unload_init_flags:
            ws_vars.MicroState.err_messages.append('Error - DESCARGA - Paso 1 - Verificar clampeo plato')
            return False
        
        pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
        if pos not in ctrl_vars.LOAD_STEPS:
            # print('Error en posicion de cabezal')
            ws_vars.MicroState.err_messages.append('Error - DESCARGA - Paso 1 - Verificar posicion de cabezal')
            return False

        key_1 = 'expandir_puntera_descarga'
        key_2 = 'contraer_puntera_descarga'
        wait_key = 'puntera_descarga_contraida'
        group = 0
        wait_group = 0
        print("EXPANDIR HORIZONTAL PUNTERA DESCARGA")

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 1 - Expandir horizontal puntera descarga')
            return False

        if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 1 - Expandir horizontal puntera descarga')
            return False

        time.sleep(5)
        print('DESCARGA - Paso 1 - Expandir horizontal puntera descarga')

        # Paso 3 - Boquilla descarga contraida
        key = 'contraer_boquilla_descarga'
        wait_key = 'boquilla_descarga_expandida'
        group = 0
        wait_group = 0
        if not self.send_pneumatic(key, group, 1):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 3 - Boquilla descarga contraida')
            return False
        if not self.wait_for_not_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 3 - Boquilla descarga contraida')
            return False

        time.sleep(4) #timer ts : espera a que termine de abrir la boquilla
        print('contraer_boquilla_descarga')
        print('DESCARGA - Paso 3 - Boquilla descarga contraida')


        # Paso 5 - Puntera horizonal descarga contraída
        key_1 = 'contraer_puntera_descarga'
        key_2 = 'expandir_puntera_descarga'
        wait_key = 'puntera_descarga_contraida'
        group = 0
        wait_group = 0

        if not self.send_pneumatic(key_1, group, 1, key_2, 0):
            ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 5 - Puntera horizonal descarga contraída')
            return False

        if not self.wait_for_remote_in_flag(wait_key, wait_group):
            ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 5 - Puntera horizonal descarga contraída')
            return False

        print("DESCARGA - Paso 5 - PUNTERA HORIZONTAL DESCARGA CONTRAIDA")



        # Paso 6.1 - Verificar cupla en boquilla descarga. Si no está arroja cartel para indexar y seguir rutina de automatico
        if ws_vars.MicroState.rem_i_states[1]['pieza_en_boquilla_descarga']:
            # Paso 13 - Abrir boquilla descarga
            key = 'contraer_boquilla_descarga'
            wait_key = 'boquilla_descarga_expandida'
            group = 0
            wait_group = 0

            if not self.send_pneumatic(key, group, 0):
                ws_vars.MicroState.err_messages.append('Error Comando - DESCARGA - Paso 13 - Abrir boquilla descarga')
                return False

            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - DESCARGA - Paso 13 - Abrir boquilla descarga')
                return False
            time.sleep(1)

            print('DESCARGA - PASO 13 - Abrir boquilla descarga')
            
            #ws_vars.MicroState.err_messages.append('Error Flag - INIT DESCARGA - Paso 6.1 - Cupla no presente en plato posicion descarga')
            # running_ids = self.get_running_routines()
            # descarga_id = ctrl_vars.ROUTINE_IDS['descarga']

            # if descarga_id in running_ids:
            #     print('Rutina master, esperar fin de descarga')
            #     while descarga_id in running_ids and ws_vars.MicroState.master_stop == False:
            #         running_ids = self.get_running_routines()
            #         time.sleep(self.wait_rtn_time)

            # Create a Tkinter window
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            root.attributes('-topmost', True)  # Set the window to be always on top
            root.update()  # Update the window to apply the topmost attribute

            # Show the pymsgbox confirmation dialog
            # response = pymsgbox.confirm('No se detecto pieza en plato posicion descarga, desea ejecutar rutina de indexado?', 'Confirmation', buttons=['Yes', 'No'])
            response = pymsgbox.confirm('Confirma que no hay pieza en el plato en posicion de descarga para seguir automatico?', 'Confirmation', buttons=['Yes', 'No'])

            # Check the response and take action accordingly
            if response == 'Yes':
                print('You selected Yes.')
                # Destroy the Tkinter window
                root.destroy()
                return True
                # name = pymsgbox.prompt('What is your name?')
                # print(f'Your name is {name}.')
            else:
                print('You selected No.')
                ws_vars.MicroState.err_messages.append('Pieza en plato confirmada por usuario, no se pudo descargar')
                # Destroy the Tkinter window
                root.destroy()
                return False
        else:
            print('CUPLA PRESENTE')
            step = 8

        
        ws_vars.MicroState.first_two_runs_unload += 1
        return step


# ******************** Rutina para salir roscando ********************
    def routine_exit_tapping(self):
        if ws_vars.MicroState.master_running == False:
            roscado_start_time = datetime.now() # es para sacar los tiempos de cada paso de la rutina roscado
            
            # *** Paso 3 - Presurizar ON
            ws_vars.MicroState.roscado_allow_presure_off = False
            key = 'presurizar'
            group = 1

            if not self.send_pneumatic(key, group, 1):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 3 - Presurizar ON')
                return False

            roscado_delta_time_paso3=datetime.now()-roscado_start_time
            print('Delta Time Paso 3: ', roscado_delta_time_paso3)
            
            print("ROSCADO - Paso 3 - Presurizar ON")



            # *** Paso 4 - accionar cerrar para presurizar boquilla hidráulica
            boquilla = self.get_current_boquilla_roscado()
            key_1 = 'cerrar_boquilla_' + str(boquilla)
            key_2 = 'abrir_boquilla_' + str(boquilla)
            group = 1
            self.send_pneumatic(key_1, group, 1, key_2, 0)

            roscado_delta_time_paso4=datetime.now()-roscado_start_time
            print('Delta Time Paso 4: ', roscado_delta_time_paso4)

            print("ROSCADO - Paso 4 - accionar cerrar para presurizar boquilla hidráulica")



            # *** Paso 7 - Pone en Enable el husillo
            command = Commands.power_on
            axis = ctrl_vars.AXIS_IDS['giro']
            msg_id = self.get_message_id()
            header = build_msg(command, eje=axis, msg_id=msg_id)

            if not self.send_message(header):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 7 - Pone en Enable el husillo')
                return False
            
            # VERIFICA EL ESTADO DEL EJE
            target_state = msg_app.StateMachine.EST_INITIAL
            if not self.wait_for_axis_state(target_state, axis):
                ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 7 - Pone en Enable el husillo')
                return False

            roscado_delta_time_paso7=datetime.now()-roscado_start_time
            print('Delta Time Paso 7: ', roscado_delta_time_paso7)

            print('ROSCADO - Paso 7 - Pone en Enable el husillo')

            # *** Paso 8 - Pone Sincronizado ON
            command = Commands.sync_on
            axis = ctrl_vars.AXIS_IDS['avance']
            paso = ctrl_vars.ROSCADO_CONSTANTES['paso_de_rosca']
            header, data = build_msg(command, eje=axis, msg_id=msg_id, paso=paso)

            if not self.send_message(header, data):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 8 - Pone Sincronizado ON')
                return False
            print("SYNC ON SENT")
            
            # VERIFICA EL ESTADO DEL EJE
            # *** REVISAR *** NO AVISA SI DA ERROR EL SYNC OM
            state = ws_vars.MicroState.axis_flags[axis]['sync_on']
            while not state:
                state = ws_vars.MicroState.axis_flags[axis]['sync_on']
                time.sleep(self.wait_time)
            
            if self.wait_for_axis_state(msg_app.StateMachine.EST_INITIAL, axis) == False:
                ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 8 - Error en condicion inical de eje de avance')
                print('ROSCADO PASO 8 - Error en condicion inical de eje de avance')
                return False

            roscado_delta_time_paso8=datetime.now()-roscado_start_time
            print('Delta Time Paso 8: ', roscado_delta_time_paso8)

            print("ROSCADO - PASO 8 - Pone Sincronizado ON")

            # # *** Paso 8 - Pone Sincronizado ON
            # # Parámetros adicionales
            # self.wait_time  = 0.1  # Tiempo de espera en segundos entre verificaciones
            # self.max_wait_time = 5  # Tiempo máximo de espera en segundos para activar sincronización
            # command = Commands.sync_on
            # axis = ctrl_vars.AXIS_IDS['avance']
            # paso = ctrl_vars.ROSCADO_CONSTANTES['paso_de_rosca']
            # header, data = build_msg(command, eje=axis, msg_id=msg_id, paso=paso)

            # if not self.send_message(header, data):
            #     ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 8 - Pone Sincronizado ON')
            #     return False
            # print("SYNC ON SENT")

            # # VERIFICA EL ESTADO DEL EJE
            # # *** REVISAR *** NO AVISA SI DA ERROR EL SYNC ON
            # state = ws_vars.MicroState.axis_flags[axis]['sync_on']
            # wait_time = 0
            # while not state:
            #     state = ws_vars.MicroState.axis_flags[axis]['sync_on']
            #     if not state:
            #         time.sleep(self.wait_time)
            #         wait_time += self.wait_time
            #         if wait_time > self.max_wait_time:
            #             ws_vars.MicroState.err_messages.append('Timeout - ROSCADO - Paso 8 - No se pudo activar sincronización')
            #             print('Timeout - No se pudo activar sincronización')
            #             return False
            
            # if not self.wait_for_axis_state(msg_app.StateMachine.EST_INITIAL, axis):
            #     ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 8 - Error en condición inicial de eje de avance')
            #     print('ROSCADO PASO 8 - Error en condición inicial de eje de avance')
            #     return False

            # roscado_delta_time_paso8 = datetime.now() - roscado_start_time
            # print('Delta Time Paso 8: ', roscado_delta_time_paso8)

            # print("ROSCADO - PASO 8 - Pone Sincronizado ON")

            # *** Paso 9.1 - Dejar boquilla en centro cerrado

            # espera que se llene el pistón
            time.sleep(2)

            # manda comando para aislar el pistón
            boquilla = self.get_current_boquilla_roscado()
            key_1 = 'cerrar_boquilla_' + str(boquilla)
            key_2 = 'abrir_boquilla_' + str(boquilla)
            group = 1
            self.send_pneumatic(key_1, group, 0, key_2, 0)
            
            time.sleep(2) #espera que se accione las EV que dejan el pistón aislado

            roscado_delta_time_paso_9_1=datetime.now()-roscado_start_time
            print('Delta Time Paso 9.1: ', roscado_delta_time_paso_9_1)

            print("ROSCADO - PASO 9.1 - Dejar boquilla en centro cerrado")



            # *** Paso 9.2 - Presurizar OFF
            ws_vars.MicroState.roscado_allow_presure_off = True

            #espera tener el flag allow_presure_off de carga en true
            load_id = ctrl_vars.ROUTINE_IDS['carga']
            load_running = RoutineInfo.objects.get(name=ctrl_vars.ROUTINE_NAMES[load_id]).running == 1

            if load_running:
                if self.wait_presure_off_allowed(load_id) == False:
                    ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 9.2 - Presurizar OFF, no tiene flag allow_presure_off de carga')
                    return False

            key = 'presurizar'
            group = 1
            self.send_pneumatic(key, group, 0)

            roscado_delta_time_paso_9_2=datetime.now()-roscado_start_time
            print('Delta Time Paso 9.2: ', roscado_delta_time_paso_9_2)

            print('ROSCADO - Paso 9.2 - Presurizar OFF')


            # *** Paso 11 - Avanzar a pos y vel de salida de rosca

            # ARMA EL MENSAJE
            axis = ctrl_vars.AXIS_IDS['avance']
            command = Commands.mov_to_pos
            msg_id = self.get_message_id()
            ref = ctrl_vars.ROSCADO_CONSTANTES['posicion_salida_de_roscado']
            header, data = build_msg(
                command,
                ref = ref,
                ref_rate = ctrl_vars.ROSCADO_CONSTANTES['velocidad_de_retraccion'],
                msg_id = msg_id,
                eje = axis)

            # MANDA EL MENSAJE
            if not self.send_message(header, data):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 11 - Avanzar a pos y vel de salida de rosca')
                return False
            
            # VERIFICA POSICION
            if not self.wait_for_lineal_mov(ref):
                ws_vars.MicroState.err_messages.append('Error POS - ROSCADO - Paso 11 - Verifica pos de salida de rosca')
                return False
            
            roscado_delta_time_paso11=datetime.now()-roscado_start_time
            print('Delta Time Paso 11: ', roscado_delta_time_paso11)

            print("ROSCADO - Paso 11 - Avanzar a pos y vel de salida de rosca")



            # *** Paso 12 - Sincronizado OFF
            command = Commands.sync_off
            axis = ctrl_vars.AXIS_IDS['avance']
            header = build_msg(command, eje=axis, msg_id=msg_id)

            if not self.send_message(header):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 12 - Sincronizado OFF')
                return False

            # VERIFICA EL ESTADO DEL EJE
            # *** REVISAR *** NO AVISA SI DA ERROR EL SYNC OFF
            state = ws_vars.MicroState.axis_flags[axis]['sync_on']
            while state:
                state = ws_vars.MicroState.axis_flags[axis]['sync_on']
                time.sleep(self.wait_time)
            
            roscado_delta_time_paso12=datetime.now()-roscado_start_time
            print('Delta Time Paso 12: ', roscado_delta_time_paso12)

            print('ROSCADO - Paso 12 - Sincronizado OFF')



            # *** Paso 13 - Enable husillo OFF
            
            command = Commands.power_off
            axis = ctrl_vars.AXIS_IDS['giro']
            drv_flag = msg_base.DrvFbkDataFlags.ENABLED
            msg_id = self.get_message_id()
            header = build_msg(command, eje=axis, msg_id=msg_id)

            if not self.send_message(header):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 13 - Enable husillo OFF')
                return False
        
            # VERIFICA EL ESTADO DEL EJE
            if not self.wait_for_drv_flag(drv_flag, axis, 0):
                ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 13 - Enable husillo OFF')
                return False

            roscado_delta_time_paso13=datetime.now()-roscado_start_time
            print('Delta Time Paso 13: ', roscado_delta_time_paso13)

            print('ROSCADO - Paso 13 - Enable husillo OFF')



            # *** Paso 13.1 - Abrir válvula de boquilla hidráulica
            boquilla = self.get_current_boquilla_roscado()
            key_1 = 'abrir_boquilla_' + str(boquilla)
            key_2 = 'cerrar_boquilla_' + str(boquilla)
            group = 1
            self.send_pneumatic(key_1, group, 1, key_2, 0)

            roscado_delta_time_paso131=datetime.now()-roscado_start_time
            print('Delta Time Paso 13.1: ', roscado_delta_time_paso131)

            print('ROSCADO - Paso 13.1 - Abrir válvula de boquilla hidráulica')



            # *** Paso 15 - Apagar bomba solube si está en semiautomático o configurado por paramtreo
            key = 'encender_bomba_soluble'
            group = 1

            if not self.send_pneumatic(key, group, 0):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 15 - Apagar bomba solube')
                return False

            roscado_delta_time_paso15 = datetime.now() - roscado_start_time
            print('Delta Time Paso 15: ', roscado_delta_time_paso15)

            print("ROSCADO - Paso 15 - Apagar bomba solube si está en semiautomático")



            # *** Paso 16 - Retira acople lubricante
            key = 'expandir_acople_lubric'
            wait_key = 'acople_lubric_contraido'
            group = 1
            wait_group = 1

            if not self.send_pneumatic(key, group, 0):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 16 - Retira acople lubricante')
                return False
            
            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 16 - Retira acople lubricante')
                return False

            roscado_delta_time_paso16=datetime.now()-roscado_start_time
            print('Delta Time Paso 16: ', roscado_delta_time_paso16)

            print("ROSCADO - Paso 16 - Retira acople lubricante")



            # *** Paso 17 - Contraer cerramiento de roscado
            key = 'expandir_cerramiento_roscado'
            wait_key = 'cerramiento_roscado_contraido'
            group = 0
            wait_group = 1

            if not self.send_pneumatic(key, group, 0):
                ws_vars.MicroState.err_messages.append('Error Comando - ROSCADO - Paso 17 - Contraer cerramiento roscado')
                return False
            
            if not self.wait_for_remote_in_flag(wait_key, wait_group):
                ws_vars.MicroState.err_messages.append('Error Flag - ROSCADO - Paso 17 - Contraer cerramiento roscado')
                return False

            roscado_delta_time_paso17 = datetime.now() - roscado_start_time
            print('Delta Time Paso 17: ', roscado_delta_time_paso17)

            print("ROSCADO - Paso 17 - Contraer cerramiento de roscado")

            
            print("ROSCADO - FIN RUTINA")
            ws_vars.MicroState.log_messages.append('ROSCADO - Fin de rutina')
            # return print("exit tampping handler function")
            return True



# ******************** HOMING AVANCE********************
    def routine_homing_avance(self):

        print('LIBERAR LINEAL AVANCE INICIADO')
        ws_vars.MicroState.log_messages.append('LIBERAR LINEAL AVANCE INICIADO')

        command = Commands.run_zeroing
        axis = ctrl_vars.AXIS_IDS['avance']
        msg_id = self.get_message_id()
        header = build_msg(command, msg_id=msg_id, eje=axis)

        if not self.send_message(header):
            ws_vars.MicroState.err_messages.append('Error Comnando - HOMING AVANCE')
            return False
      
        if not self.wait_for_lineal_mov(0):
            ws_vars.MicroState.err_messages.append('Error POS - HOMING AVANCE - Chequeo cero')
            return False

        print('LIBERAR LINEAL AVANCE FINALIZADO')
        ws_vars.MicroState.log_messages.append('LIBERAR LINEAL AVANCE FINALIZADO')
        return True



    def get_message_id(self):
        msg_id = ws_vars.MicroState.last_rx_header.get_msg_id() + 1
        ws_vars.MicroState.msg_id = msg_id
        return msg_id



    def send_pneumatic(self, key, group, bool_value, second_key=None, second_bool_value=None):
        command = Commands.rem_do_set
        header, data = ctrl_fun.set_rem_do(command, key, group, bool_value)
        if not self.send_message(header, data):
            return False
        if second_key:
            header, data = ctrl_fun.set_rem_do(command, second_key, group, second_bool_value)
            return self.send_message(header, data)
        return True



    def wait_for_remote_in_flag(self, flag_key, group):
        flag = ws_vars.MicroState.rem_i_states[group][flag_key]
        timer = 0
        stop_flags_ok = self.check_stop_flags(timeout=ctrl_vars.TIMEOUT_PNEUMATIC)
        while not flag and stop_flags_ok:     # Verifica que el flag está en HIGH
            flag = ws_vars.MicroState.rem_i_states[group][flag_key]
            time.sleep(self.wait_time)
            stop_flags_ok = self.check_stop_flags(timer=timer, timeout=ctrl_vars.TIMEOUT_PNEUMATIC)
            timer += self.wait_time
        if not flag:
            return False
        return True



    def wait_flag_presencia_cupla_en_cargador(self, flag_key, group): #AGREGADO 20220819 POR AP Y TS
        flag = ws_vars.MicroState.rem_i_states[group][flag_key]
        timer = 0
        stop_flags_ok = self.check_stop_flags(timeout=ctrl_vars.TIMEOUT_CARGA_CUPLA)
        while not flag and stop_flags_ok:     # Verifica que el flag está en HIGH
            flag = ws_vars.MicroState.rem_i_states[group][flag_key]
            time.sleep(self.wait_time)
            stop_flags_ok = self.check_stop_flags(timer=timer, timeout=ctrl_vars.TIMEOUT_CARGA_CUPLA)
            timer += self.wait_time
        if not flag:
            return False
        return True

    def wait_for_not_flag_tobogan_descargador(self, flag_key, group): #AGREGADO 20220819 POR AP Y TS
        flag = ws_vars.MicroState.rem_i_states[group][flag_key]
        timer = 0
        stop_flags_ok = self.check_stop_flags(timeout=ctrl_vars.TIMEOUT_CARGA_CUPLA)
        while flag and stop_flags_ok:     # Verifica que el flag está en HIGH
            flag = ws_vars.MicroState.rem_i_states[group][flag_key]
            time.sleep(self.wait_time)
            stop_flags_ok = self.check_stop_flags(timer=timer, timeout=ctrl_vars.TIMEOUT_CARGA_CUPLA)
            timer += self.wait_time
        if flag:
            return False
        return True



    def wait_for_not_remote_in_flag(self, flag_key, group):
        flag = ws_vars.MicroState.rem_i_states[group][flag_key]
        timer = 0
        stop_flags_ok = self.check_stop_flags(timeout=ctrl_vars.TIMEOUT_PNEUMATIC)
        while flag and stop_flags_ok:     # Verifica que el flag está en LOW
            flag = ws_vars.MicroState.rem_i_states[group][flag_key]
            time.sleep(self.wait_time)
            timer += self.wait_time
            stop_flags_ok = self.check_stop_flags(timer=timer, timeout=ctrl_vars.TIMEOUT_PNEUMATIC)
        if flag:
            return False
        return True



    def wait_for_axis_state(self, target_state, axis):
        current_state_value = ws_vars.MicroState.axis_flags[axis]['maq_est_val']
        timer = 0
        timeout = ctrl_vars.TIMEOUT_STATE_CHANGE
        err_msg='cambio de estado de eje'
        stop_flags_ok = self.check_stop_flags(err_msg=err_msg, timeout=timeout, axis=axis)
        
        while current_state_value != target_state and stop_flags_ok:
            current_state_value = ws_vars.MicroState.axis_flags[axis]['maq_est_val']
            time.sleep(self.wait_time)
            timer += self.wait_time
            stop_flags_ok = self.check_stop_flags(err_msg=err_msg, timer=timer, timeout=timeout, axis=axis)
        print('Estado eje:', current_state_value)
        if stop_flags_ok == False:
            return False

        if current_state_value != target_state:
            return False
        return True



    def move_step_load_axis(self):
        axis = ctrl_vars.AXIS_IDS['carga']
        pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
        steps = ctrl_vars.LOAD_STEPS
        current_step = None
        nex_step = None
        steps_count = len(steps)
        for i in range(steps_count):
            step = steps[i]
            if pos <= step + 2 and pos >= step - 2:
                current_step = i
                break
        if current_step == steps_count - 1:
            nex_step = 0
        else:
            nex_step = steps[current_step + 1]
        command = Commands.mov_to_pos
        msg_id = self.get_message_id()
        header, data = build_msg(command, ref=nex_step, ref_rate=ctrl_vars.COMMAND_REF_RATES['vel_carga'], msg_id=msg_id, eje=axis)

        if not self.send_message(header, data):
            return False
        
        pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
        print("POS:", pos)
        timer = 0
        stop_flags_ok = self.check_stop_flags(err_msg='indexado', timeout=ctrl_vars.TIMEOUT_LOAD, axis=axis)
        while not (pos >= nex_step - 1 and pos <= nex_step + 1) and stop_flags_ok:
            pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
            time.sleep(self.wait_time)
            timer += self.wait_time
            stop_flags_ok = self.check_stop_flags(err_msg='indexado', timer=timer, timeout=ctrl_vars.TIMEOUT_LOAD, axis=axis)

        if stop_flags_ok == False:
            return False

        return self.wait_for_axis_state(msg_app.StateMachine.EST_INITIAL, axis)



    def wait_for_lineal_mov(self, target_pos):
        axis = ctrl_vars.AXIS_IDS['avance']
        current_pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
        timer = 0
        stop_flags_ok = self.check_stop_flags(err_msg='movimiento lineal', timeout=ctrl_vars.TIMEOUT_LINEAL, axis=axis)
        
        while not (current_pos >= target_pos - 0.1 and current_pos <= target_pos + 0.1) and stop_flags_ok:
            #print("espera posicion del lineal",current_pos,target_pos)
            current_pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
            time.sleep(self.wait_time)
            timer += self.wait_time
            stop_flags_ok = self.check_stop_flags(err_msg='movimiento lineal', timeout=ctrl_vars.TIMEOUT_LINEAL, axis=axis)

        if stop_flags_ok == False:
            return False
        
        return self.wait_for_axis_state(msg_app.StateMachine.EST_INITIAL, axis)



    def get_current_boquilla_carga(self):
        axis = ctrl_vars.AXIS_IDS['carga']
        pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
        steps = ctrl_vars.LOAD_STEPS
        current_step = -1
        steps_count = len(steps)
        for i in range(steps_count):
            step = steps[i]
            if pos <= step + 2 and pos >= step - 2:
                current_step = i
                break
        if current_step >= 0:
            return ctrl_vars.BOQUILLA_CARGADOR[current_step]
        return False



    def get_current_boquilla_descarga(self):
        axis = ctrl_vars.AXIS_IDS['carga']
        pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
        steps = ctrl_vars.LOAD_STEPS
        current_step = -1
        steps_count = len(steps)
        for i in range(steps_count):
            step = steps[i]
            if pos <= step + 2 and pos >= step - 2:
                current_step = i
                break
        if current_step >= 0:
            return ctrl_vars.BOQUILLA_DESCARGADOR[current_step]
        return False



    def get_current_boquilla_roscado(self):
        axis = ctrl_vars.AXIS_IDS['carga']
        pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
        steps = ctrl_vars.LOAD_STEPS
        current_step = -1
        steps_count = len(steps)
        for i in range(steps_count):
            step = steps[i]
            if pos <= step + 2 and pos >= step - 2:
                current_step = i
                break
        if current_step >= 0:
            return ctrl_vars.BOQUILLA_ROSCADO[current_step]
        return False



    def mov_to_pos_lineal(self, target_pos, ref_rate=ctrl_vars.ROSCADO_CONSTANTES['velocidad_en_vacio']):   # Sends cmd to move to target position on lineal axis
        axis = ctrl_vars.AXIS_IDS['avance']
        command = Commands.mov_to_pos
        msg_id = self.get_message_id()
        ref = target_pos
        header, data = build_msg(
            command,
            ref = ref,
            ref_rate = ref_rate,
            msg_id = msg_id,
            eje = axis)
        print('sending mov to pos lineal cmd')
        if not self.send_message(header, data):
            print('send false')
            return False
        print('send true')
        return True



    def stop(self):
        self._stop_event.set()



    def wait_for_drv_flag(self, flag, axis, flag_value):
        drv_flags = ws_vars.MicroState.axis_flags[axis]['drv_flags']
        timer = 0
        stop_flags_ok = self.check_stop_flags(timeout=ctrl_vars.TIMEOUT_STATE_CHANGE)
        while drv_flags & flag != flag_value and stop_flags_ok == True:
            drv_flags = ws_vars.MicroState.axis_flags[axis]['drv_flags']
            time.sleep(self.wait_time)
            stop_flags_ok = self.check_stop_flags(timer=timer, timeout=ctrl_vars.TIMEOUT_STATE_CHANGE)
        if drv_flags & flag != flag_value:
            return False
        return True



    def check_stop_flags(self, err_msg='', timer=0, timeout=ctrl_vars.TIMEOUT_GENERAL, axis=None):
        msg = ''

        if timer >= timeout:
            msg = 'Timeout'
            if err_msg:
                msg += ' en ' + err_msg
            self.err_msg.append(msg)
            return False

        if axis or axis == 0:
            if ws_vars.MicroState.axis_flags[axis]['em_stop']:
                msg = 'Parada de emergencia (eje)'
                if err_msg:
                    msg += ' en ' + err_msg
                self.err_msg.append(msg)
                return False
        
        if ws_vars.MicroState.micro_flags['em_stop'] == True:
            msg = 'Parada de emergencia (general)'
            if err_msg:
                msg += ' en ' + err_msg
            self.err_msg.append(msg)
            return False
        
        if ws_vars.MicroState.routine_stopped == True:
            msg = 'Rutina detenida'
            if err_msg:
                msg += ' en ' + err_msg
            self.err_msg.append(msg)
            return False

        return True



    def check_running_routines(self):
        for routine in RoutineInfo.objects.all():
            if routine.running == 1:
                return True
        return False



    def set_routine_ongoing_flag(self):
        if self.check_running_routines():
            ws_vars.MicroState.routine_ongoing = True
        else:
            ws_vars.MicroState.routine_ongoing = False


    
    def wait_presure_off_allowed(self, routine): # espera hasta que los flags allow_presure_off de roscado o load sean true
        stop_flags_ok = self.check_stop_flags()
        load_id = ctrl_vars.ROUTINE_IDS['carga']
        
        #si la rutina es la de carga, carga el flag de carga; sino carga el flag de roscado
        if routine == load_id:
            flag = ws_vars.MicroState.load_allow_presure_off
        else:
            flag = ws_vars.MicroState.roscado_allow_presure_off
        
        while flag == False and stop_flags_ok == True:
            time.sleep(self.wait_time)
            stop_flags_ok = self.check_stop_flags()
            if routine == load_id:
                flag = ws_vars.MicroState.load_allow_presure_off
            else:
                flag = ws_vars.MicroState.roscado_allow_presure_off
        
        if stop_flags_ok == False:
            return False

        return True    



# ******************** MASTER ********************
class MasterHandler(threading.Thread):



    def __init__(self, **kwargs):
        super(MasterHandler, self).__init__(**kwargs)
        self.wait_time = 0.2
        self.wait_rtn_time = 0.5
        self.timer = 0
        self.init_rtn_timeout = 20
        #  ws_vars.MicroState.master_stop == True
        ws_vars.MicroState.master_running = True
        ws_vars.MicroState.master_stop = False
        ws_vars.MicroState.routine_stopped = False
        ws_vars.MicroState.end_master_routine = False
        ws_vars.MicroState.reset_cuplas_count = False
        ws_vars.MicroState.iteration = 0
        ws_vars.MicroState.first_run_load = True
        ws_vars.MicroState.first_two_runs_unload = 0
        
    

    def run(self):
        print("Master stop:", ws_vars.MicroState.master_stop)
        roscado_id = ctrl_vars.ROUTINE_IDS['roscado']
        carga_id = ctrl_vars.ROUTINE_IDS['carga']
        descarga_id = ctrl_vars.ROUTINE_IDS['descarga']
        indexar_id = ctrl_vars.ROUTINE_IDS['cabezal_indexar']
        
        if ctrl_fun.check_init_conditions_master() == False:
            ws_vars.MicroState.master_running = False
            return
        
        print('Inicio rutina master')
        ws_vars.MicroState.log_messages.append('MODO AUTOMATICO - Inicio')

        while ws_vars.MicroState.master_stop == False:
            running_ids = self.get_running_routines()
            print('\nRUNNING RTNS', running_ids)

            if indexar_id in running_ids:
                print('Rutina master, esperar fin de indexado')
                while indexar_id in running_ids and ws_vars.MicroState.master_stop == False:
                    running_ids = self.get_running_routines()
                    time.sleep(self.wait_rtn_time)

            if carga_id not in running_ids and ws_vars.MicroState.end_master_routine == False:
                print('RUTINA CARGA')
                RoutineHandler(carga_id).start()
                
                if self.wait_init_rtn(carga_id) == False:
                    return

            boquilla = self.get_current_boquilla_roscado()
            part_present = ctrl_vars.part_present_indicator[boquilla]
            print('Boquilla presente en roscado:', part_present)
            print('Numero iteracion:', ws_vars.MicroState.iteration)

            # agregado por AP - manda a el cuadro de mensajes el Nro d eiteracion
            mensaje = 'ROSCADO - Numero iteracion: ' + str(ws_vars.MicroState.iteration)
            ws_vars.MicroState.log_messages.append(mensaje)

            if ws_vars.MicroState.iteration >= 1 and part_present == True:
                if roscado_id not in running_ids:
                    print('RUTINA ROSCADO')
                    RoutineHandler(roscado_id).start()
                
                    if self.wait_init_rtn(roscado_id) == False:
                        return
            
            if ws_vars.MicroState.iteration >= 1 and ws_vars.MicroState.end_master_routine == False and part_present == False:
                print('Error en master. Pieza en roscado no presente')
                ws_vars.MicroState.err_messages.append('Error en rutina master. Pieza en roscado no presente')
                return


            boquilla = self.get_current_boquilla_descarga()
            part_present = ctrl_vars.part_present_indicator[boquilla]
            print('Boquilla presente en descarga:', part_present)
            print('Numero iteracion:', ws_vars.MicroState.iteration)
            if (ws_vars.MicroState.iteration >= 2 and part_present == True) or (ws_vars.MicroState.first_two_runs_unload <= 2):
                if descarga_id not in running_ids:
                    print('RUTINA DESCARGA')
                    RoutineHandler(descarga_id).start()

                    if self.wait_init_rtn(descarga_id) == False:
                        return
            
            if ws_vars.MicroState.iteration >= 2 and ws_vars.MicroState.end_master_routine == False and part_present == False:
                print('Error en master. Pieza en descarga no presente')
                ws_vars.MicroState.err_messages.append('Error en rutina master. Pieza en descarga no presente')
                return
            

            while ws_vars.MicroState.routine_ongoing == True and ws_vars.MicroState.master_stop == False:
                time.sleep(self.wait_rtn_time)
            
            
            part_present_descarga = ctrl_vars.part_present_indicator[boquilla]
            part_present_roscar = ctrl_vars.part_present_indicator[self.get_current_boquilla_roscado()]
            part_present = part_present_descarga or part_present_roscar
            print('Boquilla presente en descarga:', part_present)
            print('Numero iteracion:', ws_vars.MicroState.iteration)
            if ws_vars.MicroState.iteration >= 2 and ws_vars.MicroState.end_master_routine == True and part_present == False:
                print('MASTER - Fin de rutina')
                ws_vars.MicroState.master_running = False
                ws_vars.MicroState.log_messages.append('MODO AUTOMATICO - fin')
                
                ch_info = get_ch_info(ChannelInfo, 'micro')
                key = 'encender_bomba_soluble'
                group = 1
                command = Commands.rem_do_set
                header, data = ctrl_fun.set_rem_do(command, key, group, 0)
                send_message(header, ch_info=ch_info, data=data)

                command = Commands.sync_off
                axis = ctrl_vars.AXIS_IDS['avance']
                header = build_msg(command, eje=axis, msg_id=ctrl_fun.get_message_id())
                send_message(header, ch_info=ch_info)

                return
            
            
            if ws_vars.MicroState.master_stop == True:
                ws_vars.MicroState.master_running = False
                return
            
            running_ids = self.get_running_routines()
            if indexar_id not in running_ids:
                print('RUTINA INDEXAR')
                ws_vars.MicroState.log_messages.append('INDEXAR - Inicio de rutina*')
                RoutineHandler(indexar_id).start()

                if self.wait_init_rtn(indexar_id) == False:
                    return
            
            while indexar_id in running_ids and ws_vars.MicroState.master_stop == False:
                time.sleep(self.wait_rtn_time)
                running_ids = self.get_running_routines()
            
            if ws_vars.MicroState.master_stop == True:
                ws_vars.MicroState.master_running = False
                return

            # if ws_vars.MicroState.iteration < 2:
            ws_vars.MicroState.iteration += 1

        return



    def get_running_routines(self):
        running_routines = []
        for routine in RoutineInfo.objects.all():
            if routine.running == 1:
                running_routines.append(ctrl_vars.ROUTINE_IDS[routine.name])
        return running_routines
    


    def check_timeout_exceeded(self, timeout):
        print("*"*50,"\nCheck timeout exceeded", ws_vars.MicroState.master_stop)
        if self.timer >= timeout or ws_vars.MicroState.master_stop == True:
            ws_vars.MicroState.master_running = False
            return True
        return False
    


    def wait_init_rtn(self, routine_id):
        running_ids = self.get_running_routines()
        timeout_exceeded = self.check_timeout_exceeded(self.init_rtn_timeout)

        while routine_id not in running_ids and timeout_exceeded == False:
            time.sleep(self.wait_time)
            self.timer += self.wait_time
            running_ids = self.get_running_routines()
            timeout_exceeded = self.check_timeout_exceeded(self.init_rtn_timeout)
        
        if timeout_exceeded:
            if self.timer >= self.init_rtn_timeout:
                print('Timeout esperando inicio de rutina', routine_id)
                ws_vars.MicroState.master_stop = True
                ws_vars.MicroState.master_running = False
            else:
                print('Rutina master detenida')
            return False
        self.timer = 0
        return True



    def get_current_boquilla_carga(self):
        axis = ctrl_vars.AXIS_IDS['carga']
        pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
        steps = ctrl_vars.LOAD_STEPS
        current_step = -1
        steps_count = len(steps)
        for i in range(steps_count):
            step = steps[i]
            if pos <= step + 2 and pos >= step - 2:
                current_step = i
                break
        if current_step >= 0:
            return ctrl_vars.BOQUILLA_CARGADOR[current_step]
        return False



    def get_current_boquilla_descarga(self):
        axis = ctrl_vars.AXIS_IDS['carga']
        pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
        steps = ctrl_vars.LOAD_STEPS
        current_step = -1
        steps_count = len(steps)
        for i in range(steps_count):
            step = steps[i]
            if pos <= step + 2 and pos >= step - 2:
                current_step = i
                break
        if current_step >= 0:
            return ctrl_vars.BOQUILLA_DESCARGADOR[current_step]
        return False



    def get_current_boquilla_roscado(self):
        axis = ctrl_vars.AXIS_IDS['carga']
        pos = ws_vars.MicroState.axis_measures[axis]['pos_fil']
        steps = ctrl_vars.LOAD_STEPS
        current_step = -1
        steps_count = len(steps)
        for i in range(steps_count):
            step = steps[i]
            if pos <= step + 2 and pos >= step - 2:
                current_step = i
                break
        if current_step >= 0:
            return ctrl_vars.BOQUILLA_ROSCADO[current_step]
        return False