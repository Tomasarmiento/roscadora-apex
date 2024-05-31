from datetime import datetime
from apps.service.acdp.acdp import AcdpHeader
from apps.service.acdp.messages_app import AcdpPc

class MicroState:
    # Comunications
    last_rx_header  = AcdpHeader()
    last_rx_data    = AcdpPc()
    msg_id          = 0         # Id of last msg sent
    cmd_rejected    = False
    cmd_ok          = False
    
    # Front
    log_messages    = []
    err_messages    = []

    # Remote/Local digital I/O
    rem_i_states        = []        # A dictionary with boolean values for each flag
    rem_o_states        = []
    rem_i               = []        # Int number with flags values
    rem_o               = []
    loc_i_states        = None
    loc_o_states        = None
    loc_i               = {}
    loc_o               = {}

    # Flags
    micro_flags     = {}            # Flags on the data part of the rx message
    axis_flags      = [{}, {}, {}]  # Indexes corresponds with axis index
    stopped         = False         # Raised when command/movemnt is interrupted
    stop_messages   = []            # Describes stop cause

    # Measurements
    axis_measures   = [{}, {}, {}]

    # Routines flags
    routine_stopped = False
    routine_ongoing = False
    homing_ongoing  = False
    roscado_ongoing = False
    load_allow_presure_off      = True
    roscado_allow_presure_off   = True
    first_run_load      = True
    first_two_runs_unload      = 0

    # Master routine flags
    master_running      = False
    master_stop         = False
    end_master_routine  = False
    reset_cuplas_count  = False
    iteration           = 0

    # Graph
    position_values             = []
    torque_values               = []
    torque_lineal_values        = []
    graph_flag                  = False # *** REVISAR *** pusimos para que ni bien arranque no grabe el grafico
    graph_duration              = 0
    count                       = 0
    max_torque_value            = 0
    max_torque_lineal_value     = 0

    # Error log
    last_err_msg            = None
    last_err_time           = datetime.now()
    err_msg_refresh_timer   = 10

    # General
    load_on_timer       = datetime.now()    # Timer para apagar eje de carga con cabezal clampeado
    turn_on_timer       = datetime.now()    # Timer para apagar eje de husillo con velocidad 0
    turn_load_drv_off   = False
    turn_turn_drv_off   = False

    # Nueumatic mode flags
    neumatic_safe_mode  = True     # Flag para chequear condiciones inicales antes de mandar comando neumatico

    # Flags de fin de estado
    end_state_husillo = None
    end_state_carga = None
    end_state_lineal = None

class WsCodes:
    states          = 0
    cmd_ok          = 1
    cmd_rejected    = 2
    error_msg       = 3
    log_msg         = 4
    last_rx_header  = 5

front_channel_name = ''
back_channel_name = ''