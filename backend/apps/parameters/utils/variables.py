# -------------------------------------------------------------------------------------------- #
# ---------------------------------- Parts parameters ---------------------------------------- #
# -------------------------------------------------------------------------------------------- #

PARAM_NAMES = [
    'paso_de_rosca',
    'posicion_de_aproximacion',
    'velocidad_en_vacio',
    'posicion_final_de_roscado',
    'velocidad_de_roscado',
    'posicion_salida_de_roscado',
    'velocidad_de_retraccion',
    'posicion_de_inicio',
    'torque_tolerado',
    'roscado_contador',
    'soluble_intermitente',
    'modelo',
]


PARAM_DEFAULT_VALUES_1 = {
    'paso_de_rosca': 2.54,
    'posicion_de_aproximacion': -80,
    'velocidad_en_vacio': 50,
    'posicion_final_de_roscado': -205,
    'velocidad_de_roscado': 6,
    'posicion_salida_de_roscado': -81,
    'velocidad_de_retraccion': 10,
    'posicion_de_inicio': 5,
    'torque_tolerado': 100,
    'soluble_intermitente': 0,
    'modelo': 0,
}

PARAM_DEFAULT_VALUES_2 = {
    'paso_de_rosca': 2.54,
    'posicion_de_aproximacion': -80,
    'velocidad_en_vacio': 50,
    'posicion_final_de_roscado': -205,
    'velocidad_de_roscado': 6,
    'posicion_salida_de_roscado': -82,
    'velocidad_de_retraccion': 10,
    'posicion_de_inicio': 5,
    'torque_tolerado': 100,
    'soluble_intermitente': 0,
    'modelo': 0,
}

PARAM_DEFAULT_VALUES_3 = {
    'paso_de_rosca': 2.54,
    'posicion_de_aproximacion': -80,
    'velocidad_en_vacio': 50,
    'posicion_final_de_roscado': -205,
    'velocidad_de_roscado': 6,
    'posicion_salida_de_roscado': -83,
    'velocidad_de_retraccion': 10,
    'posicion_de_inicio': 5,
    'torque_tolerado': 100,
    'soluble_intermitente' : 0,
    'modelo': 0,
}

PARAM_DEFAULT_VALUES = {
    1: PARAM_DEFAULT_VALUES_1,
    2: PARAM_DEFAULT_VALUES_2,
    3: PARAM_DEFAULT_VALUES_3
}

PARAMS_UNITS = {
    'paso_de_rosca': 'mm/v',
    'posicion_de_aproximacion': 'mm',
    'velocidad_en_vacio': 'mm/seg',
    'posicion_final_de_roscado': 'mm',
    'velocidad_de_roscado': 'mm/seg',
    'velocidad_de_retraccion': 'mm/seg',
    'tiempo_de_ciclo': 'seg',
    'torque_tolerado': 'Nm',
    't_inicio_soluble': 'seg',
    'soluble_intermitente' : '-',
    'modelo': '-',
}

SELECTED_MODEL = 1
PART_MODEL_OPTIONS = (1, 2, 3)

PARAMS = {}

# -------------------------------------------------------------------------------------------- #
# ---------------------------------- Routines Parameters ------------------------------------- #
# -------------------------------------------------------------------------------------------- #

HOMING_PARAM_NAMES = [
    'position_positive_7',
    'position_mid_low',
    'position_mid_high',
    'position_negative_7'
]

HOMING_PARAMS_DEFAULT_VALUES = {
    'position_positive_7':  4,
    'position_mid_low':     -3,
    'position_mid_high':    1,
    'position_negative_7':  -4
}

ROSCADO_PARAMS_NAMES = [
    'posicion_de_aproximacion',
    'velocidad_en_vacio',
    'posicion_final_de_roscado',
    'velocidad_de_roscado',
    'posicion_salida_de_roscado',
    'velocidad_de_retraccion',
    'paso_de_rosca',
    'posicion_de_inicio',
    'torque_tolerado',
    'roscado_contador',
    'soluble_intermitente',
    'modelo',
]

ROSCADO_PARAMS_PARAMS_DEFAULT_VALUES = {
    'posicion_de_aproximacion': -80,
    'velocidad_en_vacio': 50,
    'posicion_final_de_roscado': -205,
    'velocidad_de_roscado': 6,
    'posicion_salida_de_roscado': -80,
    'velocidad_de_retraccion': 10,
    'paso_de_rosca': 2.54,
    'posicion_de_inicio': 5,
}