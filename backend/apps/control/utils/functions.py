import string
import django
import random, time
from datetime import datetime
from apps.service.acdp.handlers import build_msg
from apps.service.api.variables import Commands, COMMANDS
from apps.service.acdp import messages_app as msg_app
from apps.service.acdp import messages_base as msg_base

from apps.control.utils import variables as ctrl_vars

from apps.ws.utils.handlers import send_message
from apps.ws.utils.functions import send_front_message, get_ch_info
from apps.ws.utils import variables as ws_vars


# -------------------------------------------------------------------------------------------- #
# ----------------------------------- Initialization ----------------------------------------- #
# -------------------------------------------------------------------------------------------- #

def init_rem_io():
    for i in range(len(ctrl_vars.REM_DI_G1_ARR)):
        key = ctrl_vars.REM_DI_G1_ARR[i]
        if key: ctrl_vars.REM_DI_G1_STATES[key] = None
        key = ctrl_vars.REM_DI_G2_ARR[i]
        if key: ctrl_vars.REM_DI_G2_STATES[key] = None
        key = ctrl_vars.REM_DO_G1_ARR[i]
        if key: ctrl_vars.REM_DO_G1_STATES[key] = None
        key = ctrl_vars.REM_DO_G2_ARR[i]
        if key: ctrl_vars.REM_DO_G2_STATES[key] = None


def init_loc_io():
    for key in ctrl_vars.LOC_DI_ARR:
        ctrl_vars.LOC_DI_STATES[key] = None
    for key in ctrl_vars.LOC_DO_ARR:
        ctrl_vars.LOC_DO_STATES[key] = None


def init_routine_info():
    from apps.control.models import RoutineInfo
    routines = RoutineInfo.objects.all()
    rtn_names = []
    for routine in routines:
        rtn_names.append(routine.name)
        routine.running = 0
        routine.save()
    for rtn_name in ctrl_vars.ROUTINE_NAMES.values():
        if rtn_name not in rtn_names:
            RoutineInfo.objects.create(name=rtn_name, running=0)


def init_comands_ref_rates():
    for key, value in ctrl_vars.COMMAND_DEFAULT_VALUES.items():
        ctrl_vars.COMMAND_REF_RATES[key] = value


def init_master_flags():
    ws_vars.MicroState.master_running = False
    ws_vars.MicroState.master_stop = False
    ws_vars.MicroState.iteration = 0

def fake_tapping():
    count = 0
    while True:
        if count == 0:
            ws_vars.MicroState.graph_flag = True
        count += 1
        if count == 600:
            ws_vars.MicroState.graph_flag = False
            count = 0

# -------------------------------------------------------------------------------------------- #
# --------------------------------------- Routines ------------------------------------------- #
# -------------------------------------------------------------------------------------------- #



# ********* condiciones iniciales - MASTER *********
def check_init_conditions_master():
    
    if ws_vars.MicroState.rem_i_states[1]['presion_normal'] == False:
        err_msg = 'Baja presión'
        print('\nBaja presión\n')
        ws_vars.MicroState.err_messages.append(err_msg)
        return False

    pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
    if pos not in ctrl_vars.LOAD_STEPS:
        err_msg = 'Error en posicion de cabezal' 
        print('\nError en posicion de cabezal\n')
        ws_vars.MicroState.err_messages.append(err_msg)
        return False

    err_msg_index = check_init_conditions_index()
    err_msg_load = check_init_conditions_load()
    err_msg_unload = check_init_conditions_unload()
    err_msg_tapping = check_init_conditions_tapping()
    error_flag = False
    
    if err_msg_load:
        print('\nError en condiciones iniciales de carga')
        err_msg = 'Error en condiciones iniciales de carga'
        ws_vars.MicroState.err_messages.append(err_msg)
        for err in err_msg_load:
            ws_vars.MicroState.err_messages.append(err)
            print(err)
        error_flag = True
    else:
        log_msg = 'Condiciones iniciales de carga OK'
        print('Condiciones iniciales de carga OK')
        ws_vars.MicroState.log_messages.append(log_msg)
    
    if err_msg_unload:
        print('\nError en condiciones iniciales de descarga')
        err_msg = 'Error en condiciones iniciales de descarga'
        ws_vars.MicroState.err_messages.append(err_msg)
        for err in err_msg_unload:
            ws_vars.MicroState.err_messages.append(err)
            print(err)
        error_flag = True
    else:
        log_msg = 'Condiciones iniciales de descarga OK'
        print('Condiciones iniciales de descarga OK')
        ws_vars.MicroState.log_messages.append(log_msg)
    
    if err_msg_index:
        print('\nError en condiciones iniciales de indexado')
        err_msg = 'Error en condiciones iniciales de indexado'
        ws_vars.MicroState.err_messages.append(err_msg)
        for err in err_msg_index:
            ws_vars.MicroState.err_messages.append(err)
            print(err)
        error_flag = True
    else:
        log_msg = 'Condiciones iniciales de indexado OK'
        print('Condiciones iniciales de indexado OK')
        ws_vars.MicroState.log_messages.append(log_msg)
    
    if err_msg_tapping:
        print('\nError en condiciones iniciales de roscado')
        err_msg = 'Error en condiciones iniciales de roscado'
        ws_vars.MicroState.err_messages.append(err_msg)
        for err in err_msg_tapping:
            ws_vars.MicroState.err_messages.append(err)
            print(err)
        error_flag = True
    else:
        log_msg = 'Condiciones iniciales de roscado OK'
        print('Condiciones iniciales de roscado OK')
        ws_vars.MicroState.log_messages.append(log_msg)

    if error_flag == True:
        return False
    return True



