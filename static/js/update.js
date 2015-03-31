    $(document).ready(function() {
        var pending = false;    // true while an update request is pending
        var refreshId = setInterval(function() {
            if (!pending) {     // don't allow multiple pending requests
                pending = true;
                $.getJSON('update', {}, function(data) {    // get updaated values
                    $.each( data, function(key, val) {      // set value and class of each
                        $('#'+key).text(val[1]);
                        $('#'+key).attr('class', val[0]);
                        });
                    pending = false;
                    });
                var tempColor = function(temp) {        // set temp color based on temp value
                    if (temp > 126){
                        var red = 252;
                        var green = 0;
                        var blue = 252;
                        }
                    else if (temp > 105){
                        var red = 252;
                        var green = 0;
                        var blue = (temp-105)*12;
                        }
                    else if (temp > 84){
                        var red = 252;
                        var green = (105-temp)*12;
                        var blue = 0;
                        }
                    else if (temp > 63){
                        var red = (temp-63)*12;
                        var green = 252;
                        var blue = 0;
                        }
                    else if (temp > 42){
                        var red = 0;
                        var green = 252;
                        var blue = (63-temp)*12;
                        }
                    else if (temp > 21){
                        var red = 0;
                        var green = (temp-21)*12;
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

