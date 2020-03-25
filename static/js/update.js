$(document).ready(function() {
    var blinkers = [];
    var cacheTime = 0;      // timestamp of resource cache
    var soundPlaying = 0;

    // set color of temp elements based on temp value
    var tempColor = function(temp, min, max){
        maxcolor = 254;
        span = max - min;
        step = Math.floor(span / 5);
        incr = Math.floor(maxcolor / step);
        step1 = min + step;
        step2 = step1 + step;
        step3 = step2 + step;
        step4 = step3 + step;
        if      (temp > max) {red = maxcolor; green = 0; blue = maxcolor;}             // magenta
        else if (temp > step4) {red = maxcolor; green = 0; blue = (temp-step4)*incr;}  // red
        else if (temp > step3)  {red = maxcolor; green = (step4-temp)*incr; blue = 0;} // yellow
        else if (temp > step2)  {red = (temp-step2)*incr; green = maxcolor; blue = 0;} // green
        else if (temp > step1)  {red = 0; green = maxcolor; blue = (step2-temp)*incr;} // cyan
        else if (temp > min)  {red = 0; green = (temp-min)*incr; blue = maxcolor;}     // blue
        else if (temp > 0)   {red = 0; green = 0; blue = maxcolor;}
        else                 {red = 112; green = 128; blue = 144;}
        return "rgb("+red.toString()+","+green.toString()+","+blue.toString()+")";
        }

    // set color of a battery charge
    var chargeColor = function(charge, okLevel, cautionLevel){
        if      (charge > okLevel) {color = "LawnGreen";}
        else if (charge > cautionLevel) {color = "Gold";}
        else                 {color = "OrangeRed";}
        return color;
        }

    // submit a data change
    $(".button").click(function() {
        event.preventDefault();
        resource = this['form']['children']['0']['value'];
        value = this['value'];
        if (value == 'Set') {
            value = this['form']['1']['value'];
        }
        $.post('/submit', {"action": value, "resource": resource});
        $.getJSON('/state', {}, function(data) {    // get new state value and update
            updateAll(data);
            });
        return false;
        });

    // update the attributes of one data item
    var update = function(key, val) {
//        $('#'+key).attr('value', val[1]);     // set the button value
        if (val[0] == 'temp') {                 // set the color of a temp item
            $('#'+key).text(val[1]);            // set the value
            $('#'+key).css('color', tempColor(parseInt(val[1]), 30, 120));
            }
        else if (val[0] == 'panel') {           // set the color of a solar panel
            $('#'+key).text(val[1]);            // set the value
            $('#'+key+"_panel").css('background', tempColor(parseInt(val[1]), 0, 260));
            }
        else if (val[0] == 'battery') {          // set the color of a battery charge
            $('#'+key).text(val[1]);            // set the value
            $('#'+key).css('color', chargeColor(parseInt(val[1]), 30, 10));
            }
        else if (val[0] == 'sound') {           // play a sound if one is specified
            if (val[1] == 'On') {
                if (!soundPlaying) {            // only play the sound once when transitioning to On
                    soundPlaying = 1;
                    var audio = new Audio('/sound/' + val[1]);
                    audio.play();
                    }
                }
            else {
                soundPlaying = 0;
                }
            }
        else if (val[0] == 'select') {
            $('#'+key).text(val[1]);
            // $('#'+key+'_select').prop('value', val[1]);
            $('#'+key+'_select').removeAttr('selected')
            $('#'+key+'_select'+' option[value="'+val[1]+'"]').prop({defaultSelected: true});
            }
        else {                                  // change the class
            $('#'+key).text(val[1]);            // set the value
            $('#'+key).attr('class', val[0]);
            };
        }

    // update the attributes of all the data items
    var updateAll = function(data) {
        blinkers = data["blinkers"];
        if (data["cacheTime"] > cacheTime) {        // has the resource cache been updated ?
            location.reload(true);                  // reload the page
            }
        else {
            $.each(data, function(key, val) {
                update(key, val);
                });
            };
        }

    var pending = false;    // true while a stateChange request is pending
    var count = 0;          // loop counter
    var blinkToggle = false;
    var blinkOpacity = 1.0;
    // main loop once per second
    var refreshId = setInterval(function() {
        if (count >= 60) {     // update everything every minute
            count = 0;
            if (getStateChange) {
                getStateChange.abort(); // abort the pending getStateChange
                };
            pending = false;
            var getState = $.getJSON('/state', {}, function(data) {    // get state values
                updateAll(data);
                })
                .fail(function() {
                    count = 0;
                    pending = false;
                    });
            };
        if (!pending) {     // don't allow multiple pending stateChange requests
            pending = true;
            var getStateChange = $.getJSON('/stateChange', {}, function(data) {    // get changed state values
                updateAll(data);
                pending = false;
                })
                .fail(function() {
                    count = 0;
                    pending = false;
                    });
            };
        if (blinkToggle) {      // blink bright
            blinkOpacity = 1.0;
            blinkToggle = false;
            }
        else {                  // blink dim
            blinkOpacity = 0.5;
            blinkToggle = true;
            };
        $.each(blinkers, function(key, val) {
            $('#'+val).css("opacity", blinkOpacity);     // blink the value
        });
        count = count + 1;
        }, 1000);
    $.ajaxSetup({cache: false});
    $.getJSON('/state', {}, function(data) {    // get initial state values
        cacheTime = data["cacheTime"];
        updateAll(data);
        });
    });
