    $(document).ready(function() {
        $(".button").click(function() {
            event.preventDefault();
            $.post('/submit', {"action": this['defaultValue'], "resource": this['form']['children']['0']['defaultValue']});
            return false;
            });
        });

