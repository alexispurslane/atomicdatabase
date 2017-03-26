$(document).ready(function () {
    $(document.body).on('click', ".submit", function () {
        var submit = $($($(this).parent().children()[0]).children()[0]);
        var txtarea = $($(this).parent().children()[1]);
        var n = submit.index($(this));
        var text = txtarea.val();
        console.log(n-1);

        var data = {
            'type': 'rule',
            'text': text,
            'flag': 'sexp'
        }
        $.post(window.location.protocol + "//" + window.location.host + "/", data, function (res) {
            console.log(res);
        });
        submit.remove();
        txtarea.remove();
        $(this).remove();
    });

    $("#new").click(function () {
        $(".container-fluid").first().append('<div class="rule">\
        <h1><input style="font-size: 36px;height:38px;" type="text" class="form-control"/></h1>\
        <textarea cols=80 rows=15 style="font-family: monospace;" class="form-control">Type your rule here!</textarea>\
        <button class="btn btn-success submit" type="button">Update rule</button>\
      </div>');
    });
});
