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

    function LoanApplicationForm(loanAmountSel1, loanAmountSel2, loanDurationSel1, loanDurationSel2,
      loanInfoSectionSel, loanAmountSliderSel, loanDurationSliderSel, endpoint) {
      this.loanAmountSel1 = loanAmountSel1;
      this.loanAmountSel2 = loanAmountSel2;
      this.loanDurationSel1 = loanDurationSel1;
      this.loanDurationSel2 = loanDurationSel2;
      this.loanInfoSectionSel = loanInfoSectionSel;
      this.loanAmountSliderSel = loanAmountSliderSel;
      this.loanDurationSliderSel = loanDurationSliderSel;
      this.endpoint = endpoint;
      this.loan_duration = 1;
      this.loan_amount = 500;
      this.listeners = [];
      var $this = this;

      this.setLoanAmount = function(amount) {
        $this.loan_amount = amount;
        $($this.loanAmountSel1).val(amount);
        $($this.loanAmountSel2).val("$" + amount);
      }

      this.setLoanDuration = function(duration) {
        $this.loan_duration = duration;
        var loan_duration_suffix = duration == 1 ? "month" : "months";
        $($this.loanDurationSel1).val(duration);
        $($this.loanDurationSel2).val(duration + " " + loan_duration_suffix);
      }

      this.getPaymentPlan = function() {
        $this.setLoanAmount($this.loan_amount);
        $this.setLoanDuration($this.loan_duration);

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
        $this.setLoanDuration($this.loan_duration);
        $this.setLoanAmount($this.loan_amount);
        $($this.loanInfoSectionSel).hide();

        this.registerLoanAmountListener();
        this.registerLoanDurationListener();
      }
    }
