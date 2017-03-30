function addRule(title, body) {
    title = title.trim();
    if (title.length !== 0) {
        $('.sidebar').append('<a href="#'+title+'" class="list-group-item">\
                    '+title+'\
                    <span class="glyphicon glyphicon-check pull-right" id="'+title+'-toggle" aria-hidden="true"></span>\
                </a>');
    }
    $(".rules").append('<a name="'+title+'"></a><div id="'+title+'-panel" class="panel panel-default">\
            <div class="rule panel-heading">\
                <h3 class="panel-title"><input style="font-size: inherit;" value="'+title+'" type="text" class="form-control title"/></h3>\
            </div>\
            <div class="panel-body">\
                <select class="format">\
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
            </div>\
        </div>');

    $('#'+title+'-toggle').click(function () {
        if ($(this).hasClass('glyphicon-unchecked')) {
            $(this).removeClass('glyphicon-unchecked');
            $(this).addClass('glyphicon-check');
        } else {
            $(this).addClass('glyphicon-unchecked');
            $(this).removeClass('glyphicon-check');
        }
        $('#'+title+'-panel').toggle(800);
    });
}

$(document).ready(function () {
    var baseURI = window.location.protocol + "//" + window.location.host + "/";

    window.addEventListener("hashchange", function () {
        window.scrollTo(window.scrollX, window.scrollY - 100);
    });

    $.post(baseURI, {'type': 'rules'}, function (res) {
        var keys = Object.keys(res.data);
        if (keys.length > 0) {
            keys.forEach(key => addRule(key, res.data[key].text));
        } else {
            addRule("", "");
        }
    });

    $(document.body).on('click', ".submit", function () {
        var p = $(this).parent().parent();
        var title = $(p.find('.title')[0]).val();
        var text = $(p.find('.code')[0]).val();
        var data = {
            'type': 'rule',
            'text': text,
            'title': title,
            'flag': $(p.find('.format')[0]).val()
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
            p.remove();
            addRule(title, text);
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
