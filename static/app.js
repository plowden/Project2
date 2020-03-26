// Global parameters:
// Resize the chart canvas when its container does 
Chart.defaults.global.responsive = true;
 
// define the chart data
var hostsChartData = {
  labels : [{% for item in webex_data.hosts %}
             "{{item}}",
            {% endfor %}],
  datasets : [{
      label: '{{ webex_data.months }}',
      fill: true,
      lineTension: 0.1,
      backgroundColor: "rgba(75,192,192,0.4)",
      borderColor: "rgba(75,192,192,1)",
      borderCapStyle: 'butt',
      borderDash: [],
      borderDashOffset: 0.0,
      borderJoinStyle: 'miter',
      pointBorderColor: "rgba(75,192,192,1)",
      pointBackgroundColor: "#fff",
      pointBorderWidth: 1,
      pointHoverRadius: 5,
      pointHoverBackgroundColor: "rgba(75,192,192,1)",
      pointHoverBorderColor: "rgba(220,220,220,1)",
      pointHoverBorderWidth: 2,
      pointRadius: 1,
      pointHitRadius: 10,
      data : [{% for item in webex_data['hosts'] %}
                {{item}},
              {% endfor %}],
      spanGaps: false
  }]
}
 
// get chart canvas
var ctx = document.getElementById("hosts-chart").getContext("2d");
 
// create the chart using the chart canvas
var hosts-chart = new Chart(ctx, {
  type: 'line',
  data: hostsChartData,
});
