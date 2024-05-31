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
//husillo = giro     cabezal=carga      lineal=avance
socket.onmessage = function (event) {
  const datosWs = JSON.parse(event.data);

    if (datosWs) {
      // console.log(datosWs.flags_fin_eje_giro);
      // console.log(datosWs.flags_fin_eje_carga);
      // console.log(datosWs.flags_fin_eje_avance);
      //Flags de Estados
      const kEst_SafeH = document.querySelector("#kEst_Safe_H");
      const kEst_SafeC = document.querySelector("#kEst_Safe_C");
      const kEst_SafeL = document.querySelector("#kEst_Safe_L");

      //kEst_Preinitial
      const kEst_PreinitialH = document.querySelector("#kEst_Preinitial_H");
      const kEst_PreinitialC = document.querySelector("#kEst_Preinitial_C");
      const kEst_PreinitialL = document.querySelector("#kEst_Preinitial_L");

      //kEst_Initial
      const kEst_InitialH = document.querySelector("#kEst_Initial_H");
      const kEst_InitialC = document.querySelector("#kEst_Initial_C");
      const kEst_InitialL = document.querySelector("#kEst_Initial_L");

      //kEst_PoweringOn
      const kEst_PoweringOnH = document.querySelector("#kEst_PoweringOn_H");
      const kEst_PoweringOnC = document.querySelector("#kEst_PoweringOn_C");
      const kEst_PoweringOnL = document.querySelector("#kEst_PoweringOn_L");

      //kEst_PoweringOff
      const kEst_PoweringOffH = document.querySelector("#kEst_PoweringOff_H");
      const kEst_PoweringOffC = document.querySelector("#kEst_PoweringOff_C");
      const kEst_PoweringOffL = document.querySelector("#kEst_PoweringOff_L");

      //kEst_Stopping
      const kEst_StoppingH = document.querySelector("#kEst_Stopping_H");
      const kEst_StoppingC = document.querySelector("#kEst_Stopping_C");
      const kEst_StoppingL = document.querySelector("#kEst_Stopping_L");

      //kEst_FastStopping
      const kEst_FastStoppingH = document.querySelector("#kEst_FastStopping_H");
      const kEst_FastStoppingC = document.querySelector("#kEst_FastStopping_C");
      const kEst_FastStoppingL = document.querySelector("#kEst_FastStopping_L");

      //kEst_Homing
      const kEst_HomingH = document.querySelector("#kEst_Homing_H");
      const kEst_HomingC = document.querySelector("#kEst_Homing_C");
      const kEst_HomingL = document.querySelector("#kEst_Homing_L");

      //kEst_Positioning
      const kEst_PositioningH = document.querySelector("#kEst_Positioning_H");
      const kEst_PositioningC = document.querySelector("#kEst_Positioning_C");
      const kEst_PositioningL = document.querySelector("#kEst_Positioning_L");

      //kEst_MovToHel
      const kEst_MovToVelH = document.querySelector("#kEst_MovToVel_H");
      const kEst_MovToVelC = document.querySelector("#kEst_MovToVel_C");
      const kEst_MovToVelL = document.querySelector("#kEst_MovToVel_L");

      //kEst_MovToPos
      const kEst_MovToPosH = document.querySelector("#kEst_MovToPos_H");
      const kEst_MovToPosC = document.querySelector("#kEst_MovToPos_C");
      const kEst_MovToPosL = document.querySelector("#kEst_MovToPos_L");

      //kEst_MovToPosLoad
      const kEst_MovToPosLoadH = document.querySelector("#kEst_MovToPosLoad_H");
      const kEst_MovToPosLoadC = document.querySelector("#kEst_MovToPosLoad_C");
      const kEst_MovToPosLoadL = document.querySelector("#kEst_MovToPosLoad_L");

      //kEst_MovToFza
      const kEst_MovToFzaH = document.querySelector("#kEst_MovToFza_H");
      const kEst_MovToFzaC = document.querySelector("#kEst_MovToFza_C");
      const kEst_MovToFzaL = document.querySelector("#kEst_MovToFza_L");
      

      // Flags Fin de Estados
      const flgFinEstadosH = document.getElementsByClassName("fin-estadosH");
      const flgFinEstadosC = document.getElementsByClassName("fin-estadosC");
      const flgFinEstadosL = document.getElementsByClassName("fin-estadosL");

      datosWs.estado_eje_avance == 'safe'
      ? (kEst_SafeL.className = "estadoL led led-green")
      : (kEst_SafeL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'safe'
      ? (kEst_SafeC.className = "estadoC led led-green")
      : (kEst_SafeC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'safe'
      ? (kEst_SafeH.className = "estadoH led led-green")
      : (kEst_SafeH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'pre_initial'
      ? (kEst_PreinitialL.className = "estadoL led led-green")
      : (kEst_PreinitialL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'pre_initial'
      ? (kEst_PreinitialC.className = "estadoC led led-green")
      : (kEst_PreinitialC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'pre_initial'
      ? (kEst_PreinitialH.className = "estadoH led led-green")
      : (kEst_PreinitialH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'initial'
      ? (kEst_InitialL.className = "estadoL led led-green")
      : (kEst_InitialL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'initial'
      ? (kEst_InitialC.className = "estadoC led led-green")
      : (kEst_InitialC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'initial'
      ? (kEst_InitialH.className = "estadoH led led-green")
      : (kEst_InitialH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'powering_on'
      ? (kEst_PoweringOnL.className = "estadoL led led-green")
      : (kEst_PoweringOnL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'powering_on'
      ? (kEst_PoweringOnC.className = "estadoC led led-green")
      : (kEst_PoweringOnC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'powering_on'
      ? (kEst_PoweringOnH.className = "estadoH led led-green")
      : (kEst_PoweringOnH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'powering_off'
      ? (kEst_PoweringOffL.className = "estadoL led led-green")
      : (kEst_PoweringOffL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'powering_off'
      ? (kEst_PoweringOffC.className = "estadoC led led-green")
      : (kEst_PoweringOffC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'powering_off'
      ? (kEst_PoweringOffH.className = "estadoH led led-green")
      : (kEst_PoweringOffH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'stopping'
      ? (kEst_StoppingL.className = "estadoL led led-green")
      : (kEst_StoppingL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'stopping'
      ? (kEst_StoppingC.className = "estadoC led led-green")
      : (kEst_StoppingC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'stopping'
      ? (kEst_StoppingH.className = "estadoH led led-green")
      : (kEst_StoppingH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'fast_stopping'
      ? (kEst_FastStoppingL.className = "estadoL led led-green")
      : (kEst_FastStoppingL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'fast_stopping'
      ? (kEst_FastStoppingC.className = "estadoC led led-green")
      : (kEst_FastStoppingC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'fast_stopping'
      ? (kEst_FastStoppingH.className = "estadoH led led-green")
      : (kEst_FastStoppingH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'homing'
      ? (kEst_HomingL.className = "estadoL led led-green")
      : (kEst_HomingL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'homing'
      ? (kEst_HomingC.className = "estadoC led led-green")
      : (kEst_HomingC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'homing'
      ? (kEst_HomingH.className = "estadoH led led-green")
      : (kEst_HomingH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'positioning'
      ? (kEst_PositioningL.className = "estadoL led led-green")
      : (kEst_PositioningL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'positioning'
      ? (kEst_PositioningC.className = "estadoC led led-green")
      : (kEst_PositioningC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'positioning'
      ? (kEst_PositioningH.className = "estadoH led led-green")
      : (kEst_PositioningH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'mov_to_vel'
      ? (kEst_MovToVelL.className = "estadoL led led-green")
      : (kEst_MovToVelL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'mov_to_vel'
      ? (kEst_MovToVelC.className = "estadoC led led-green")
      : (kEst_MovToVelC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'mov_to_vel'
      ? (kEst_MovToVelH.className = "estadoH led led-green")
      : (kEst_MovToVelH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'mov_to_pos'
      ? (kEst_MovToPosL.className = "estadoL led led-green")
      : (kEst_MovToPosL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'mov_to_pos'
      ? (kEst_MovToPosC.className = "estadoC led led-green")
      : (kEst_MovToPosC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'mov_to_pos'
      ? (kEst_MovToPosH.className = "estadoH led led-green")
      : (kEst_MovToPosH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'mov_to_pos_load'
      ? (kEst_MovToPosLoadL.className = "estadoL led led-green")
      : (kEst_MovToPosLoadL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'mov_to_pos_load'
      ? (kEst_MovToPosLoadC.className = "estadoC led led-green")
      : (kEst_MovToPosLoadC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'mov_to_pos_load'
      ? (kEst_MovToPosLoadH.className = "estadoH led led-green")
      : (kEst_MovToPosLoadH.className = "estadoH led led-grey");

      datosWs.estado_eje_avance == 'mov_to_fza'
      ? (kEst_MovToFzaL.className = "estadoL led led-green")
      : (kEst_MovToFzaL.className = "estadoL led led-grey");
      datosWs.estado_eje_carga == 'mov_to_fza'
      ? (kEst_MovToFzaC.className = "estadoC led led-green")
      : (kEst_MovToFzaC.className = "estadoC led led-grey");
      datosWs.estado_eje_giro == 'mov_to_fza'
      ? (kEst_MovToFzaH.className = "estadoH led led-green")
      : (kEst_MovToFzaH.className = "estadoH led led-grey");


      
      for (let i = 0; i < flgFinEstadosH.length; i++) {
        // console.log(datosWs.flags_fin_eje_giro.toString(2).split('').reverse()[i]);
        datosWs.flags_fin_eje_giro.toString(2).split('').reverse()[i] == 1
          ? (flgFinEstadosH[i].className = "fin-estadosH led led-green")
          : (flgFinEstadosH[i].className = "fin-estadosH led led-grey");
      }
  
      for (let i = 0; i < flgFinEstadosC.length; i++) {
        datosWs.flags_fin_eje_carga.toString(2).split('').reverse()[i] == 1
          ? (flgFinEstadosC[i].className = "fin-estadosC led led-green")
          : (flgFinEstadosC[i].className = "fin-estadosC led led-grey");
      }

      for (let i = 0; i < flgFinEstadosL.length; i++) {
        datosWs.flags_fin_eje_avance.toString(2).split('').reverse()[i] == 1
          ? (flgFinEstadosL[i].className = "fin-estadosL led led-green")
          : (flgFinEstadosL[i].className = "fin-estadosL led led-grey");
      }
    }
}