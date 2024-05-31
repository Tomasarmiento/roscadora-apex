window.addEventListener("DOMContentLoaded", () => {                         //todo el tiempo
    (window.location.hash);
    monitor = document.querySelector("#component-monitor");
    let btn_modoSafe = document.getElementById('modoSafe'); 
    
        btn_modoSafe.addEventListener('click', (e) => {
            let url = "http://localhost:8000/control/safe/";
    
            let xhr = new XMLHttpRequest();
    
            xhr.open("POST", url, true);
    
            //Send the proper header information along with the request
            xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
    
            xhr.send();
        });

    //Modelo Cupla
    for(let i=1; i <= 3; i++){
        let btn_id = 'selCuple' + i;
        btn = document.getElementById(btn_id);
        csrf_token = btn.getAttribute('token');
        btn.addEventListener('click', (e) => {
            btn.className = "badge lg-badge badge-pill badge-success indLargo";
            let url = "http://localhost:8000/parametros/";
            let params = "part_model=" + i + "&csrfmiddlewaretoken=" + csrf_token;
        
            let xhr = new XMLHttpRequest();
        
            xhr.open("POST", url, true);
        
            //Send the proper header information along with the request
            xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
        
            xhr.send(params);

            // location.reload(true)
        });
    }

    const selectorCupla = document.querySelector("#selectorCupla");
    selectorCupla.addEventListener("click", (e) => {
    
        switch (e.target.id) {
        case "selCuple1":
            console.log('aca');
            document.getElementById(e.target.id).className =
            "badge lg-badge badge-pill badge-success";
            selCuple2.className = "badge lg-badge badge-pill badge-secondary";
            selCuple3.className = "badge lg-badge badge-pill badge-secondary";
            break;

        case "selCuple2":
            document.getElementById(e.target.id).className =
            "badge lg-badge badge-pill badge-success";
            selCuple1.className = "badge lg-badge badge-pill badge-secondary";
            selCuple3.className = "badge lg-badge badge-pill badge-secondary";
            break;

        case "selCuple3":
            document.getElementById(e.target.id).className =
            "badge lg-badge badge-pill badge-success";
            selCuple1.className = "badge lg-badge badge-pill badge-secondary";
            selCuple2.className = "badge lg-badge badge-pill badge-secondary";
            break;
        }
    });

});