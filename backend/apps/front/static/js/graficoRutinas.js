
      const totalDuration = 10000;
      const delayBetweenPoints = totalDuration / data.length;
      const previousY = (ctx) => ctx.index === 0 
      ? ctx.chart.scales.y.getPixelForValue(100) 
      : ctx.chart.getDatasetMeta(ctx.datasetIndex).data[ctx.index - 1].getProps(['y'], true).y;
      console.log('levanta grafico.js');
document.addEventListener("DOMContentLoaded", (e) => {
  
      //Configuration variables
      var updateInterval = 20 //in ms
      var numberElements = 200;
  
      //Globals
      var updateCount = 0;
  
      // Chart Objects
      var xAccelChart = $("#xAccelChart");
      //chart instances & configuration
      
  
      const btnContainer = document.querySelector("#resetZoomDiv");
     
      var commonOptions = {
          scales: {
              yAxes: [{
                  ticks: {
                      beginAtZero:true
                  },
              }],
              xAxes: [{
                  ticks: {
                      beginAtZero:true
                  }
              }]
          },
          backgroundColor: '#ffffff73',
          legend: {display: true},
          tooltips:{
            enabled: false
          },
      };
      
      var xAccelChartInstance = new Chart(xAccelChart, {
          type: 'line',
          data: {
              datasets: [{
                  label: "Torque",
                  data: 0,
                  pointRadius: 0.5,
                  fill: false,
                  borderColor: '#00aeef',
                  backgroundColor: 'blue',
                  borderWidth: 2
              }]
          },
          options: Object.assign({}, commonOptions, {
            title:{
              display: true,
              text: "cabezal_pos",
              fontSize: 18,
              backgroundColor: '#ffffff73',
            },
          }),
          options: {
              scales: {
                  yAxes: [{
                      scaleLabel: {
                          display: true,
                          labelString: 'Torque'
                      },   
                  }],
                  xAxes: [{
                      scaleLabel: {
                          display: true,
                          labelString: 'Posición'
                      },
                      type: 'time',
                      time: {
                              unit: 'second',
                              
                              displayFormats: {
                                  second: 'mm:ss'
                                }
                      },
                      displayFormats: {
                          second: 'ss:SSS'
                        }
                  }],
                 
              },
              responsive: true,
              
              maintainAspectRatio: false,
              backgroundColor: '#ffffff73',
              plugins: {
                  legend:  false,
                  zoom: {
                      pan: {
                          enabled: true,
                          mode: 'xy',
                          xScale0: {
                              max: 1e4
                          }, 
                      },
                      zoom: {
                          enabled: true,
                          mode: 'xy'
                      },
                      pinch: {
                          enabled: true,
                      },
                      sensitivity:0.1,
                  }
              },
              animation:{
                  x: {
                      type: 'number',
                      easing: 'linear',
                      duration: delayBetweenPoints,
                      from: NaN, // the point is initially skipped
                      delay(ctx) {
                      if (ctx.type !== 'data' || ctx.xStarted) {
                          return 0;
                      }
                      ctx.xStarted = true;
                      return ctx.index * delayBetweenPoints;
                      }
                  },
                  y: {
                      type: 'number',
                      easing: 'linear',
                      duration: delayBetweenPoints,
                      from: previousY,
                      delay(ctx) {
                      if (ctx.type !== 'data' || ctx.yStarted) {
                          return 0;
                      }
                      ctx.yStarted = true;
                      return ctx.index * delayBetweenPoints;
                      }
                  }
              },
          }   
      });

    socket.onmessage = function (event) {
    const datosWs = JSON.parse(event.data);
    
    if(datosWs){
        console.log(datosWs)
        xAccelChartInstance.data.labels.push(new Date());            //(datosWs.cabezal_pos).toFixed(1);
        xAccelChartInstance.data.datasets.forEach((dataset) =>{dataset.data.push(datosWs.husillo_torque).toFixed(1)});
    if(updateCount > numberElements){
        xAccelChartInstance.data.labels.shift();
        xAccelChartInstance.data.datasets[0].data.shift();
    }
    else updateCount++;
    xAccelChartInstance.update();
    }
    };

});