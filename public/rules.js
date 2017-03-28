function addRule(title, body) {
    $(".rules").append('<div class="rule list-group-item">\
        <h4 class="list-group-item-heading"><input style="font-size: inherit;" value="'+title+'" type="text" class="form-control"/></h1>\
        <select>\
            <option value="natural">Natural Language</option>\
            <option value="sexp">S-Expressions (pro)</option>\
        </select>\
        <textarea rows=15 class="form-control code">'+body+'</textarea>\
        <button class="btn btn-success submit toolbar" type="button">\
            <span class="glyphicon glyphicon-ok" aria-hidden="true"></span>\
        </button>\
        <button class="btn btn-danger delete toolbar" type="button">\
            <span class="glyphicon glyphicon-remove" aria-hidden="true"></span>\
        </button>\
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
            'flag': $($(this).parent().children()[1]).val()
        };
        $.post(baseURI, data, function (res) {
            console.log(res);
            // clear other alert types
            $("#status > .alert").removeClass(function (index, className) {
                return (className.match (/(^|\s)alert-\S+/g) || []).join(' ');
            });
            if (res.success) {
                $("#status > .alert").addClass('alert-success');
                $("#status > .alert").html("<strong>Success!</strong> Your rule has been understood.");
            } else {
                $("#status > .alert").addClass('alert-danger');
                $("#status > .alert").html("<strong>An error occured: </strong> Your rule could not be parsed.");
            }
        });
    });

    $(document.body).on('click', ".delete", function () {
        var data = {
            'type': 'delete-rule',
            'title': $($($(this).parent().children()[0]).children()[0]).val()
        };

        $.post(baseURI, data, function (res) {
            console.log(res);
            $("#status > .alert").removeClass(function (index, className) {
                return (className.match (/(^|\s)alert-\S+/g) || []).join(' ');
            });
            if (res.success) {
                $("#status > .alert").addClass('alert-warning');
                $("#status > .alert").html("<strong>Success!</strong> Your rule has been deleted.");
            } else {
                $("#status > .alert").addClass('alert-danger');
                $("#status > .alert").html("<strong>An error occured: </strong> Your rule could not be found.");
            }
        });
    });

    $("#new").click(function () {
        addRule("", "");
    });
});
