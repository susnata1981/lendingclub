    // $(function() {
    //   var loan_duration = 1;
    //   var loan_amount = 500;
    //
    //   function get_payment_plan() {
    //     var loan_duration_suffix = loan_duration == 1 ? "month" : "months";
    //     $("#loan-duration").val(loan_duration + " " + loan_duration_suffix);
    //     $("#loan-amount").val("$" + loan_amount);
    //
    //     $.post(
    //       'lending/get_payment_plan_estimate', {
    //         'loan_amount': loan_amount,
    //         'loan_duration': loan_duration
    //       },
    //       function(response) {
    //         $("#loan-info-section").show();
    //         $("#loan-info-section").html(response);
    //       }
    //     )
    //   }
    //
    //   $(".amount-slider").slider({
    //     value: loan_amount,
    //     min: 500,
    //     max: 1000,
    //     step: 50,
    //     slide: function(event, ui) {
    //       loan_amount = ui.value;
    //       get_payment_plan();
    //     }
    //   });
    //
    //   $(".loan-duration-slider").slider({
    //     value: loan_duration,
    //     min: 1,
    //     max: 6,
    //     step: 1,
    //     slide: function(event, ui) {
    //       loan_duration = ui.value;
    //       get_payment_plan();
    //     }
    //   });
    //   $("#loan-amount").val("$" + loan_amount);
    //   $("#loan-duration").val(loan_duration + " month");
    //   $("#loan-info-section").hide();
    // });

    function LoanApplicationForm(loanAmountSel, loanDurationSel, loanInfoSectionSel,
      loanAmountSliderSel, loanDurationSliderSel, endpoint) {
      this.loanAmountSel = loanAmountSel;
      this.loanDurationSel = loanDurationSel;
      this.loanInfoSectionSel = loanInfoSectionSel;
      this.loanAmountSliderSel = loanAmountSliderSel;
      this.loanDurationSliderSel = loanDurationSliderSel;
      this.endpoint = endpoint;
      this.loan_duration = 1;
      this.loan_amount = 500;
      this.listeners = [];
      var $this = this;

      this.getPaymentPlan = function() {
        var loan_duration_suffix = $this.loan_duration == 1 ? "month" : "months";
        $($this.loanDurationSel).val($this.loan_duration);//+ " " + loan_duration_suffix);
        $($this.loanAmountSel).val($this.loan_amount);

        $.post(
          $this.endpoint,
          {
            'loan_amount': $this.loan_amount,
            'loan_duration': $this.loan_duration
          },
          function(response) {
            $($this.loanInfoSectionSel).show();
            $($this.loanInfoSectionSel).html(response);
          }
        )
      }

      this.notifyListeners = function() {
        for(var i = 0; i < $this.listeners.length; i++) {
          var listener = $this.listeners[i];
          if (listener.hasOwnProperty('update')) {
            listener.update();
          }
        }
      }

      this.registerLoanDurationListener = function() {
        $($this.loanDurationSliderSel).slider({
          value: $this.loan_duration,
          min: 1,
          max: 6,
          step: 1,
          slide: function(event, ui) {
            $this.loan_duration = ui.value;
            $this.getPaymentPlan();
            $this.notifyListeners();
          }
        });
      }

      this.registerLoanAmountListener = function() {
        $($this.loanAmountSliderSel).slider({
          value: $this.loan_amount,
          min: 500,
          max: 1000,
          step: 50,
          slide: function(event, ui) {
            $this.loan_amount = ui.value;
            $this.getPaymentPlan();
            $this.notifyListeners();
          }
        });
      }

      this.addListener = function(listener) {
          $this.listeners.push(listener);
      }

      this.bind = function() {
        $($this.loanAmountSel).val($this.loan_amount);
        $($this.loanDurationSel).val($this.loan_duration);
        $($this.loanInfoSectionSel).hide();

        this.registerLoanAmountListener();
        this.registerLoanDurationListener();
      }
    }
