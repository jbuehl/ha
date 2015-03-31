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
                    if (temp > 145){
                        var red = 250;
                        var green = 0;
                        var blue = 250;
                        }
                    else if (temp > 120){
                        var red = 250;
                        var green = 0;
                        var blue = (temp-120)*10;
                        }
                    else if (temp > 95){
                        var red = 250;
                        var green = (120-temp)*10;
                        var blue = 0;
                        }
                    else if (temp > 70){
                        var red = (temp-70)*10;
                        var green = 250;
                        var blue = 0;
                        }
                    else if (temp > 45){
                        var red = 0;
                        var green = 250;
                        var blue = (70-temp)*10;
                        }
                    else if (temp > 20){
                        var red = 0;
                        var green = (temp-20)*10;
                        var blue = 250;
                        }
                    else{
                        var red = 0;
                        var green = 0;
                        var blue = 250;
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

