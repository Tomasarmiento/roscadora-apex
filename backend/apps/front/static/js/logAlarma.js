var data = []
var monitor = null;

const socket = new WebSocket("ws://127.0.0.1:8000/ws/front/");
socket.addEventListener("open", function (event) {
    socket.send(
        JSON.stringify({
        message: "datos",      
        })
    );
});
// Escucha cierre de WebSocket
socket.onclose = function (event) {
    window.location.reload();
};
    
window.addEventListener("hashchange", () => {                  //cuando tocas f5
    (window.location.hash);
    monitor = document.querySelector("#component-monitor");

});

window.addEventListener("DOMContentLoaded", () => {                         //todo el tiempo
    (window.location.hash);
    cuadroDeErrores = document.querySelector("#terminalDeTextoErrores");
    if (sessionStorage.getItem("mensajesError") && cuadroDeErrores) {
        console.log('aca');
        let ul = document.getElementById("cuadroMensajesErrores");
        const listaMensajes = sessionStorage.getItem("mensajesError").split(",").reverse();
        for (let i = 0; i < listaMensajes.length; i++) {
            const li = document.createElement("li");
            li.setAttribute("style", "list-style: none;");
            li.innerHTML = listaMensajes[i];
            ul.appendChild(li);
        }
    }

    let btn_servo1 = document.getElementById('servoCarga');
    btn_servo1.addEventListener('click', (e) => {
        sendResetDrvFalutsCmd(btn_servo1.getAttribute('cmd'), btn_servo1.getAttribute('axis_id'));
    });


    let btn_servo2 = document.getElementById('servoGiro');
    btn_servo2.addEventListener('click', (e) => {
        sendResetDrvFalutsCmd(btn_servo2.getAttribute('cmd'), btn_servo2.getAttribute('axis_id'));
    });


    let btn_servo3 = document.getElementById('servoAvance');
    btn_servo3.addEventListener('click', (e) => {
        sendResetDrvFalutsCmd(btn_servo3.getAttribute('cmd'), btn_servo3.getAttribute('axis_id'));
    });

   
    var listaMensajesErrores = [];

    const resetLogAlarma = document.querySelector("#limpiarLogAlarma");
    resetLogAlarma.addEventListener('click', (e) => {
        sessionStorage.removeItem("mensajesError");
        sessionStorage.setItem("mensajesError", listaMensajesErrores);
        location.reload(true);
        
    });

    const resetLogMensajes = document.querySelector("#limpiarLogMensajes");
    resetLogMensajes.addEventListener('click', (e) => {
        sessionStorage.removeItem("mensajes");
        sessionStorage.setItem("mensajes", listaMensajesErrores);
        location.reload(true);
        
    });

    socket.onmessage = function (event) {
        const datosWs = JSON.parse(event.data);
        
        if (datosWs.mensajes_error.length > 0) {
            listaMensajesErrores.push(datosWs.mensajes_error);
            sessionStorage.setItem("mensajesError", listaMensajesErrores);
            InsertarTextoErrores(datosWs.mensajes_error);
        };

        const servoIndicator_carga = document.querySelector("#squareCarga");
        const servoIndicator_giro = document.querySelector("#squareGiro");
        const servoIndicator_avance = document.querySelector("#squareAvance");

        //Falla servo husillo
        if (datosWs.forward_drv_fault == true){
            servoIndicator_giro.className = "square-red mb-5"
        }
        else{
            servoIndicator_giro.className = "square mb-5"
        }

        //Falla servo avance
        if (datosWs.lineal_drv_fault == true){
            servoIndicator_avance.className = "square-red mb-5"
        }
        else{
            servoIndicator_avance.className = "square mb-5"
        }

        //Falla servo carga
        if (datosWs.cabezal_drv_fault == true){
            servoIndicator_carga.className = "square-red mb-5"
        }
        else{
            servoIndicator_carga.className = "square mb-5"
        }
        
    };
});

function sendResetDrvFalutsCmd(cmd, axis) {
    const url = "http://localhost:8000/logAlarma/";
    const params = "command=" + cmd + "&axis=" + axis;

    let xhr = new XMLHttpRequest();

    xhr.open("POST", url, true);

    //Send the proper header information along with the request
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    xhr.send(params);
}