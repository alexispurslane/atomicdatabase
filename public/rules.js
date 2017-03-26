function addRule(title, body) {
    $(".rules").append('<div class="rule list-group-item">\
        <h4 class="list-group-item-heading"><input style="font-size: inherit;" value="'+title+'" type="text" class="form-control"/></h1>\
        <select>\
            <option value="natural">Natural Language</option>\
            <option value="sexp">S-Expressions (pro)</option>\
        </select>\
        <textarea rows=15 style="resize: vertical;font-family: monospace;" class="form-control">'+body+'</textarea>\
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
        var data = {
            'type': 'rule',
            'text': $($(this).parent().children()[2]).val(),
            'title': $($($(this).parent().children()[0]).children()[0]).val(),
            'flag': $($(".submit").parent().children()[1]).val()
        };
        $.post(baseURI, data, function (res) { console.log(res); });
    });

    $("#new").click(function () {
        addRule("", "");
    });
});
