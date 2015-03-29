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
                var tempColor = function(value) {        // set temp color based on temp value
                    if (value > 130){
                        var red = 255;
                        var green = 0;
                        var blue = 255;
                        }
                    else if (value > 105){
                        var red = 250;
                        var green = 0;
                        var blue = (value-105)*10;
                        }
                    else if (value > 80){
                        var red = 250;
                        var green = (105-value)*10;
                        var blue = 0;
                        }
                    else if (value > 55){
                        var red = (value-55)*10;
                        var green = (value-30)*5;
                        var blue = 0;
                        }
                    else if (value > 30){
                        var red = 0;
                        var green = (value-30)*5;
                        var blue = (55-value)*10;
                        }
                    else{
                        var red = 0;
                        var green = 0;
                        var blue = 255;
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

