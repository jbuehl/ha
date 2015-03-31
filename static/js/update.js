    $(document).ready(function() {
        var pending = false;    // true while an update request is pending
        var refreshId = setInterval(function() {
            if (!pending) {     // don't allow multiple pending requests
                pending = true;
                $.getJSON('update', {}, function(data) {    // get updated values
                    $.each( data, function(key, val) {      // set value and class of each
                        $('#'+key).text(val[1]);
                        $('#'+key).attr('class', val[0]);
                        });
                    pending = false;
                    });
                var tempColor = function(temp) {        // set temp color based on temp value
                    if (temp > 120){                    // magenta
                        var red = 252;
                        var green = 0;
                        var blue = 252;
                        }
                    else if (temp > 102){               // red
                        var red = 252;
                        var green = 0;
                        var blue = (temp-102)*14;
                        }
                    else if (temp > 84){                // yellow
                        var red = 252;
                        var green = (102-temp)*14;
                        var blue = 0;
                        }
                    else if (temp > 66){                // green
                        var red = (temp-66)*14;
                        var green = 252;
                        var blue = 0;
                        }
                    else if (temp > 48){                // cyan
                        var red = 0;
                        var green = 252;
                        var blue = (66-temp)*14;
                        }
                    else if (temp > 30){                // blue
                        var red = 0;
                        var green = (temp-30)*14;
                        var blue = 252;
                        }
                    else{
                        var red = 0;
                        var green = 0;
                        var blue = 252;
                        }
                    return 'rgb('+red.toString()+','+green.toString()+','+blue.toString()+')';
                    }
                $('.tempF').each(function(){
                    $(this).css('color', tempColor(parseInt($(this).text())));
                    });
                $('.tempC').each(function(){
                    $(this).css('color', tempColor(parseInt($(this).text())));
                    });
                $('.spaTemp').each(function(){
                    $(this).css('color', tempColor(parseInt($(this).text())));
                    });
                };
            }, 1000);
        $.ajaxSetup({cache: false});
        });

