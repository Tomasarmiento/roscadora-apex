document.addEventListener("DOMContentLoaded", (e) => {
    let btns_stop = document.getElementsByClassName('detener');

    for(let i=0; i < btns_stop.length; i++){
        btns_stop[i].addEventListener('click', (e) => {
            let cmd = btns_stop[i].getAttribute('cmd');
            sendStopAxisCommand(cmd);
        });
    }
});

function sendStopAxisCommand(cmd, eje){
    let url = "http://localhost:8000/control/stop-all/";
    let params = "command=" + cmd;

    let xhr = new XMLHttpRequest();
    
    xhr.open("POST", url, true);

    //Send the proper header information along with the request
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    xhr.send(params);
}