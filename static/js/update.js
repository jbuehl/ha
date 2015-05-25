$(document).ready(function() {
    var pending = false;    // true while an update request is pending
    var count = 0;
    var cacheTime = 0;      // timestamp of resource cache
    var update = function(data) {
        if (data["cacheTime"] > cacheTime) {        // has the resource cache been updated ?
            location.reload(true);                  // reload the page
            }
        else {
            $.each(data, function(key, val) {       // set value and class of each item
                $('#'+key).text(val[1]);            // set the value
                if (val[0] == 'temp') {             // set the color of a temp item
                    $('#'+key).css('color', val[2])
                    }
                else {                              // change the class
                    $('#'+key).attr('class', val[0]);
                    }
                });
            };
        }
    var refreshId = setInterval(function() {
        if (count == 60) {     // every minute
            $.getJSON('state', {}, function(data) {    // get state values
                update(data);
                count = 0;
                });
            };
        if (!pending) {     // don't allow multiple pending requests
            pending = true;
            $.getJSON('stateChange', {}, function(data) {    // get updated state values
                update(data);
                pending = false;
                });
            };
        count = count + 1;
        }, 1000);
    $.ajaxSetup({cache: false});
    $.getJSON('state', {}, function(data) {    // get state values
        cacheTime = data["cacheTime"];
        update(data);
        });
    });

