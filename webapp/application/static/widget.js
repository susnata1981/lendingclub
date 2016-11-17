    $( function() {
      var loan_duration = 1;
      var loan_amount = 500;

    function recalculate() {
      $("#amount").val( "$" + loan_amount);
      $("#loan-duration").val(loan_duration + " months");
      var total_amount = loan_duration == 1 ? loan_amount * 1.1 : loan_amount * (1.1 + loan_duration * 0.05);
      var payday_interest = ((loan_amount * 15 * loan_duration * 2)/100);
      var total_payday_amount_due = parseFloat(payday_interest + loan_amount);
      var monthly_payments = (total_amount/loan_duration).toFixed(2);
      var loan_duration_suffix = loan_duration == 1 ? "month" : "months";
      $("#loan-duration").val(loan_duration+" "+loan_duration_suffix);

      var payments_html = '<ul>';
      for (var i = 0; i < loan_duration; i++) {
        payments_html += '<li> <div class="info"> month <span class="orange-text">'+(i+1)+'</span> payment due <span class="orange-text">$'+monthly_payments+' </span></div></li>';
      }
      payments_html += '</ul>';
      payments_html += '<div class="underline"></div>';
      payments_html += '<div class="info">'+
      'total amount due &nbsp;&nbsp; <span class="orange-text">$'+total_amount.toFixed(2)+
      '</span><span class="red-text"> @Payday $'+total_payday_amount_due.toFixed(2)+'</span></div>';

      payments_html += '<div class="info">'+
      'amount borrowed &nbsp;<span class="orange-text">$'+loan_amount.toFixed(2)+'</span>'+
      '<span class="red-text"> @Payday $'+loan_amount.toFixed(2)+'</span></div>';

      payments_html += '<div class="info">'+
      'interest charges &nbsp;&nbsp;&nbsp;&nbsp;<span class="orange-text">$'+(total_amount - loan_amount).toFixed(2)+
      '&nbsp;&nbsp;<span class="red-text"> @Payday $'+payday_interest+'</span></div>';

      payments_html += '<div class="info">'+
      'with Ziplly you save &nbsp;<span class="green-text bold">$'+(payday_interest -(total_amount - loan_amount)).toFixed(2)+
      '</span></div>';

      // $("#monthly-payments").html(payments_html);
      // $("#payment-details").show();
    }

    function get_payment_plan() {
      var loan_duration_suffix = loan_duration == 1 ? "month" : "months";
      $("#loan-duration").val(loan_duration +" "+ loan_duration_suffix);
      $("#loan-amount").val("$"+loan_amount);

      $.post(
        'lending/get_payment_plan_estimate',
        {
          'loan_amount': loan_amount,
          'loan_duration': loan_duration
        },
        function(response) {
          $("#loan-info-section").show();
          $("#loan-info-section").html(response);
        }
      )
    }

    $(".amount-slider").slider({
      value:loan_amount,
      min: 500,
      max: 1000,
      step: 50,
      slide: function( event, ui ) {
        loan_amount = ui.value;
        get_payment_plan();
      }
    });

    $(".loan-duration-slider").slider({
      value: loan_duration,
      min: 1,
      max: 6,
      step: 1,
      slide: function( event, ui ) {
        loan_duration = ui.value;
        get_payment_plan();
      }
    });
    $("#loan-amount").val( "$" + loan_amount );
    $("#loan-duration").val(loan_duration + " month");
    $("#loan-info-section").hide();
    });
