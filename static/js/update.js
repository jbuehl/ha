    $(document).ready(function() {
        var pending = false;
        var refreshId = setInterval(function() {
            if (!pending) {
                pending = true;
                $.getJSON('update', {}, function(data) {
                    $.each( data, function(key, val) {
                        $('#'+key).text(val[1]);
                        $('#'+key).attr('class', val[0]);
                        });
                    pending = false;
                    });
                };
            }, 1000);
        $.ajaxSetup({cache: false});
        });