# ********* condiciones iniciales - HOMING *********
def check_init_conditions_homing():
    eje_avance = ctrl_vars.AXIS_IDS['avance']
    eje_carga = ctrl_vars.AXIS_IDS['carga']
    eje_giro = ctrl_vars.AXIS_IDS['giro']
    error_messages = []
    initial_state = msg_app.StateMachine.EST_INITIAL
    # Paso 0 - Chequear condiciones iniciales - Todos los valores deben ser True par que empiece la rutina
    init_flags = [
        (ws_vars.MicroState.axis_flags[eje_carga]['estado'] != 'safe', 'Eje carga en safe'),                    # Eje NO en safe
        (ws_vars.MicroState.axis_flags[eje_giro]['estado'] != 'safe', 'Eje husillo en safe'),                   # Eje NO en safe
        (ws_vars.MicroState.axis_flags[eje_avance]['estado'] != 'safe', 'Eje avance en safe'),                  # Eje NO en safe
        (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                 # Presión normal

        (ws_vars.MicroState.rem_o_states[1]['presurizar'] == False, 'Presurizar en ON'),                        # Presurizar OFF

        (ws_vars.MicroState.axis_flags[eje_avance]['maq_est_val'] == initial_state, 'Eje lineal apagado'),      # eje avance encendido
        (ws_vars.MicroState.rem_i_states[1]['acople_lubric_contraido'], 'Acople lubricante afuera'),            # acople_lubricante_contraido
        (ws_vars.MicroState.rem_i_states[1]['cerramiento_roscado_contraido'], 'Cerramiento roscado expandido'), # cerramiento_roscado_contraido
        (ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'], 'Puntera descarga expandida'),       # puntera_descarga_contraida
        (ws_vars.MicroState.rem_i_states[0]['puntera_carga_contraida'], 'Puntera carga expandida'),             # puntera_carga_contraida
    ]

    for flag, error in init_flags:
        if flag == False:
            error_messages.append(error)

    return error_messages



# ********* condiciones iniciales - INDEX *********
def check_init_conditions_index():
    pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
    eje_avance = ctrl_vars.AXIS_IDS['avance']
    eje_carga = ctrl_vars.AXIS_IDS['carga']
    eje_giro = ctrl_vars.AXIS_IDS['giro']
    error_messages = []
    init_flags = [
        (pos in ctrl_vars.LOAD_STEPS, 'Posición de plato errónea'),                                                                     # Plato alineado
        (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),   # Eje lineal cerado
        (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),    # Cabezal cerado
        
        (ws_vars.MicroState.axis_flags[eje_carga]['estado'] != 'safe', 'Eje carga en safe'),                                            # Eje NO en safe
        (ws_vars.MicroState.axis_flags[eje_giro]['estado'] != 'safe', 'Eje husillo en safe'),                                           # Eje NO en safe
        (ws_vars.MicroState.axis_flags[eje_avance]['estado'] != 'safe', 'Eje avance en safe'),                                          # Eje NO en safe
        (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal

        (ws_vars.MicroState.rem_o_states[1]['presurizar'] == False, 'Presurizar en ON'),                                                # Presurizar OFF

        (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                                          # plato_clampeado
        (ws_vars.MicroState.rem_i_states[1]['acople_lubric_contraido'], 'Acople lubricante expandido'),                                 # acople_lubricante_contraido
        (ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'], 'Puntera descarga expandida'),                               # puntera_descarga_contraida
        (ws_vars.MicroState.rem_i_states[0]['puntera_carga_contraida'], 'Puntera carga expandida'),                                     # puntera_carga_contraida
        (ws_vars.MicroState.rem_i_states[1]['cerramiento_roscado_contraido'], 'Cerramiento roscado expandido'),                         # cerramiento_roscado_contraido
        (round(ws_vars.MicroState.axis_measures[eje_avance]['pos_fil'], 0) >= round(ctrl_vars.ROSCADO_CONSTANTES['posicion_de_inicio'], 0), 'Posición de eje avance erróneo'),   # Eje avance en posición de inicio
    ]
    for flag, error in init_flags:
        if flag == False:
            error_messages.append(error)

    return error_messages



# ********* condiciones iniciales - CARGA *********
def check_init_conditions_load():
    pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
    eje_avance = ctrl_vars.AXIS_IDS['avance']
    eje_carga = ctrl_vars.AXIS_IDS['carga']
    eje_giro = ctrl_vars.AXIS_IDS['giro']
    error_messages = []
    init_flags = [
        (pos in ctrl_vars.LOAD_STEPS, 'Posición de plato errónea'),                                                                     # Plato alineado
        (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),   # Eje lineal cerado
        (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),    # Cabezal cerado

        (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
        (ws_vars.MicroState.axis_flags[eje_carga]['estado'] != 'safe', 'Eje carga en safe'),                                            # Eje NO en safe
        (ws_vars.MicroState.axis_flags[eje_giro]['estado'] != 'safe', 'Eje husillo en safe'),                                           # Eje NO en safe
        (ws_vars.MicroState.axis_flags[eje_avance]['estado'] != 'safe', 'Eje avance en safe'),                                          # Eje NO en safe

        (ws_vars.MicroState.rem_o_states[1]['encender_bomba_hidraulica'], 'Bomba hidráulica apagada'),              # hidráulica ON
        (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                      # Plato clampeado
        (ws_vars.MicroState.rem_i_states[0]['vertical_carga_contraido'], 'Vertical de carga expandido'),            # vertical_carga_contraido
        (ws_vars.MicroState.rem_i_states[0]['puntera_carga_contraida'], 'Puntera carga expandida'),                 # puntera_carga_contraida
        (ws_vars.MicroState.rem_i_states[0]['brazo_cargador_expandido'], 'Brazo cargador cntraído'),                # brazo_cargador_expandido
        (ws_vars.MicroState.rem_i_states[0]['boquilla_carga_expandida'], 'Boquilla de carga contraída'),            # boquilla de carga  liberada - ws_vars.MicroState.rem_i_states[0]
        #(ws_vars.MicroState.rem_i_states[1]['presencia_cupla_en_cargador'], 'Cupla en cargador no presente'),       # presencia_cupla_en_cargador, comentado porque espera que haya presencia
        (ws_vars.MicroState.rem_i_states[1]['pieza_en_boquilla_carga'], 'Pieza en boquilla de carga presente')  # pieza no presente en boquilla de carga, se dio vuelta la logica de los sensores respecto a durallite
    ]

    for flag, error in init_flags:
        if flag == False:
            error_messages.append(error)
    
    return error_messages



# ********* condiciones iniciales - DESCARGA *********
def check_init_conditions_unload():
    pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
    eje_avance = ctrl_vars.AXIS_IDS['avance']
    eje_carga = ctrl_vars.AXIS_IDS['carga']
    eje_giro = ctrl_vars.AXIS_IDS['giro']
    error_messages = []
    init_flags = [
        (pos in ctrl_vars.LOAD_STEPS, 'Posición de plato errónea'),                                                                     # Plato alineado
        (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),   # Eje lineal cerado
        (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),    # Cabezal cerado

        (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
        (ws_vars.MicroState.axis_flags[eje_carga]['estado'] != 'safe', 'Eje carga en safe'),                                            # Eje NO en safe
        (ws_vars.MicroState.axis_flags[eje_giro]['estado'] != 'safe', 'Eje husillo en safe'),                                           # Eje NO en safe
        (ws_vars.MicroState.axis_flags[eje_avance]['estado'] != 'safe', 'Eje avance en safe'),                                          # Eje NO en safe

        (ws_vars.MicroState.rem_o_states[1]['encender_bomba_hidraulica'], 'Bomba hidráulica apagada'),                      # hidráulica ON
        (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                              # Plato clampeado
        (ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'], 'Puntera descarga expandida'),                   # puntera_descarga_contraida
        (ws_vars.MicroState.rem_i_states[0]['brazo_descarga_expandido'], 'Brazo descargador contraído'),                    # brazo_descarga_expandido
        (ws_vars.MicroState.rem_i_states[0]['boquilla_descarga_expandida'], 'Boquilla descarga contraída'),                 # boquilla descarga liberada - boquilla_descarga_expandida
        #(ws_vars.MicroState.rem_i_states[1]['cupla_por_tobogan_descarga'], 'Cupla presente en tobogán de descarga'),        # cupla no presente en tobogan_descarga
        (ws_vars.MicroState.rem_i_states[1]['pieza_en_boquilla_descarga'], 'Cupla presente en boquilla de descarga'),   # cupla no presente en boquilla descarga
        (ws_vars.MicroState.rem_i_states[1]['horiz_pinza_desc_contraido'], 'Horizontal pinza de descarga expandida'),       # horiz_pinza_desc_contraido
        (ws_vars.MicroState.rem_i_states[1]['vert_pinza_desc_contraido'], 'Vertical pinza de descarga expandida'),          # vert_pinza_desc_contraido
        #(ws_vars.MicroState.rem_i_states[0]['pinza_descargadora_abierta'], 'Pinza descargadora cerrada')                    # pinza_descargadora_abierta, se comenta por que no estan puestos los sensores de la garra respecto a durallite
    ]

    for flag, error in init_flags:
        if flag == False:
            error_messages.append(error)
    
    return error_messages



# ********* condiciones iniciales - ROSCADO *********
def check_init_conditions_tapping():
    pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
    eje_avance = ctrl_vars.AXIS_IDS['avance']
    eje_carga = ctrl_vars.AXIS_IDS['carga']
    eje_giro = ctrl_vars.AXIS_IDS['giro']
    initial_state = msg_app.StateMachine.EST_INITIAL
    
    sync_flag = None
    sync_err_msg = None
    if ws_vars.MicroState.master_running == False or ws_vars.MicroState.iteration <= 1:
        sync_flag = ws_vars.MicroState.axis_flags[eje_avance]['sync_on'] == 0   # Si master no está corriendo o la iteración es <= 1 (todavía no empezó a roscar)
                                                                                # el sync tiene que estar apagado (sync_flag = 1)
        sync_err_msg = 'Sincronismo encendido'
    else:
        sync_flag = ws_vars.MicroState.axis_flags[eje_avance]['sync_on'] == 1
        sync_err_msg = 'Sincronismo apagado con master'
    error_messages = []

    init_flags = [
        (pos in ctrl_vars.LOAD_STEPS, 'Posición de plato errónea'),                                                                     # Plato alineado
        (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),   # Eje lineal cerado
        (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),    # Cabezal cerado

        (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
        (ws_vars.MicroState.axis_flags[eje_carga]['estado'] != 'safe', 'Eje carga en safe'),                                            # Eje NO en safe
        (ws_vars.MicroState.axis_flags[eje_giro]['estado'] != 'safe', 'Eje husillo en safe'),                                           # Eje NO en safe
        (ws_vars.MicroState.axis_flags[eje_avance]['estado'] != 'safe', 'Eje avance en safe'),                                          # Eje NO en safe

        (ws_vars.MicroState.rem_o_states[1]['encender_bomba_hidraulica'], 'Bomba hidráulica apagada'),                                  # hidráulica ON
        (ws_vars.MicroState.rem_o_states[1]['presurizar'] == False, 'Presurizar en ON'),                                                # Presurizar OFF

        (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                                          # Plato clampeado
        (ws_vars.MicroState.rem_i_states[1]['acople_lubric_contraido'], 'Acople lubricante afuera'),                                    # acople_lubricante_contraido
        (ws_vars.MicroState.rem_i_states[1]['cerramiento_roscado_contraido'], 'Cerramiento roscado expandido'),                         # cerramiento_roscado_contraido
        (ws_vars.MicroState.axis_flags[eje_avance]['maq_est_val'] == initial_state, 'Eje de avance apagado'),                           # eje avance ON
        (ws_vars.MicroState.axis_flags[eje_carga]['drv_flags'] & msg_base.DrvFbkDataFlags.ENABLED == 0, 'Eje de carga encendido'),      # eje carga OFF
        (sync_flag, sync_err_msg),                                                                                                      # Sincronismo
        (round(ws_vars.MicroState.axis_measures[eje_avance]['pos_fil'], 0) == round(ctrl_vars.ROSCADO_CONSTANTES['posicion_de_inicio'], 0), 'Posición de eje de avance errónea')   # Eje avance en posición de inicio
    ]

    for flag, error in init_flags:
        if flag == False:
            error_messages.append(error)
    
    return error_messages


def get_running_routines():
    from apps.control.models import RoutineInfo
    routines = RoutineInfo.objects.all()
    running_routines = []
    for rtn in routines:
        if rtn.running == 1:
            running_routines.append(rtn.name)
    return running_routines


def check_routine_allowed(routine):
    running_rtns = get_running_routines()
    homing_name = ctrl_vars.ROUTINE_NAMES[ctrl_vars.ROUTINE_IDS['cerado']]
    cabezal_indexar = ctrl_vars.ROUTINE_NAMES[ctrl_vars.ROUTINE_IDS['cabezal_indexar']]
    roscado = ctrl_vars.ROUTINE_NAMES[ctrl_vars.ROUTINE_IDS['roscado']]
    routine_name = ctrl_vars.ROUTINE_NAMES[routine]
    cerado_lineal = ctrl_vars.ROUTINE_NAMES[ctrl_vars.ROUTINE_IDS['cerado_lineal']]

    if running_rtns:

        if homing_name in running_rtns:
            print('Cerado en proceso')
            return False
        
        if cerado_lineal in running_rtns:
            print('Cerado lineal en proceso')
            return False

        if cabezal_indexar in running_rtns:
            print('indexado en proceso')
            return False
    
        if routine_name == homing_name or routine_name == cerado_lineal or routine_name in running_rtns:
            print('Rutina en proceso')
            return False
    
        if routine_name == cabezal_indexar and roscado in running_rtns:
            print('Indexar prohibido: roscado en proceso')
            return False
    
    return True


def reset_routines_info():
    from apps.control.models import RoutineInfo
    rtns_info = RoutineInfo.objects.all()
    for rtn in rtns_info:
        rtn.running = 0
        rtn.save()
# -------------------------------------------------------------------------------------------- #
# ------------------- Chequeo de condiciones iniciales neumatica(safe-mode) ------------------ #
# -------------------------------------------------------------------------------------------- #


def check_init_conditions_neumatic_test(param_name):
    error_messages = []
    if param_name == 'contraer_boquilla_carga':
        #checkea
        init_flags = [
            (ws_vars.MicroState.rem_i_states[0]['boquilla_descarga_expandida'], 'Boquilla descarga contraída'),     
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages
    
    if param_name == 'contraer_brazo_cargador':
        #checkea
        init_flags = [
            (ws_vars.MicroState.rem_i_states[0]['boquilla_descarga_expandida'], 'Boquilla descarga contraída'),
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages
    
    if param_name == 'expandir_brazo_cargador':
        #checkea
        init_flags = [
            (ws_vars.MicroState.rem_i_states[0]['boquilla_descarga_expandida'], 'Boquilla descarga contraída'),     
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages


def check_init_conditions_neumatic_load(param_name):
    pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
    error_messages = []
    if param_name == 'contraer_puntera_carga': # revisado
        #checkea
        print("Checkeo condiciones iniciales de contraer_puntera_carga")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'expandir_puntera_carga': # revisado
        #checkea
        print("Checkeo condiciones iniciales de expandir_puntera_carga")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (pos in ctrl_vars.LOAD_STEPS, 'Posición de plato errónea'),                                                                     # Plato alineado
            (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),    # Cabezal cerado
            (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                                          # Plato clampeado
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'expandir_vertical_carga': # revisado
        #checkea
        print("Checkeo condiciones iniciales de expandir_vertical_carga (y contraer - MONOESTABLE)")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[0]['puntera_carga_contraida'], 'Puntera carga expandida'),                                     # puntera_carga_contraida
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'contraer_boquilla_carga': # revisado
        #checkea
        print("Checkeo condiciones iniciales de contraer_boquilla_carga (y expandir - MONOESTABLE)")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'contraer_brazo_cargador': # revisado
        #checkea
        print("Checkeo condiciones iniciales de contraer_brazo_cargador")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[0]['puntera_carga_contraida'], 'Puntera carga expandida'),                                     # puntera_carga_contraida
            (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                                          # Plato clampeado
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'expandir_brazo_cargador': # revisado
        #checkea
        print("Checkeo condiciones iniciales de expandir_brazo_cargador")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[0]['puntera_carga_contraida'], 'Puntera carga expandida'),                                     # puntera_carga_contraida
            (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                                          # Plato clampeado
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages
    

def check_init_conditions_neumatic_unload(param_name):
    pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
    error_messages = []
    if param_name == 'contraer_puntera_descarga': # revisado
        #checkea
        print("Checkeo condiciones iniciales de contraer_puntera_descarga")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'expandir_puntera_descarga': # revisado
        #checkea
        print("Checkeo condiciones iniciales de expandir_puntera_descarga")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),    # Cabezal cerado
            (pos in ctrl_vars.LOAD_STEPS, 'Posición de plato errónea'),                                                                     # Plato alineado
            (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                                          # Plato clampeado
            (ws_vars.MicroState.rem_i_states[0]['pinza_descargadora_abierta'], 'Pinza descargadora cerrada')                                # pinza_descargadora_abierta
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'contraer_brazo_descargador': # revisado
        #checkea
        print("Checkeo condiciones iniciales de contraer_brazo_descargador")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'], 'Puntera descarga expandida'),                               # puntera_descarga_contraida
            (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                                          # Plato clampeado
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'expandir_brazo_descargador': # revisado
        #checkea
        print("Checkeo condiciones iniciales de expandir_brazo_descargador")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'], 'Puntera descarga expandida'),                               # puntera_descarga_contraida
            (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                                          # Plato clampeado
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'expandir_horiz_pinza_desc': # revisado
        #checkea
        print("Checkeo condiciones iniciales de expandir_horiz_pinza_desc")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[1]['vert_pinza_desc_contraido'], 'Vertical pinza de descarga expandida'),                      # vert_pinza_desc_contraido
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'contraer_horiz_pinza_desc': # revisado
        #checkea
        print("Checkeo condiciones iniciales de contraer_horiz_pinza_desc")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[1]['vert_pinza_desc_contraido'], 'Vertical pinza de descarga expandida'),                      # vert_pinza_desc_contraido
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'expandir_vert_pinza_desc': # revisado
        #checkea
        print("Checkeo condiciones iniciales de expandir_vert_pinza_desc")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'], 'Puntera descarga expandida'),                               # puntera_descarga_contraida
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'contraer_vert_pinza_desc': # revisado
        #checkea
        print("Checkeo condiciones iniciales de contraer_vert_pinza_desc")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'], 'Puntera descarga expandida'),                               # puntera_descarga_contraida
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'contraer_boquilla_descarga': # revisado
        #checkea
        print("Checkeo condiciones iniciales de contraer_boquilla_descarga (y expandir - MONOESTABLE)")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'cerrar_pinza_descargadora': # revisado
        #checkea
        print("Checkeo condiciones iniciales de cerrar_pinza_descargadora")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'abrir_pinza_descargadora': # revisado
        #checkea
        print("Checkeo condiciones iniciales de abrir_pinza_descargadora")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages


def check_init_conditions_neumatic_cabezal(param_name):
    pos = round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'], 0)
    eje_avance = ctrl_vars.AXIS_IDS['avance']
    error_messages = []

    if param_name == 'expandir_cerramiento_roscado': # revisado
        #checkea
        print("Checkeo condiciones iniciales de expandir_cerramiento_roscado (y contraer - MONOESTABLE)")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),    # Cabezal cerado
            (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                                          # Plato clampeado
            (pos in ctrl_vars.LOAD_STEPS, 'Posición de plato errónea'),                                                                     # Plato alineado
            (ws_vars.MicroState.rem_o_states[1]['encender_bomba_soluble'] == False, 'Bomba Soluble encendida'),                             # Bomba Soluble apagada
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'contraer_clampeo_plato': # revisado 
        #checkea
        print("Checkeo condiciones iniciales de contraer_clampeo_plato")
        init_flags = [
            (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),   # Eje lineal cerado
            (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),    # Cabezal cerado
        
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[1]['acople_lubric_contraido'], 'Acople lubricante expandido'),                                 # acople_lubricante_contraido
            (ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'], 'Puntera descarga expandida'),                               # puntera_descarga_contraida
            (ws_vars.MicroState.rem_i_states[0]['puntera_carga_contraida'], 'Puntera carga expandida'),                                     # puntera_carga_contraida
            (ws_vars.MicroState.rem_i_states[1]['cerramiento_roscado_contraido'], 'Cerramiento roscado expandido'),                         # cerramiento_roscado_contraido
        
            (pos in ctrl_vars.LOAD_STEPS, 'Posición de plato errónea'),                                                                     # Plato alineado
            (round(ws_vars.MicroState.axis_measures[eje_avance]['pos_fil'], 0) >= round(ctrl_vars.ROSCADO_CONSTANTES['posicion_de_inicio'], 0), 'Posición de eje avance erróneo'),   # Eje avance en posición de inicio
        ]           

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'expandir_clampeo_plato': # revisado
        #checkea
        print("Checkeo condiciones iniciales de expandir_clampeo_plato")
        init_flags = [
            (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),   # Eje lineal cerado
            (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),    # Cabezal cerado
        
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.rem_i_states[1]['acople_lubric_contraido'], 'Acople lubricante expandido'),                                 # acople_lubricante_contraido
            (ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'], 'Puntera descarga expandida'),                               # puntera_descarga_contraida
            (ws_vars.MicroState.rem_i_states[0]['puntera_carga_contraida'], 'Puntera carga expandida'),                                     # puntera_carga_contraida
            (ws_vars.MicroState.rem_i_states[1]['cerramiento_roscado_contraido'], 'Cerramiento roscado expandido'),                         # cerramiento_roscado_contraido
        
            (pos in ctrl_vars.LOAD_STEPS, 'Posición de plato errónea'),                                                                     # Plato alineado
            (round(ws_vars.MicroState.axis_measures[eje_avance]['pos_fil'], 0) >= round(ctrl_vars.ROSCADO_CONSTANTES['posicion_de_inicio'], 0), 'Posición de eje avance erróneo'),   # Eje avance en posición de inicio
        ]   

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'presurizar': # revisado
        #checkea
        print("Checkeo condiciones iniciales de presurizar ON  (y OFF - MONOESTABLE)")
        init_flags = [
            (ws_vars.MicroState.rem_o_states[1]['encender_bomba_hidraulica'], 'Bomba hidráulica apagada'),                                  # hidráulica ON
            (ws_vars.MicroState.rem_o_states[1]['cerrar_boquilla_1'] == False, 'Boquilla 1 Cerrar ON'),                                     # Boquilla 1 Cerrar OFF
            (ws_vars.MicroState.rem_o_states[1]['cerrar_boquilla_2'] == False, 'Boquilla 2 Cerrar ON'),                                     # Boquilla 2 Cerrar OFF
            (ws_vars.MicroState.rem_o_states[1]['cerrar_boquilla_3'] == False, 'Boquilla 3 Cerrar ON'),                                     # Boquilla 3 Cerrar OFF
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'cerrar_boquilla_1': # revisado
        #checkea
        print("Checkeo condiciones iniciales de cerrar_boquilla_1")
        init_flags = [
            (ws_vars.MicroState.rem_o_states[1]['encender_bomba_hidraulica'], 'Bomba hidráulica apagada'),                                  # hidráulica ON
            (ws_vars.MicroState.rem_o_states[1]['presurizar'], 'Presurizar en OFF'),                                                        # Presurizar ON
            (ws_vars.MicroState.rem_o_states[1]['abrir_boquilla_1'] == False, 'Boquilla 1 Abrir ON'),                                       # Boquilla 1 Abrir OFF
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'abrir_boquilla_1': # revisado
        #checkea
        print("Checkeo condiciones iniciales de abrir_boquilla_1")
        init_flags = [
            # (ws_vars.MicroState.rem_i_states[0]['boquilla_descarga_expandida'], 'Boquilla descarga contraída'),
            (ws_vars.MicroState.rem_o_states[1]['encender_bomba_hidraulica'], 'Bomba hidráulica apagada'),                                  # hidráulica ON
            (ws_vars.MicroState.rem_o_states[1]['presurizar'] == False, 'Presurizar en ON'),                                                # Presurizar OFF
            (ws_vars.MicroState.rem_o_states[1]['cerrar_boquilla_1'] == False, 'Boquilla 1 Cerrar ON'),                                     # Boquilla 1 Cerrar OFF
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'cerrar_boquilla_2': # revisado
        #checkea
        print("Checkeo condiciones iniciales de cerrar_boquilla_2")
        init_flags = [
            (ws_vars.MicroState.rem_o_states[1]['encender_bomba_hidraulica'], 'Bomba hidráulica apagada'),                                  # hidráulica ON
            (ws_vars.MicroState.rem_o_states[1]['presurizar'], 'Presurizar en OFF'),                                                        # Presurizar ON
            (ws_vars.MicroState.rem_o_states[1]['abrir_boquilla_2'] == False, 'Boquilla 2 Abrir ON'),                                       # Boquilla 2 Abrir OFF
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'abrir_boquilla_2': # revisado
        #checkea
        print("Checkeo condiciones iniciales de abrir_boquilla_2")
        init_flags = [
            (ws_vars.MicroState.rem_o_states[1]['encender_bomba_hidraulica'], 'Bomba hidráulica apagada'),                                  # hidráulica ON
            (ws_vars.MicroState.rem_o_states[1]['presurizar'] == False, 'Presurizar en ON'),                                                # Presurizar OFF
            (ws_vars.MicroState.rem_o_states[1]['cerrar_boquilla_2'] == False, 'Boquilla 2 Cerrar ON'),                                     # Boquilla 2 Cerrar OFF
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'cerrar_boquilla_3': # revisado
        #checkea
        print("Checkeo condiciones iniciales de cerrar_boquilla_3")
        init_flags = [
            (ws_vars.MicroState.rem_o_states[1]['encender_bomba_hidraulica'], 'Bomba hidráulica apagada'),                                  # hidráulica ON
            (ws_vars.MicroState.rem_o_states[1]['presurizar'], 'Presurizar en OFF'),                                                        # Presurizar ON
            (ws_vars.MicroState.rem_o_states[1]['abrir_boquilla_3'] == False, 'Boquilla 3 Abrir ON'),                                       # Boquilla 3 Abrir OFF
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'abrir_boquilla_3': # revisado
        #checkea
        print("Checkeo condiciones iniciales de abrir_boquilla_3")
        init_flags = [
            (ws_vars.MicroState.rem_o_states[1]['encender_bomba_hidraulica'], 'Bomba hidráulica apagada'),                                  # hidráulica ON
            (ws_vars.MicroState.rem_o_states[1]['presurizar'] == False, 'Presurizar en ON'),                                                # Presurizar OFF
            (ws_vars.MicroState.rem_o_states[1]['cerrar_boquilla_3'] == False, 'Boquilla 3 Cerrar ON'),                                     # Boquilla 3 Cerrar OFF
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'expandir_acople_lubric': # revisado
        #checkea
        print("Checkeo condiciones iniciales de expandir_acople_lubric (y contraer - MONOESTABLE)")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal
            (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),    # Cabezal cerado
            (pos in ctrl_vars.LOAD_STEPS, 'Posición de plato errónea'),                                                                     # Plato alineado
            (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido'], 'Plato no clampeado'),                                          # Plato clampeado
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'encender_bomba_soluble': # revisado
        #checkea
        print("Checkeo condiciones iniciales de encender_bomba_soluble (y apagar - MONOESTABLE)")
        init_flags = [
            (ws_vars.MicroState.rem_i_states[1]['cerramiento_roscado_contraido'] == False, 'Cerramiento roscado NO expandido'),                         # cerramiento_roscado_al_menos_NO_contraido
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    elif param_name == 'encender_bomba_hidraulica': # revisado
        #checkea
        print("Checkeo condiciones iniciales de encender_bomba_hidraulica (y apagar - MONOESTABLE)")
        init_flags = [
            (ws_vars.MicroState.rem_o_states[1]['presurizar'] == False, 'Presurizar en ON'),                                                # Presurizar OFF
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

# -------------------------------------------------------------------------------------------- #
# ---------------- Chequeo de condiciones iniciales manual-motores(safe-mode) ---------------- #
# -------------------------------------------------------------------------------------------- #


def check_init_conditions_motores(axis):
    eje_avance = ctrl_vars.AXIS_IDS['avance']
    eje_carga = ctrl_vars.AXIS_IDS['carga']
    eje_giro = ctrl_vars.AXIS_IDS['giro']
    error_messages = []
    #CABEZAL
    if axis == 2: # eje de INDEXADO revisado
        print("Checkeo condiciones iniciales de eje INDEXADO")
        #checkea CABEZAL
        init_flags = [
            (ws_vars.MicroState.axis_flags[eje_carga]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),                      # Cabezal cerado
            (ws_vars.MicroState.axis_flags[eje_carga]['estado'] != 'safe', 'Eje carga en safe'),                                            # Eje NO en safe

            (ws_vars.MicroState.rem_i_states[1]['presion_normal'], 'Baja presión'),                                                         # Presión normal

            (ws_vars.MicroState.rem_o_states[1]['presurizar'] == False, 'Presurizar en ON'),                                                # Presurizar OFF

            (ws_vars.MicroState.rem_i_states[1]['clampeo_plato_contraido'], 'Plato clampeado'),                                             # plato_NO_clampeado
            (ws_vars.MicroState.rem_i_states[1]['acople_lubric_contraido'], 'Acople lubricante expandido'),                                 # acople_lubricante_contraido
            (ws_vars.MicroState.rem_i_states[0]['puntera_descarga_contraida'], 'Puntera descarga expandida'),                               # puntera_descarga_contraida
            (ws_vars.MicroState.rem_i_states[0]['puntera_carga_contraida'], 'Puntera carga expandida'),                                     # puntera_carga_contraida
            (ws_vars.MicroState.rem_i_states[1]['cerramiento_roscado_contraido'], 'Cerramiento roscado expandido'),                         # cerramiento_roscado_contraido
            (round(ws_vars.MicroState.axis_measures[eje_avance]['pos_fil'], 0) >= round(ctrl_vars.ROSCADO_CONSTANTES['posicion_de_inicio'], 0), 'Posición de eje avance erróneo'),   # Eje avance en posición de inicio o mayor
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages

    #LINEAL
    elif axis == 1: # eje LINEAL revisado
        print("Checkeo condiciones iniciales de eje LINEAL")
        #checkea LINEAL
        init_flags = [
            (ws_vars.MicroState.axis_flags[eje_avance]['cero_desconocido'] == False, 'Cero desconocido en eje lineal'),                     # Eje lineal cerado
            (ws_vars.MicroState.axis_flags[eje_avance]['estado'] != 'safe', 'Eje avance en safe'),                                          # Eje NO en safe
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages


    #HUSILLO
    elif axis == 0: # eje HUSILLO revisado
        print("Checkeo condiciones iniciales de eje HUSILLO")
        #checkea HUSILLO
        init_flags = [
            (ws_vars.MicroState.axis_flags[eje_giro]['estado'] != 'safe', 'Eje husillo en safe'),                                           # Eje NO en safe
        ]

        for flag, error in init_flags:
            if flag == False:
                error_messages.append(error)
        
        return error_messages


# -------------------------------------------------------------------------------------------- #
# -------------------------------- Update/Get States ----------------------------------------- #
# -------------------------------------------------------------------------------------------- #


def update_data_flags(micro_data):
    cmd_toggle_bit = 1 << 0
    cmd_received_bit = 1 << 1
    
    em_stop_bit = 1 << 0
    ctrl_ok_bit = 1 << 1
    running_bit = 1 << 2

    micro_flags = {
        'cmd_toggle':   not (ws_vars.MicroState.last_rx_data.data.flags & cmd_toggle_bit == micro_data.data.flags & cmd_toggle_bit),
        'cmd_received': (micro_data.data.flags & cmd_received_bit == cmd_received_bit),
        'em_stop':      micro_data.data.ctrl.flags & em_stop_bit == em_stop_bit,
        'ctrl_ok':      micro_data.data.ctrl.flags & ctrl_ok_bit == ctrl_ok_bit,
        'running':      micro_data.data.ctrl.flags & running_bit == running_bit
    }

    ws_vars.MicroState.micro_flags = micro_flags
    return micro_flags


def check_end_flags(flags_value,axis):
    ok_bit                  = msg_app.AxisFlagsFin.FLGFIN_OK
    cancel_bit              = msg_app.AxisFlagsFin.FLGFIN_CANCELLED
    em_stop_bit             = msg_app.AxisFlagsFin.FLGFIN_EM_STOP
    drv_homing_err_bit      = msg_app.AxisFlagsFin.FLGFIN_DRV_HOMING_ERROR
    echo_timeout_bit        = msg_app.AxisFlagsFin.FLGFIN_ECHO_TIMEOUT
    pos_abs_disabled_bit    = msg_app.AxisFlagsFin.FLGFIN_POS_ABS_DISABLED
    unkown_zero_bit         = msg_app.AxisFlagsFin.FLGFIN_UNKNOWN_ZERO
    pos_fbk_err_bit         = msg_app.AxisFlagsFin.FLGFIN_POS_FEEDBACK_ERROR
    limit_vel_exceeded_bit  = msg_app.AxisFlagsFin.FLGFIN_LIMIT_VEL_EXCEEDED
    limit_pos_exceeded_bit  = msg_app.AxisFlagsFin.FLGFIN_LIMIT_POS_EXCEEDED
    limit_fza_exceeded_bit  = msg_app.AxisFlagsFin.FLGFIN_LIMIT_FZA_EXCEEDED
    yield_bit               = msg_app.AxisFlagsFin.FLGFIN_YIELD
    invalid_state_bit       = msg_app.AxisFlagsFin.FLGFIN_INVALID_STATE
    drv_not_enabled_bit     = msg_app.AxisFlagsFin.FLGFIN_DRV_NOT_ENABLED
    axis_limit_torque       = msg_app.AxisFlagsFin.FLGFIN_AXIS_LIMIT_TORQUE_EXCEEDED

    end_states = []
    state = None

    if axis == 0:
        axis = 'husillo'
    elif axis == 1:
        axis = 'carga'
    else:
        axis = 'lineal'

    if flags_value & ok_bit == ok_bit:
        end_states = 'ok'
        state = 'ok'

    else:
        if flags_value & cancel_bit == cancel_bit:
            state = 'cancel'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Comando cancelado")
        if flags_value & em_stop_bit == em_stop_bit:
            state = 'em_stop'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Parada de emergencia")
        if flags_value & drv_homing_err_bit == drv_homing_err_bit:
            state = 'homming_error'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Error de cerado")
        if flags_value & echo_timeout_bit == echo_timeout_bit:
            state = 'echo_timeout'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Eco tiemout")
        if flags_value & pos_abs_disabled_bit == pos_abs_disabled_bit:
            state = 'pos_abs_disabled'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Posicion absuluta deshabilitada")
        if flags_value & unkown_zero_bit == unkown_zero_bit:
            state = 'unkown_zero'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Cero desconocido")
        if flags_value & pos_fbk_err_bit == pos_fbk_err_bit:
            state = 'pos_fbk_err'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Position feedback error")
        if flags_value & limit_vel_exceeded_bit == limit_vel_exceeded_bit:
            state = 'limit_vel_exceeded'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Limite de velocidad exedido")
        if flags_value & limit_pos_exceeded_bit == limit_pos_exceeded_bit:
            state = 'limit_pos_exceeded'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Limite de posicion exedido")
        if flags_value & limit_fza_exceeded_bit == limit_fza_exceeded_bit:
            state = 'limit_fza_exceeded'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Limite de fuerza exedido")
        if flags_value & yield_bit == yield_bit:
            end_states.append('yield')
        if flags_value & invalid_state_bit == invalid_state_bit:
            state = 'invalid_state'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Estado invalido")
        if flags_value & drv_not_enabled_bit == drv_not_enabled_bit:
            state = 'drv_not_enabled'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Driver not enabled")
        if flags_value & axis_limit_torque == axis_limit_torque:
            state = 'axis_disabled'
            end_states.append(state)
            if getattr(ws_vars.MicroState, f'end_state_{axis}') != state:
                ws_vars.MicroState.err_messages.append(f"Axis .{str(axis)} - Axis disabled")

    if axis == 'husillo':
        ws_vars.MicroState.end_state_husillo = state
    elif axis == 'carga':
        ws_vars.MicroState.end_state_carga = state
    else:
        ws_vars.MicroState.end_state_lineal = state

    #print(ws_vars.MicroState.end_state_husillo,ws_vars.MicroState.end_state_carga,ws_vars.MicroState.end_state_lineal)
    
    return end_states


def update_axis_flags(micro_data, axis):
    flag = msg_app.AcdpAxisMovementsMovEjeDataFlagsBits.slave
    ws_vars.MicroState.axis_flags[axis]['slave']            = micro_data.data.ctrl.eje[axis].flags & flag == flag

    flag = msg_app.AcdpAxisMovementsMovEjeDataFlagsBits.sync_on
    ws_vars.MicroState.axis_flags[axis]['sync_on']          = micro_data.data.ctrl.eje[axis].flags & flag == flag
    
    flag = msg_app.AcdpAxisMovementsMovEjeDataFlagsBits.em_stop
    ws_vars.MicroState.axis_flags[axis]['em_stop']          = micro_data.data.ctrl.eje[axis].flags & flag == flag

    ws_vars.MicroState.axis_flags[axis]['maq_est_val']      = micro_data.data.ctrl.eje[axis].maq_est.estado
    ws_vars.MicroState.axis_flags[axis]['estado']           = msg_app.StateMachine.get_state(ws_vars.MicroState.axis_flags[axis]['maq_est_val'])

    flag = msg_base.DrvFbkDataFlags.UNKNOWN_ZERO
    ws_vars.MicroState.axis_flags[axis]['cero_desconocido'] = micro_data.data.ctrl.eje[axis].mov_pos.med_drv.drv_fbk.flags & flag  == flag

    flag = msg_base.DrvFbkDataFlags.HOME_SWITCH
    ws_vars.MicroState.axis_flags[axis]['home_switch']      = micro_data.data.ctrl.eje[axis].mov_pos.med_drv.drv_fbk.flags & flag == flag
    
    ws_vars.MicroState.axis_flags[axis]['drv_fbk_flags']    = micro_data.data.ctrl.eje[axis].mov_pos.med_drv.drv_fbk.flags

    ws_vars.MicroState.axis_flags[axis]['flags_fin']        = micro_data.data.ctrl.eje[axis].maq_est.flags_fin
    ws_vars.MicroState.axis_flags[axis]['fin']              = check_end_flags(ws_vars.MicroState.axis_flags[axis]['flags_fin'],axis)
    ws_vars.MicroState.axis_flags[axis]['axis_id']          = axis

    ws_vars.MicroState.axis_flags[axis]['drv_flags']        = micro_data.data.ctrl.eje[axis].mov_pos.med_drv.drv_fbk.flags


def update_axis_data(micro_data):
    # if ws_vars.MicroState.count == 0:
    #     ws_vars.MicroState.graph_flag = True
    # ws_vars.MicroState.count += 1
    # if ws_vars.MicroState.count == 100:
    #     ws_vars.MicroState.graph_flag = False
    # if ws_vars.MicroState.count == 200:
    #     ws_vars.MicroState.count = 0
    # print(ws_vars.MicroState.count)
    for i in range(ctrl_vars.AXIS_IDS['axis_amount']):
        update_axis_flags(micro_data, i)
        ws_vars.MicroState.axis_measures[i]['pos_fil'] = micro_data.data.ctrl.eje[i].mov_pos.med_drv.pos_fil
        ws_vars.MicroState.axis_measures[i]['vel_fil'] = micro_data.data.ctrl.eje[i].mov_pos.med_drv.vel_fil
        ws_vars.MicroState.axis_measures[i]['torque_fil'] = micro_data.data.ctrl.eje[i].mov_pos.med_drv.torque_fil
        ws_vars.MicroState.axis_measures[i]['pos_abs'] = micro_data.data.ctrl.eje[i].mov_pos.med_drv.drv_fbk.pos_abs
    
    if ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['estado'] == 'initial' and ws_vars.MicroState.rem_i_states[1]['clampeo_plato_expandido']:
        time_diff = datetime.now() - ws_vars.MicroState.load_on_timer
        if time_diff.total_seconds() >= ctrl_vars.CABEZAL_ON_TIMEOFF:
            print('Cabezal timeout excedido')
            ws_vars.MicroState.err_messages.append('Tiempo de cabezal encendido con clampeo excedido')
            ws_vars.MicroState.turn_load_drv_off = True
    else:
        ws_vars.MicroState.load_on_timer = datetime.now()
    
    enable_flag = msg_base.DrvFbkDataFlags.ENABLED
    if (ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['giro']]['drv_flags'] & enable_flag or ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['giro']]['estado'] == 'slave') and round(ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['giro']]['vel_fil'], 0) == 0:
        # si esta en enable,slave,velocidad 0
        inicio = time.time()
        # print("entra en condicion de apagar husillo")

        if ws_vars.MicroState.master_running == 0 and ws_vars.MicroState.roscado_ongoing == False: #roscado_info.running == 0 and 
            # from apps.control.models import RoutineInfo
            # roscado_info = RoutineInfo.objects.get(name='roscado')
            # if roscado_info.running == 0:
            time_diff = datetime.now() - ws_vars.MicroState.turn_on_timer
            if time_diff.total_seconds() >= ctrl_vars.GIRO_ON_TIMEOUT:
                # print("pone en true el apagar husillo")
                # ws_vars.MicroState.turn_turn_drv_off = True
                pass
        
        fin = time.time()
        #print(fin-inicio)
    
    else:
        ws_vars.MicroState.turn_on_timer = datetime.now()
    
    


def update_rem_io_states(micro_data):
    g_1_i = {}
    g_2_i = {}
    g_1_o = {}
    g_2_o = {}
    ws_vars.MicroState.rem_i_states = []
    ws_vars.MicroState.rem_o_states = []
    ws_vars.MicroState.rem_i = []
    ws_vars.MicroState.rem_o = []
    for i in range(len(ctrl_vars.REM_DI_G1_STATES)):
        keys = (
            ctrl_vars.REM_DI_G1_ARR[i],
            ctrl_vars.REM_DI_G2_ARR[i],
            ctrl_vars.REM_DO_G1_ARR[i],
            ctrl_vars.REM_DO_G2_ARR[i]
            )
        flag = 1 << i
        # print(i)
        if keys[0]:
            g_1_i[keys[0]] = (micro_data.data.ctrl.rem_io.di16[0] & flag == flag)
            ctrl_vars.REM_DI_G1_STATES[keys[0]] = g_1_i[keys[0]]
        if keys[1]:
            g_2_i[keys[1]] = (micro_data.data.ctrl.rem_io.di16[1] & flag == flag)
            ctrl_vars.REM_DI_G2_STATES[keys[1]] = g_2_i[keys[1]]
        if keys[2]:
            g_1_o[keys[2]] = (micro_data.data.ctrl.rem_io.do16[0] & flag == flag)
            ctrl_vars.REM_DO_G1_STATES[keys[2]] = g_1_o[keys[2]]
        if keys[3]:
            g_2_o[keys[3]] = (micro_data.data.ctrl.rem_io.do16[1] & flag == flag)
            ctrl_vars.REM_DO_G2_STATES[keys[3]] = g_2_o[keys[3]]
    states = {
        'i1': g_1_i,
        'i2': g_2_i,
        'o1': g_1_o,
        'o2': g_2_o
    }
    ws_vars.MicroState.rem_i_states.append(g_1_i)
    ws_vars.MicroState.rem_i_states.append(g_2_i)
    ws_vars.MicroState.rem_o_states.append(g_1_o)
    ws_vars.MicroState.rem_o_states.append(g_2_o)
    ws_vars.MicroState.rem_i.append(micro_data.data.ctrl.rem_io.di16[0])
    ws_vars.MicroState.rem_i.append(micro_data.data.ctrl.rem_io.di16[1])
    ws_vars.MicroState.rem_o.append(micro_data.data.ctrl.rem_io.do16[0])
    ws_vars.MicroState.rem_o.append(micro_data.data.ctrl.rem_io.do16[1])
    return states


def update_loc_io_states(micro_data):
    loc_in = {}
    loc_out = {}
    for i in range(len(ctrl_vars.LOC_DI_ARR)):
        flag = 1 << i
        key = ctrl_vars.LOC_DI_ARR[i]
        loc_in[key] = (micro_data.data.ctrl.loc_io.di16 & flag == flag)
        ctrl_vars.LOC_DI_STATES[key] = loc_in[key]
        ws_vars.MicroState.loc_i[key] = micro_data.data.ctrl.loc_io.di16 & flag
    
    for i in range(len(ctrl_vars.LOC_DO_ARR)):
        flag = 1 << i
        key = ctrl_vars.LOC_DO_ARR[i]
        loc_out[key] = (micro_data.data.ctrl.loc_io.do16 & flag == flag)
        ctrl_vars.LOC_DO_STATES[key] = loc_out[key]
        ws_vars.MicroState.loc_o[key] = micro_data.data.ctrl.loc_io.do16 & flag
    
    states = {
        'i': loc_in,
        'o': loc_out
    }
    ws_vars.MicroState.loc_i_states = loc_in
    ws_vars.MicroState.loc_o_states = loc_out
    # print(ws_vars.MicroState.loc_i_states)
    return states


def update_io_states(micro_data):
    update_rem_io_states(micro_data)
    update_loc_io_states(micro_data)


def update_graph():
    if ws_vars.MicroState.graph_flag == True:
        position_value = ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['avance']]['pos_fil']
        torque_value = ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['giro']]['torque_fil']
        torque_lineal_value = ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['avance']]['torque_fil']
        ws_vars.MicroState.position_values.append(position_value)
        ws_vars.MicroState.torque_values.append(torque_value)
        ws_vars.MicroState.torque_lineal_values.append(torque_lineal_value)
        


def update_states(micro_data):
    update_io_states(micro_data)
    update_data_flags(micro_data)
    update_axis_data(micro_data)
    update_graph()
    update_front_states()           # Should always be called at the end
    # print(ws_vars.MicroState.rem_i_states[1]['cerramiento_roscado_contraido'],ws_vars.MicroState.rem_o_states[0]['expandir_cerramiento_roscado'])
    # print(ws_vars.MicroState.rem_o_states[0]['new_output'])


def update_front_messages():
    now_time = datetime.now()
    timestamp = now_time.strftime("%m/%d/%y %H:%M:%S")
    if ws_vars.MicroState.log_messages:
        log_messages = []
        for msg in ws_vars.MicroState.log_messages:
            msg = timestamp + ' - ' + msg
            log_messages.append(msg)
        ws_vars.MicroState.log_messages = log_messages
    
    if ws_vars.MicroState.err_messages:
        time_diff = now_time - ws_vars.MicroState.last_err_time
        if ws_vars.MicroState.err_messages != ws_vars.MicroState.last_err_msg or time_diff.total_seconds() >= ws_vars.MicroState.err_msg_refresh_timer:
            ws_vars.MicroState.last_err_msg = ws_vars.MicroState.err_messages
            ws_vars.MicroState.last_err_time = now_time
            err_messages = []
            for msg in ws_vars.MicroState.err_messages:
                msg = timestamp + ' - ' + msg
                err_messages.append(msg)
            ws_vars.MicroState.err_messages = err_messages
        else:
            ws_vars.MicroState.err_messages = []


def get_front_states():
    limit_fwd_flag = msg_base.DrvFbkDataFlags.POSITIVE_OT
    home_sw_flag = msg_base.DrvFbkDataFlags.HOME_SWITCH
    drv_fault_flag = msg_base.DrvFbkDataFlags.FAULT
    update_front_messages()
    
    data = {
        # Measures
        'husillo_rpm': ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['giro']]['vel_fil'],
        'husillo_torque': ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['giro']]['torque_fil'],

        'cabezal_pos': ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['pos_fil'],
        'cabezal_vel': ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['carga']]['vel_fil'],

        'avance_pos': ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['avance']]['pos_fil'],
        'avance_vel': ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['avance']]['vel_fil'],
        'avance_torque': ws_vars.MicroState.axis_measures[ctrl_vars.AXIS_IDS['avance']]['torque_fil'],

        # Axis states
        'lineal_enable': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['estado'] == 'initial',
        'cabezal_enable': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['estado'] == 'initial',
        'husillo_enable': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['giro']]['estado'] == 'initial',

        'lineal_cero_desconocido': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['cero_desconocido'],
        'cabezal_cero_desconocido': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['cero_desconocido'],

        'remote_inputs': ws_vars.MicroState.rem_i_states,
        'remote_outputs': ws_vars.MicroState.rem_o_states,

        'flags_fin_eje_carga': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['flags_fin'],
        'estado_eje_carga': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['estado'],

        'flags_fin_eje_avance': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['flags_fin'],
        'estado_eje_avance': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['estado'],

        'flags_fin_eje_giro': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['giro']]['flags_fin'],
        'estado_eje_giro': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['giro']]['estado'],

        'sync_on_avance': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['sync_on'],
        'slave_giro': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['giro']]['slave'],

        'lineal_limite_forward': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['drv_fbk_flags'] & limit_fwd_flag == 0,
        'lineal_home_switch': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['drv_fbk_flags'] & home_sw_flag == home_sw_flag,
        'cabezal_home_switch': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['drv_fbk_flags'] & home_sw_flag == home_sw_flag,

        'forward_drv_fault': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['giro']]['drv_fbk_flags'] & drv_fault_flag == drv_fault_flag,
        'lineal_drv_fault': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['avance']]['drv_fbk_flags'] & drv_fault_flag == drv_fault_flag,
        'cabezal_drv_fault': ws_vars.MicroState.axis_flags[ctrl_vars.AXIS_IDS['carga']]['drv_fbk_flags'] & drv_fault_flag == drv_fault_flag,

        # Routines
        'condiciones_init_carga_ok': len(check_init_conditions_load()) == 0,
        'condiciones_init_descarga_ok': len(check_init_conditions_unload()) == 0,
        'condiciones_init_indexar_ok': len(check_init_conditions_index()) == 0,
        'condiciones_init_roscado_ok': len(check_init_conditions_tapping()) == 0,
        'homing_on_going': ws_vars.MicroState.homing_ongoing,
        'end_master_routine': ws_vars.MicroState.end_master_routine,
        'master_running': ws_vars.MicroState.master_running,
        'master_stop':ws_vars.MicroState.master_stop,

        # 'graph': ws_vars.MicroState.graph_flag
        'graph': False,
        'graph_flag': ws_vars.MicroState.graph_flag,
        'max_torque_value': ws_vars.MicroState.max_torque_value,
        'max_torque_lineal_value': ws_vars.MicroState.max_torque_lineal_value,

        'posicion_de_inicio': ctrl_vars.ROSCADO_CONSTANTES['posicion_de_inicio'],

        # Contador de cuplas
        'roscado_contador': ctrl_vars.ROSCADO_CONSTANTES['roscado_contador'],
        'reset_roscado_contador' : ws_vars.MicroState.reset_cuplas_count,

        # Messages
        'mensajes_log': ws_vars.MicroState.log_messages,
        'mensajes_error': ws_vars.MicroState.err_messages,

        # Modo seguro automatico flag
        'state_mode_neumatic': ws_vars.MicroState.neumatic_safe_mode,
    }
    return data


def update_front_states():
    data = get_front_states()
    send_front_message(data)
    ws_vars.MicroState.log_messages = []
    ws_vars.MicroState.err_messages = []

################################################################################################
######################################## COMMANDS ##############################################
################################################################################################


# -------------------------------------------------------------------------------------------- #
# ------------------------------ Set remote/local outputs ------------------------------------ #
# -------------------------------------------------------------------------------------------- #

def set_rem_do(command, key, group, bool_value):
    msg_id = ws_vars.MicroState.last_rx_header.get_msg_id() + 1
    ws_vars.MicroState.msg_id = msg_id

    mask = None
    out_value = bool_value
    
    if group == 0:
        bit = 0x0000 + 1 << ctrl_vars.REM_DO_G1_BITS[key]
    elif group == 1:
        bit = 0x0000 + 1 << ctrl_vars.REM_DO_G2_BITS[key]
    mask = bit

    if bool_value:
        out_value = bit
    else:
        out_value = 0
    return build_msg(command, msg_id=msg_id, mask=mask, out_value=out_value, group=group)


def toggle_rem_do(command, keys, group):
    msg_id = ws_vars.MicroState.last_rx_header.get_msg_id() + 1
    ws_vars.MicroState.msg_id = msg_id
    print('*********')
    mask = None
    out_value = None
    
    if type(keys) == type([]):
        key_1 = keys[0]
        key_2 = keys[1]
        print(key_1, key_2)

        if group == 0:
            bit_1 = 0x0000 + 1 << ctrl_vars.REM_DO_G1_BITS[key_1]
            bit_2 = 0x0000 + 1 << ctrl_vars.REM_DO_G1_BITS[key_2]
        elif group == 1:
            bit_1 = 0x0000 + 1 << ctrl_vars.REM_DO_G2_BITS[key_1]
            bit_2 = 0x0000 + 1 << ctrl_vars.REM_DO_G2_BITS[key_2]

        mask = bit_1 + bit_2
        state_1 = ws_vars.MicroState.rem_o_states[group][key_1]
        state_2 = ws_vars.MicroState.rem_o_states[group][key_2]
        print(bit_1)
        print(bit_2)
        if not state_1:
            out_value = bit_1
        elif not state_2:
            out_value = bit_2
    else:
        if group == 0:
            bit = 0x0000 + 1 << ctrl_vars.REM_DO_G1_BITS[keys]
        elif group == 1:
            bit = 0x0000 + 1 << ctrl_vars.REM_DO_G2_BITS[keys]
        mask = bit
        state = ws_vars.MicroState.rem_o_states[group][keys]
        if not state:
            out_value = bit
        else:
            out_value = 0
    return build_msg(command, msg_id=msg_id, mask=mask, out_value=out_value, group=group)


def set_loc_do(command, out_name, out_value):
    bit = None
    msg_id = ws_vars.MicroState.last_rx_header.get_msg_id() + 1
    ws_vars.MicroState.msg_id = msg_id
    bit = ctrl_vars.LOC_DO_BITS[out_name]
    mask = bit
    if ctrl_vars.LOC_DI_STATES[out_name]:
        out_value = 0
    else:
        out_value = bit
    return build_msg(Commands.loc_do_set, msg_id=msg_id, out_value=out_value, mask=mask)


# -------------------------------------------------------------------------------------------- #
# -------------------------------------- General --------------------------------------------- #
# -------------------------------------------------------------------------------------------- #


def sync_on(paso):
    msg_id = ws_vars.MicroState.last_rx_header.get_msg_id() + 1
    ws_vars.MicroState.msg_id = msg_id
    header = build_msg(Commands.sync_on, msg_id = msg_id, paso=paso)
    send_message(header)


def stop():
    msg_id = ws_vars.MicroState.last_rx_header.get_msg_id() + 1
    ws_vars.MicroState.msg_id = msg_id
    header = build_msg(Commands.stop, msg_id = msg_id)
    send_message(header)


def get_message_id():
    return ws_vars.MicroState.msg_id + 1