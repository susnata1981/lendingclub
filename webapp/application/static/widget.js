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
          $this.endpoint, {
            'loan_amount': $this.loan_amount,
            'loan_duration': $this.loan_duration
          },
          function(response) {
            // $($this.loanInfoSectionSel).show();
            // console.log('setting o/p to '+$this.loanInfoSectionSel);
            $($this.loanInfoSectionSel).html(response);
            $this.notifyListeners();
          }
        )
      }

      this.notifyListeners = function() {
        for (var i = 0; i < $this.listeners.length; i++) {
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
          }
        });
      }

      this.addListener = function(listener) {
        $this.listeners.push(listener);
      }

      this.bind = function() {
        $this.setLoanDuration($this.loan_duration);
        $this.setLoanAmount($this.loan_amount);
        // $($this.loanInfoSectionSel).hide();

        this.registerLoanAmountListener();
        this.registerLoanDurationListener();
      }
    }
