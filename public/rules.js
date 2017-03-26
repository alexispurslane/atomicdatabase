$(document).ready(function () {
    var baseURI = window.location.protocol + "//" + window.location.host + "/";

    $.post(baseURI, {'type': 'rules'}, function (res) {
        var keys = Object.keys(res.data);
        if (keys.length > 0) {
            keys.forEach(key => {
                $(".rules").append('<div class="rule">\
        <h1><input style="font-size: 36px;height:38px;" value="'+key+'" type="text" class="form-control"/></h1>\
        <textarea cols=80 rows=15 style="font-family: monospace;" class="form-control">'+res.data[key].text+'</textarea>\
        <button class="btn btn-success submit" type="button">Update rule</button>\
      </div>');
            });
        } else {
            $(".rules").append('<div class="rule">\
        <h1><input style="font-size: 36px;height:38px;" type="text" class="form-control"/></h1>\
        <textarea cols=80 rows=15 style="font-family: monospace;" class="form-control">Type your rule here!</textarea>\
        <button class="btn btn-success submit" type="button">Update rule</button>\
      </div>');
        }
    });

    $(document.body).on('click', ".submit", function () {
        var submit = $($($(this).parent().children()[0]).children()[0]);
        var txtarea = $($(this).parent().children()[1]);
        var tt = $($($(this).parent().children()[0]).children()[0]);;
        var n = submit.index($(this));
        var text = txtarea.val();
        var title = tt.val();

        var data = {
            'type': 'rule',
            'text': text,
            'title': title,
            'flag': 'sexp'
        }
        $.post(baseURI, data, function (res) {
            console.log(res);
        });
    });

    $("#new").click(function () {
        $(".rules").append('<div class="rule">\
        <h1><input style="font-size: 36px;height:38px;" type="text" class="form-control"/></h1>\
        <textarea cols=80 rows=15 style="font-family: monospace;" class="form-control">Type your rule here!</textarea>\
        <button class="btn btn-success submit" type="button">Update rule</button>\
      </div>');
    });
});
