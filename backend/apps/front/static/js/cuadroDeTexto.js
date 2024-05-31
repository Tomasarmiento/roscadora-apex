function InsertarTexto(datosWs) {
    var ul = document.getElementById("cuadroMensajes");
    for (let i = 0; i < datosWs.length; i++) {
      const li = document.createElement("li");
      li.setAttribute("style", "list-style: none;");
      li.innerHTML = datosWs[i];
      ul.prepend(li);
    }
  }