window.addEventListener("DOMContentLoaded", () => {                         //todo el tiempo
  (window.location.hash);
  let btn_reset_count = document.getElementById('resetCount');
       
  btn_reset_count.addEventListener('click', (e) => {
    let url = "http://localhost:8000/control/reset-cuplas-count/";

    let xhr = new XMLHttpRequest();

    xhr.open("POST", url, true);

    //Send the proper header information along with the request
    xhr.setRequestHeader("Content-type", "application/x-www-form-urlencoded");

    xhr.send();
  });

});