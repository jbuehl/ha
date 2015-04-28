$(document).ready(function() {
    var update = function(data) {
        $.each(data, function(key, val) {      // set value and class of each item
            $('#'+key).text(val[1]);
            if (val[0] == 'temp') {
                $('#'+key).css('color', val[2])
                }
            else {
                $('#'+key).attr('class', val[0]);
                }
            });
        }
    $.getJSON('state', {}, function(data) {    // get state values
        update(data);
        });
    var pending = false;    // true while an update request is pending
    var count = 0;
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
    });

