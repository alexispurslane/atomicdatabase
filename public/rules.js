$(document).ready(function () {
    $(".submit").click(function () {
        var n = $(".submit").index($(this));
        var text = $("textarea").get(n-1).value;
        console.log(n-1);

        var data = {
            'type': 'rule',
            'text': text,
            'flag': 'sexp'
        }
        $.post(window.location.protocol + "//" + window.location.host + "/", data,
               function (res) {
                   console.log(res);
               });
    });

    $("#new").click(function () {
        $(".container-fluid").first().append('<div class="rule">\
        <h1><input style="font-size: 36px;height:38px;" type="text" class="form-control"/></h1>\
        <textarea cols=80 rows=15 style="font-family: monospace;" class="form-control">Type your rule here!</textarea>\
        <button class="btn btn-success submit" type="button">Update rule</button>\
      </div>');
    });
});
