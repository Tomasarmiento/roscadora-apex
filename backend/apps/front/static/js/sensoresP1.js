
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

socket.onmessage = function (event) {
    const datosWs = JSON.parse(event.data);

    if (datosWs) {

        //SENSORES CARGA//
        const boquillaCargaAtras = document.querySelector("#boquillaLoaderBkwrd");
        const boquillaCargaAdelante = document.querySelector("#boquillaLoaderFwrd");
        const boquillaCargaLiberada = document.querySelector("#boquillaLoaderReleased");
        const boquillaCargaAccionada = document.querySelector("#boquillaLoaderActuated");
        const boquillaCargaConCupla = document.querySelector("#boquillaLoaderCupla");

        const giroBrazoCargaArriba = document.querySelector("#turnLoadUp");
        const giroBrazoCargaAbajo = document.querySelector("#turnLoadDown");

        const verticalCargaArriba = document.querySelector("#verticalLoadUp");
        const verticalCargaAbajo = document.querySelector("#verticalLoadDown");

        const presenciaCuplaEnCargador = document.querySelector("#presenceCuplaOnLoad");


        //SENSORES DESCARGA//
        const boquillaDescargaAtras = document.querySelector("#boquillaDownloadBkwrd");
        const boquillaDescargaAdelante = document.querySelector("#boquillaDownloadFwrd");
        const boquillaDescargaLiberada = document.querySelector("#boquillaDownloadReleased");
        const boquillaDescargaAccionada = document.querySelector("#boquillaDownloadActuated");
        const boquillaDescargaConCupla = document.querySelector("#boquillaDownloadCupla");

        const gripperDescargaVerticalArriba = document.querySelector("#gripVerticalDownloaderUp");
        const gripperDescargaVerticalAbajo = document.querySelector("#gripVerticalDownloaderDown");
        const gripperDescargaHorizontalAdelante = document.querySelector("#gripHorizontalDownloaderFwrd");
        const gripperDescargaHorizontalAtras = document.querySelector("#gripHorizontalDownloaderBkwrd");
        const gripperDescargaAccionado = document.querySelector("#gripDownloaderActuated");
        const gripperDescargaLiberado = document.querySelector("#gripDownloaderReleased");

        const giroBrazoDescargaArriba = document.querySelector("#turnArmDownloadUp");
        const giroBrazoDescargaAbajo = document.querySelector("#turnArmDownloadDown");

        const cuplaPorTobogánDescarga = document.querySelector("#cuplaToboganDownload");


        //PLATO//
        const neumaticoClampeoPlatoContraido = document.querySelector("#neumaticClampPlateContracted");
        const neumaticoClampeoPlatoExtendido = document.querySelector("#neumaticClampPlateExtended");
        const acopleLubricanteContraido = document.querySelector("#acopleLubricantContracted");
        const acopleLubricanteExtendido = document.querySelector("#acopleLubricantExtended");
        const cerramientoRoscadoExtendido = document.querySelector("#cerramientoRoscadoExtended");


        //MOTORES SENSORES//
        const ejelinealLimiteForward = document.querySelector("#axisLinearFwrd");
        const ejeLinealHoming = document.querySelector("#axisLinearHom");
        const ejeCabezalHoming = document.querySelector("#axisCabezalHom");


        //SENSORES CARGA//
        //Presencia cupla en cargador	
        datosWs.remote_inputs[1].presencia_cupla_en_cargador == false
         ? (presenciaCuplaEnCargador.className = "led led-green")
         : (presenciaCuplaEnCargador.className = "led led-grey");

        //Vertical carga abajo	
        datosWs.remote_inputs[0].vertical_carga_contraido == true
         ? (verticalCargaAbajo.className = "led led-green")
         : (verticalCargaAbajo.className = "led led-grey");

        //Vertical carga arriba	
        datosWs.remote_inputs[0].vertical_carga_expandido == false
         ? (verticalCargaArriba.className = "led led-grey")
         : (verticalCargaArriba.className = "led led-green");

        //Giro brazo carga abajo	
        datosWs.remote_inputs[0].brazo_cargador_expandido == false && datosWs.remote_inputs[0].brazo_cargador_contraido == true   
         ? (giroBrazoCargaAbajo.className = "led led-grey")
         : (giroBrazoCargaAbajo.className = "led led-green");

        //Giro brazo carga arriba	
        datosWs.remote_inputs[0].brazo_cargador_expandido == true && datosWs.remote_inputs[0].brazo_cargador_contraido == false
         ? (giroBrazoCargaArriba.className = "led led-grey")
         : (giroBrazoCargaArriba.className = "led led-green");

        //Boquilla carga con cupla	
        datosWs.remote_inputs[1].pieza_en_boquilla_carga == false
         ? (boquillaCargaConCupla.className = "led led-grey")
         : (boquillaCargaConCupla.className = "led led-green");

        //Boquilla carga liberada	
        datosWs.remote_inputs[0].boquilla_carga_contraida == true
         ? (boquillaCargaLiberada.className = "led led-grey")
         : (boquillaCargaLiberada.className = "led led-green");
        //Boquilla carga accionada
        datosWs.remote_inputs[0].boquilla_carga_expandida == true
         ? (boquillaCargaAccionada.className = "led led-grey")
         : (boquillaCargaAccionada.className = "led led-green");	

        //Boquilla carga atras
        datosWs.remote_inputs[0].puntera_carga_expandida == true && datosWs.remote_inputs[0].puntera_carga_contraida == false   
         ? (boquillaCargaAtras.className = "led led-grey")
         : (boquillaCargaAtras.className = "led led-green");
        //Boquilla carga adelante	
        datosWs.remote_inputs[0].puntera_carga_expandida == false && datosWs.remote_inputs[0].puntera_carga_contraida == true
         ? (boquillaCargaAdelante.className = "led led-grey")
         : (boquillaCargaAdelante.className = "led led-green");


        //SENSORES DESCARGA//
        //Boquilla descarga atras	
        datosWs.remote_inputs[0].puntera_descarga_expandida == false && datosWs.remote_inputs[0].puntera_descarga_contraida == true
         ? (boquillaDescargaAtras.className = "led led-green")
         : (boquillaDescargaAtras.className = "led led-grey");
        //Boquilla descarga adelante
        datosWs.remote_inputs[0].puntera_descarga_expandida == false && datosWs.remote_inputs[0].puntera_descarga_contraida == true   
         ? (boquillaDescargaAdelante.className = "led led-grey")
         : (boquillaDescargaAdelante.className = "led led-green");

        //Boquilla descarga accionada	
        datosWs.remote_inputs[0].boquilla_descarga_expandida == true
         ? (boquillaDescargaAccionada.className = "led led-grey")
         : (boquillaDescargaAccionada.className = "led led-green");

        //Boquilla descarga liberada	
        datosWs.remote_inputs[0].boquilla_descarga_contraida == true
         ? (boquillaDescargaLiberada.className = "led led-grey")
         : (boquillaDescargaLiberada.className = "led led-green");

        //Boquilla descarga con cupla
         datosWs.remote_inputs[1].pieza_en_boquilla_descarga == false
         ? (boquillaDescargaConCupla.className = "led led-grey")
         : (boquillaDescargaConCupla.className = "led led-green");

        //Gripper descarga accionado	
        datosWs.remote_inputs[0].pinza_descargadora_abierta == true && datosWs.remote_inputs[0].pinza_descargadora_cerrada == false
         ? (gripperDescargaAccionado.className = "led led-grey")
         : (gripperDescargaAccionado.className = "led led-green");
        //Gripper descarga liberado	
        datosWs.remote_inputs[0].pinza_descargadora_abierta == false && datosWs.remote_inputs[0].pinza_descargadora_cerrada == true   
         ? (gripperDescargaLiberado.className = "led led-grey")
         : (gripperDescargaLiberado.className = "led led-green");

        //Gripper descarga vertical arriba
        datosWs.remote_inputs[1].vert_pinza_desc_expandido == true
         ? (gripperDescargaVerticalArriba.className = "led led-grey")
         : (gripperDescargaVerticalArriba.className = "led led-green");
        //Gripper descarga vertical abajo
        datosWs.remote_inputs[1].vert_pinza_desc_contraido == true
         ? (gripperDescargaVerticalAbajo.className = "led led-grey")
         : (gripperDescargaVerticalAbajo.className = "led led-green");

        //Gripper descarga horizontal adelante
        datosWs.remote_inputs[1].horiz_pinza_desc_contraido == true
         ? (gripperDescargaHorizontalAdelante.className = "led led-grey")
         : (gripperDescargaHorizontalAdelante.className = "led led-green");
        //Gripper descarga horizontal atras	
        datosWs.remote_inputs[1].horiz_pinza_desc_expandido == true
         ? (gripperDescargaHorizontalAtras.className = "led led-grey")
         : (gripperDescargaHorizontalAtras.className = "led led-green");

        //Giro brazo descarga arriba	
        datosWs.remote_inputs[0].brazo_descarga_expandido == true && datosWs.remote_inputs[0].brazo_descarga_contraido == false
         ? (giroBrazoDescargaArriba.className = "led led-grey")
         : (giroBrazoDescargaArriba.className = "led led-green");
        //Giro brazo descarga abajo	
        datosWs.remote_inputs[0].brazo_descarga_expandido == false && datosWs.remote_inputs[0].brazo_descarga_contraido == true   
         ? (giroBrazoDescargaAbajo.className = "led led-grey")
         : (giroBrazoDescargaAbajo.className = "led led-green");

        //Cupla por tobogán descarga
        datosWs.remote_inputs[1].cupla_por_tobogan_descarga == true
         ? (cuplaPorTobogánDescarga.className = "led led-grey")
         : (cuplaPorTobogánDescarga.className = "led led-green");

        //PLATO//
        //Acople Lubricante Extendido	
        datosWs.remote_inputs[1].acople_lubric_expandido == false
         ? (acopleLubricanteExtendido.className = "led led-grey")
         : (acopleLubricanteExtendido.className = "led led-green");
        
        //Acople Lubricante Contraído	
        datosWs.remote_inputs[1].acople_lubric_contraido == false
         ? (acopleLubricanteContraido.className = "led led-grey")
         : (acopleLubricanteContraido.className = "led led-green");
        
        //Neumático clampeo plato Extendido	
        datosWs.remote_inputs[1].clampeo_plato_expandido == true
         ? (neumaticoClampeoPlatoExtendido.className = "led led-grey")
         : (neumaticoClampeoPlatoExtendido.className = "led led-green");
        //Neumático clampeo plato Contraído	
        datosWs.remote_inputs[1].clampeo_plato_contraido == true
         ? (neumaticoClampeoPlatoContraido.className = "led led-grey")
         : (neumaticoClampeoPlatoContraido.className = "led led-green");
        //Neumático cerramiento roscado Extendido
        datosWs.remote_inputs[1].cerramiento_roscado_contraido == false
         ? (cerramientoRoscadoExtendido.className = "led led-grey")
         : (cerramientoRoscadoExtendido.className = "led led-green");



        //MOTORES SENSORES EN EL DRIVE//
        //Eje lineal limite Forward//preguntar si hay sensor de fin de carrera
        //Eje lineal Homing
        datosWs.lineal_home_switch == true
         ? (ejeLinealHoming.className = "led led-green")
         : (ejeLinealHoming.className = "led led-grey");
        //Eje Cabezal Homing
        datosWs.cabezal_home_switch == true
         ? (ejeCabezalHoming.className = "led led-green")
         : (ejeCabezalHoming.className = "led led-grey");
         //Eje lineal limite Forward
         datosWs.lineal_limite_forward == true
         ? (ejelinealLimiteForward.className = "led led-green")
         : (ejelinealLimiteForward.className = "led led-grey");




        console.log(datosWs);
    }
}