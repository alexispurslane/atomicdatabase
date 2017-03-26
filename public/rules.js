function addRule(title, body) {
    $(".rules").append('<div class="rule list-group-item">\
        <h4 class="list-group-item-heading"><input style="font-size: inherit;" value="'+title+'" type="text" class="form-control"/></h1>\
        <textarea cols=80 rows=15 style="font-family: monospace;" class="form-control">'+body+'</textarea>\
        <button class="btn btn-success submit" type="button" style="width: 100%;"><span class="glyphicon glyphicon-ok" aria-hidden="true"></span></button>\
      </div>');
}

$(document).ready(function () {
    var baseURI = window.location.protocol + "//" + window.location.host + "/";

    $.post(baseURI, {'type': 'rules'}, function (res) {
        var keys = Object.keys(res.data);
        if (keys.length > 0) {
            keys.forEach(key => addRule(key, res.data[key].text));
        } else {
            addRule("", "");
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
        addRule("", "");
    });
});
