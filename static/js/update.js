$(document).ready(function() {
    var blinkers = [];
    var cacheTime = 0;      // timestamp of resource cache
    
    // set color of temp elements based on temp value
    var tempColor = function(tempString){
        temp = parseInt(tempString);
        if      (temp > 120) {red = 252; green = 0; blue = 252;}            // magenta 
        else if (temp > 102) {red = 252; green = 0; blue = (temp-102)*14;}  // red 
        else if (temp > 84)  {red = 252; green = (102-temp)*14; blue = 0;}  // yellow 
        else if (temp > 66)  {red = (temp-66)*14; green = 252; blue = 0;}   // green 
        else if (temp > 48)  {red = 0; green = 252; blue = (66-temp)*14;}   // cyan 
        else if (temp > 30)  {red = 0; green = (temp-30)*14; blue = 252;}   // blue 
        else if (temp > 0)   { red = 0; green = 0; blue = 252;}
        else                 {red = 112; green = 128; blue = 144;}
        return "rgb("+red.toString()+","+green.toString()+","+blue.toString()+")";
        }
        
    // submit a data change
    $(".button").click(function() {
        event.preventDefault();
        resource = this['form']['children']['0']['defaultValue'];
        value = this['defaultValue'];
        $.post('/submit', {"action": value, "resource": resource});
        $.getJSON('/state', {}, function(data) {    // get new state value and update
            updateAll(data);
            });
        return false;
        });
        
    // update the attributes of one data item
    var update = function(key, val) {
        $('#'+key).text(val[1]);                // set the value
//        $('#'+key).attr('value', val[1]);     // set the button value
        if (val[0] == 'temp') {                 // set the color of a temp item
            $('.'+key).css('color', tempColor(val[1]));
            }
        else {                                  // change the class
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
        
    var pending = false;    // true while an stateChange request is pending
    var count = 0;
    var blinkToggle = false;
    var blinkOpacity = 1.0;
    // main loop
    var refreshId = setInterval(function() {
        if (count == 60) {     // update everything every minute
            $.getJSON('/state', {}, function(data) {    // get state values
                updateAll(data);
                count = 0;
                });
            };
        if (!pending) {     // don't allow multiple pending stateChange requests
            pending = true;
            $.getJSON('/stateChange', {}, function(data) {    // get changed state values
                updateAll(data);
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

