from django.shortcuts import render
from django.http import JsonResponse
from django.views.generic import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt


import apps.service.acdp.handlers as service_handlers
from apps.service.api.variables import COMMANDS

from apps.parameters.utils.variables import PART_MODEL_OPTIONS
from apps.parameters.models import Parameter

from apps.control.utils.variables import AXIS_IDS, ROUTINE_IDS, ROSCADO_CONSTANTES

from apps.ws.utils import variables as ws_vars
from apps.ws.utils.functions import get_ch_info
from apps.ws.utils.handlers import send_message
from apps.ws.models import ChannelInfo

# Create your views here.
def index(request):
    return render(request, "index.html")
  
def home(request):
    part_model = Parameter.objects.get(name='part_model')
    return render(request, "home.html", {'part_model': int(part_model.value)})

def referenciar(request):
    context = ROUTINE_IDS
    return render(request, "referenciar.html", context)

def automatico(request):
    context = COMMANDS
    context.update(ROSCADO_CONSTANTES)
    return render(request, "automatico.html", context)

def neumaticaManual(request):
    context = COMMANDS
    return render(request, "neumaticaManual.html", context)

def motoresManual(request):
    context = COMMANDS
    context['id_eje_avance'] = AXIS_IDS['avance']
    context['id_eje_carga'] = AXIS_IDS['carga']
    context['id_eje_giro'] = AXIS_IDS['giro']
    return render(request, "motoresManual.html", context=context)

def sensoresPagina2(request):
    return render(request, "sensoresP2.html")

def sensores(request):
    return render(request, "sensores.html")

def monitorEstados(request):
    return render(request, "monitorEstados.html")

def semiAutomatico(request):
    context = ROUTINE_IDS
    context.update(ROSCADO_CONSTANTES)
    return render(request, "semiautomatico.html", context)

def parametrosPagina1(request):
    return render(request, "parametrosP1.html")

def logAlarma(request):
    return render(request, "logAlarma.html", AXIS_IDS)

@method_decorator(csrf_exempt, name='dispatch')
class LogAlarm(View):

    def get(self, request):
        context = AXIS_IDS
        context['reset_drv_faults_cmd'] = COMMANDS['reset_drv_faults']
        return render(request, "logAlarma.html", AXIS_IDS)
    
    def post(self, request):
        post_req = request.POST
        msg_id = ws_vars.MicroState.last_rx_header.get_msg_id() + 1
        cmd = int(post_req['command'])
        axis = int(post_req['axis'])
        header = service_handlers.build_msg(cmd, msg_id=msg_id, eje=axis)
        ch_info = get_ch_info(ChannelInfo, 'micro')
        if ch_info:
            send_message(header, ch_info)
        return JsonResponse({"response": "ok"})