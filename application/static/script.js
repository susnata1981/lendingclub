$(function() {
      function drawChart() {
        // Create the data table.
        var data = new google.visualization.DataTable();
        data.addColumn('number', 'Loan amount');
        data.addColumn('number', 'Payday loan interest charge');
        data.addColumn('number', 'Ziplly plan cost');
        data.addRows([
          [150, 180, 120],
          [300, 360, 240]
        ]);

        var data = google.visualization.arrayToDataTable([
                ["Loan Amount", "Payday Loan cost($)", { role: "style" }, { role : 'annotation' }, "Our plan cost($)", { role: "style" }, { role : 'annotation' } ],
                ["Borrow $150", 180, "#f44336", "$180", 120, "#4caf50", "$120"],
                ["Borrow $300", 360, "#f44336", "$180", 240, "#4caf50", "$240"],
              ]);

        // Set chart options
        var options = {'title':'Cost Comparison: Payday Loan vs Our Plan',
                       'width':800,
                       'height':600,
                       animation:{
                         "startup": true,
                         duration: 1000,
                         easing: 'out',
                       },
                       continuous: false,
                       colors: ['#f44336', '#4caf50'],
                       legend: { position: 'right', maxLines: 3 }
                   };

        // Instantiate and draw our chart, passing in some options.
        var chart = new google.visualization.ColumnChart(document.getElementById('plan-comparison'));
        chart.draw(data, options);
      }

      function registerChartHandler() {
          console.log('registering...'+document.getElementById('plan-overview'));
          var waypoint = new Waypoint({
              element: document.getElementById('plan-comparison'),
              handler: function(direction) {
                  drawChart();
                  waypoint.disable();
                  console.log('reached...'+direction);
              },
              offset: '20%'
          });
      }

      google.charts.load('current', {'packages':['corechart']});
      google.charts.setOnLoadCallback(registerChartHandler);

      function call_add() {
          $.post(
              '/_add',
              {
                  'a': 1,
                  'b': 2
              },
              function(data) {
                  console.log('response = '+data);
              }
          )
      }

    //   $("#notify-btn").click(function(e) {
    //       e.preventDefault();
    //       call_add();
    //   });
      //
    //   console.log('endpoint = '+$SCRIPT_ROOT);
});
