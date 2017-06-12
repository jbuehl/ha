$(document).ready(function() {
    var blinkers = [];
    var cacheTime = 0;      // timestamp of resource cache
    var changedResource = '';
    // set temp color based on temp value
    var tempColor = function(tempString){
        temp = parseInt(tempString);
        if (temp > 120) {       // magenta
            red = 252;
            green = 0;
            blue = 252;
            }
        else if (temp > 102) {  // red
            red = 252;
            green = 0;
            blue = (temp-102)*14;
            }
        else if (temp > 84) {   // yellow
            red = 252;
            green = (102-temp)*14;
            blue = 0;
            }
        else if (temp > 66) {   // green
            red = (temp-66)*14;
            green = 252;
            blue = 0;
            }
        else if (temp > 48) {   // cyan
            red = 0;
            green = 252;
            blue = (66-temp)*14;
            }
        else if (temp > 30) {   // blue
            red = 0;
            green = (temp-30)*14;
            blue = 252;
            }
        else if (temp > 0) {
            red = 0;
            green = 0;;
            blue = 252
            }
        else {
            red = 112;
            green = 128;
            blue = 144;
            }
        return "rgb("+red.toString()+","+green.toString()+","+blue.toString()+")";
        }
    // submit a data change
    $(".button").click(function() {
        event.preventDefault();
        changedResource = this['form']['children']['0']['defaultValue'];
        $.post('/submit', {"action": this['defaultValue'], "resource": changedResource});
        return false;
        });
    // update the attributes of one data item
    var update = function(key, val) {
        $('#'+key).text(val[1]);            // set the value
        $('#'+key).attr('value', val[1]);   // set the button value
        if (val[0] == 'temp') {             // set the color of a temp item
            $('#'+key).css('color', tempColor(val[1]))
            }
        else {                              // change the class
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
            if (changedResource != '') {
                update(changedResource, data[changedResource]);
                changedResource = '';
                }
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
        if (count == 60) {     // every minute
            $.getJSON('/state', {}, function(data) {    // get state values
                updateAll(data);
                count = 0;
                });
            };
        if (!pending) {     // don't allow multiple pending requests
            pending = true;
            $.getJSON('/stateChange', {}, function(data) {    // get changed state values
                updateAll(data);
                pending = false;
                });
            };
        if (blinkToggle) {
            blinkOpacity = 1.0;
            blinkToggle = false;
            }
        else {
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

