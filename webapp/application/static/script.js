$(function() {
    var Z = (function() {
        var LANDING_PAGE_SECTION = [
            // '#faq-section'
        ];

        function initialize_video_player() {
           $('.video').parent().click(function () {
              if ($(this).children(".video").get(0).paused) {
                $(this).children(".video").get(0).play();
                $(this).children(".playpause").fadeOut();
                ga('send', {
                    'hitType': 'event',
                    'eventCategory': 'play_video',
                    'eventAction': 'button_click',
                    'eventLabel': 'explainer_video'
                });
              } else {
                $(this).children(".video").get(0).pause();
                $(this).children(".playpause").fadeIn();
              }
            });
        }

        function createChartOptions(opt) {
            return {
                title: opt.title,
                titleTextStyle: {
                    fontSize: 20,
                    color: '#555',
                },
                hAxis: {
                    title: opt.hAxis.title,
                },
                vAxis: {
                    title: opt.vAxis.title,
                },
                legend: {
                    position: 'right',
                    textStyle: {
                        color: 'blue',
                        fontSize: 12
                    }
                },
                width: 740,
                height: 460,
                series: {
                    0: {
                        lineWidth: 3,
                        color: 'red'
                    },
                    1: {
                        lineWidth: 3,
                        color: 'green'
                    },
                    2: {
                        lineWidth: 3,
                        color: 'red'
                    },
                    3: {
                        lineWidth: 3,
                        color: 'green'
                    }
                },
            };
        }

        function drawChart() {
            var interestData = google.visualization.arrayToDataTable([
                ["Days", "Borrow $150 (Payday)", {
                    role: "style"
                }, {
                    role: 'annotation'
                }, "Borrow $150 (Ziplly)", {
                    role: "style"
                }, {
                    role: 'annotation'
                }],
                [0, 30, "#f44336", undefined, 0, "#4caf50", undefined],
                [14, 30, "#f44336", "$30", 0, "#4caf50", "$0"],
                [28, 60, "#f44336", "$60", 0, "#4caf50", "$0"],
                [42, 90, "#f44336", "$90", 15, "#4caf50", "$15"],
                [56, 120, "#f44336", "$120", 30, "#4caf50", "$30"],
            ]);

            var principalData = google.visualization.arrayToDataTable([
                ["Days", "Borrow $150 (Payday)", {
                    role: "style"
                }, {
                    role: 'annotation'
                }, "Borrow $150 (Ziplly)", {
                    role: "style"
                }, {
                    role: 'annotation'
                }],
                [0, 180, "#f44336", undefined, 150, "#4caf50", undefined],
                [14, 180, "#f44336", "$180", 150, "#4caf50", "$150"],
                [28, 210, "#f44336", "$210", 150, "#4caf50", "$150"],
                [42, 240, "#f44336", "$240", 165, "#4caf50", "$165"],
                [56, 270, "#f44336", "$270", 180, "#4caf50", "$180"],
            ]);

            // Instantiate and draw our chart, passing in some options.
            var chart = new google.visualization.LineChart(document.getElementById('interest-comparison'));
            chart.draw(interestData, createChartOptions({
                'title': 'Interest charge comparison: Payday vs Ziplly',
                'hAxis': {
                    'title': 'Days'
                },
                'vAxis': {
                    'title': 'Interest charge($)'
                }
            }));

            var chart = new google.visualization.LineChart(document.getElementById('principal-comparison'));
            chart.draw(principalData, createChartOptions({
                'title': 'Amount owed comparison: Payday vs Ziplly',
                'hAxis': {
                    'title': 'Days'
                },
                'vAxis': {
                    'title': 'Amount owed ($)'
                }
            }));
        }

        function show_notification(alerttype, message) {
          $("#alert-placeholder").html(
            '<div id="alertdiv" class="alert ' +  alerttype + '"><span>'+message+'</span></div>');
          $("#alertdiv").fadeOut(2500);
        }

        function register_user(selector, email_id, name_id) {
            var emailRegex = /\S+@\S+\.\S+/;
            var name = $("input[name='"+name_id+"']").val();
            var msg = '';
            var valid = true;
            if (name == undefined || name.length == 0) {
                msg = 'Must enter a name<br/>';
                valid = false;
            }

            var email = $("input[name='"+email_id+"']").val();
            if (email == undefined || email.length == 0) {
                msg += 'Must enter email address<br/>';
                valid = false;
            }

            if (email.length != 0 && !emailRegex.test(email)) {
                msg += 'Must be a valid email address';
                valid = false;
            }

            if (!valid) {
              show_notification('alert-danger', msg)
              return;
            }

            $(selector).attr('disabled','true');
            $("#circular-wait-section").show();
            var toast_duration = 1500;
            $.post(
                '/register_user_ajax', {
                    'name': name,
                    'email': email,
                },
                function(data) {
                  $("#circular-wait-section").hide();
                  $(selector).removeAttr('disabled');
                    var content = "<div>";
                    var alerttype = 'alert alert-success';
                    var message = '';
                    if (data.error) {
                      alerttype = 'alert alert-danger'
                      message = 'Sorry we were unable to register';
                        // Materialize.toast('Failed to register user: ' + email, toast_duration);
                    } else {
                        // Materialize.toast('Thanks for expressing interest!', toast_duration);
                        message = 'Thanks for expressing your interest';
                    }
                    show_notification('alert-success', message)

                    $("input[name='"+email_id+"'").val("");
                    $("input[name='"+name_id+"'").val("");
                }
            )
        }

        function add_notification_button_handler(btnSeletor, emailFieldSelector, nameFieldSelector) {
          $(btnSeletor).click(function(e) {
              e.preventDefault();
              ga('send', {
                  'hitType': 'event',
                  'eventCategory': 'landing_page_signup',
                  'eventAction': 'button_click',
                  'eventLabel': $(this).attr('class')
              });
              register_user(this, emailFieldSelector, nameFieldSelector);
          });
        }

        function phone_number_formatter() {
            var number = $(this).val().replace(/-/g,'');
            if (number.length < 3) {
              return;
            }

            if (number.length > 10) {
              number = number.substring(0, 10);
            }

            var nn = '';
            for (var i = 0; i < number.length; i++) {
              if (i == 3 || i == 6 ) {
                nn += '-';
                nn += number[i];
              } else {
                nn += number[i];
              }
            }
            $(this).val(nn)
        }

        function dob_formatter() {
            var number = $(this).val().replace(/\//g,'');
            if (number.length < 3) {
              return;
            }

            if (number.length > 8) {
              number = number.substring(0, 8);
            }

            var nn = '';
            for (var i = 0; i < number.length; i++) {
              if (i == 2 || i == 4 ) {
                nn += '/';
                nn += number[i];
              } else {
                nn += number[i];
              }
            }
            $(this).val(nn)
        }

        function ssn_formatter() {
            var number = $(this).val().replace(/-/g,'');

            if (number.length < 3) {
              return;
            }

            if (number.length > 9) {
              number = number.substring(0, 9);
            }

            var nn = '';
            for (var i = 0; i < number.length; i++) {
              if (i == 3 || i == 5 ) {
                nn += '-';
                nn += number[i];
              } else {
                nn += number[i];
              }
            }
            $(this).val(nn)
        }

        function init() {
            // google.charts.load('current', {'packages': ['corechart']});
            // google.charts.setOnLoadCallback(drawChart);

            // initialize_video_player();

            (function(i, s, o, g, r, a, m) {
                i['GoogleAnalyticsObject'] = r;
                i[r] = i[r] || function() {
                    (i[r].q = i[r].q || []).push(arguments)
                }, i[r].l = 1 * new Date();
                a = s.createElement(o),
                    m = s.getElementsByTagName(o)[0];
                a.async = 1;
                a.src = g;
                m.parentNode.insertBefore(a, m)
            })(window, document, 'script', 'https://www.google-analytics.com/analytics.js', 'ga');

            ga('create', 'UA-82892733-1', 'auto');
            ga('send', 'pageview');
            // slide();

            $(window).scroll(function() {
                // console.log('scrolling wTop = '+$(window).scrollTop());
                for (var i = LANDING_PAGE_SECTION.length - 1; i >= 0; i--) {
                    var sectionTop = $(LANDING_PAGE_SECTION[i]).position().top;
                    if ($(window).scrollTop() >= sectionTop) {
                        ga('send', {
                            'hitType': 'event',
                            'eventCategory': 'scroll',
                            'eventAction': 'view',
                            'eventLabel': LANDING_PAGE_SECTION[i].substring(1)
                        });
                        break;
                    }
                }
            });

            add_notification_button_handler('.notify-btn', 'email', 'name');
            add_notification_button_handler('.notify-btn2', 'email2', 'name2');

            // $('ul.tabs').tabs();
            // $('.modal-trigger').leanModal();

            $("#resend_btn").click(function(e) {
              e.preventDefault()
              $.post(
                '/account/resend_verification',
                function(data) {
                 if (!data.error) {
                   Materialize.toast('Verification code resent', 4000)
                 }
                }
              )
            });

            // $("#request-money-btn").click(function(e) {
            //   console.log('clicked...');
            //   $(this).parent().find("input[name='requested_amount']").val('');
            // });
            //
            // $("#request-money-form").submit(function(e) {
            //   console.log('submitting request money form...');
            //   $(this).find("input[name='requested_amount']").val('');
            // });

            // $("#payday-cartoon").fadeOut();

            // Cartoon animation
            // $("#logo-link").hover(function() {
            //   $("#payday-cartoon").fadeIn(500);
            //   setTimeout("$('#payday-cartoon').fadeOut(500);", 1000);
            // });

            // $('.datepicker').pickadate({
            //     selectMonths: true, // Creates a dropdown to control month
            //     selectYears: 100,
            // });

            $('.tooltipped').tooltip({delay: 50});

            $('.phone_number').keyup(phone_number_formatter);
            $('.ssn').keyup(ssn_formatter);
            $('.dob').keyup(dob_formatter);

            $('.dropdown-toggle').dropdown();
        }

        return {
            init: init
        };
    }());

    Z.init();
});
