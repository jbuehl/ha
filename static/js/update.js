    $(document).ready(function() {
        var pending = false;    // true while an update request is pending
        var refreshId = setInterval(function() {
            if (!pending) {     // don't allow multiple pending requests
                pending = true;
                $.getJSON('update', {}, function(data) {    // get updated values
                    $.each( data, function(key, val) {      // set value and class of each
                        $('#'+key).text(val[1]);
                        if (val[0] == 'temp') {
                            $('#'+key).css('color', val[2])
                            }
                        else {
                            $('#'+key).attr('class', val[0]);
                            }
                        });
                    pending = false;
                    });
                };
            }, 1000);
        $.ajaxSetup({cache: false});
        });

