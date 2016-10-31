$(document).ready(function() {
    var blinkers = [];
    var cacheTime = 0;      // timestamp of resource cache
    var update = function(data) {
        blinkers = data["blinkers"];
        if (data["cacheTime"] > cacheTime) {        // has the resource cache been updated ?
            location.reload(true);                  // reload the page
            }
        else {
            $.each(data, function(key, val) {       // set value and class of each item
                $('#'+key).text(val[1]);            // set the value
                $('#'+key).attr('value', val[1]);   // set the button value
                if (val[0] == 'temp') {             // set the color of a temp item
                    $('#'+key).css('color', val[2])
                    }
                else {                              // change the class
                    $('#'+key).attr('class', val[0]);
                    }
                });
            };
        }
    var pending = false;    // true while an stateChange request is pending
    var count = 0;
    var refreshId = setInterval(function() {
        if (count == 60) {     // every minute
            $.getJSON('/state', {}, function(data) {    // get state values
                update(data);
                count = 0;
                });
            };
        if (!pending) {     // don't allow multiple pending requests
            pending = true;
            $.getJSON('/stateChange', {}, function(data) {    // get changed state values
                update(data);
                pending = false;
                });
            };
        $.each(blinkers, function(key, val) {
            $('#'+val).toggle($("body").css("background-color"));     // blink the value
        });
        count = count + 1;
        }, 1000);
    $.ajaxSetup({cache: false});
    $.getJSON('/state', {}, function(data) {    // get initial state values
        cacheTime = data["cacheTime"];
        update(data);
        });
    });

