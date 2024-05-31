from apps.service.acdp.messages_app import AcdpAxisMovementEnums, AcdpMsgCodes
from apps.service.acdp.handlers import build_msg
from apps.service.acdp.acdp import ACDP_UDP_PORT, ACDP_IP_ADDR
from apps.service.api.variables import COMMANDS, Commands, last_rx_msg

def send_message(bytes_msg, transport, addr=(ACDP_IP_ADDR, ACDP_UDP_PORT)):
    if transport:
        transport.sendto(bytes_msg, addr)
        print('msg sent')
    else:
        print("Sin conexion")


def echo_reply(transport):
    msg_id = last_rx_msg.get_msg_id() + 1
    header = build_msg(Commands.echo_reply, msg_id = msg_id)
    send_message(header.pacself(), transport)


def open_connection(transport):
    header = build_msg(Commands.open_connection)
    send_message(header.pacself(), transport)


def force_connection(transport):
    header = build_msg(Commands.force_connection)
    send_message(header.pacself(), transport)


def close_connection(transport):
    header = build_msg(Commands.close_connection)
    send_message(header.pacself(), transport)