// TODO:
// Tabbing goes to the next (and wraps around)
// Enter = focusout
// Reduce verbosity

var input = "<input type=\"text\" readonly=\"true\" class=\"field form-control disabled\"></input>";
var fieldSlot = "<td> " + input + " </td>";
var baseURI = window.location.protocol + "//" + window.location.host + "/";
var tips = [
    'Columns are attributes, rows are entities, and cells are values.',
    'Queries are just regular, natural language questions! No sweat.',
    'Use rules to tell atomicdatabase what things are.',
    'Use s-expressions in rules for a more concise experience.',
    'Rules can be natural language too!'
];

var BreakException = {};

$(document).ready(function () {
    var $status = $("#status");
    updateStatus(tips[Math.floor(Math.random()*tips.length)], false, true);
    function updateStatus(t, error, tip) {
        if (error) {
            $status.html('<div class="alert alert-danger" role="alert"><strong>Error:</strong> '+t+'</div>');
            $status.hide().slideDown({
                top: 45
            }, 4000);
        } else if (tip) {
            $status.html('<div class="alert alert-success" role="alert"><strong>Tip: </strong> '+t+'</div>');
            $status.hide().slideDown({
                top: 45
            }, 4000);
        } else {
            $status.html('<div class="alert alert-success" role="alert"><strong>Success!</strong> '+t+'</div>');
            $status.hide().slideDown({
                top: 45
            }, 4000);
        }
    }

    var s = "<thead class='facts'> <tr id=\"a\"> ";
    for (var i = 0; i < 5; i++) {
        s += "<td> <input type=\"text\" readonly=\"true\" class=\"form-control disabled\"></input> </td>";
    }
    s += "</tr> </thead>";
    $("table").first().prepend(s);
    $($("input").get(1)).prop("disabled", true);
    $($("input").get(1)).prop("readonly", false);

    s = "<tr> ";
    for (var i = 0; i < 5; i++) {
        s += fieldSlot;
    }
    s += "</tr>";
    for (var i = 0; i < 4; i++)
        $("tbody.facts").append(s);

    // On each reload: Load data
    var reloadRequest = {
        'type': 'reload'
    };
    $.post(baseURI, reloadRequest, function (data) {
        var actualData = data.data;
        var attrOrder = Object.entries(actualData.attrOrder);
        var entityOrder = Object.entries(actualData.entityOrder);

        var database = actualData.database;
        if (attrOrder.length === 0 || entityOrder.length === 0 || database.length === 0) return;
        var numColsToAdd = attrOrder.length - 4;
        if (numColsToAdd > 0)
            for (var i = 0; i < numColsToAdd; i++) {
                addCol();
            }
        else if (numColsToAdd < 0)
            for (var i = 0; i > numColsToAdd; i--) {
                delColBypass();
            }
        var numRowsToAdd = entityOrder.length - 4;
        if (numRowsToAdd > 0)
            for (var i = 0; i < numRowsToAdd; i++) {
                addRow();
            }
        else if (numRowsToAdd < 0)
            for (var i = 0; i > numRowsToAdd; i--) {
                delRowBypass();
            }
        // console.log(attrOrder);
        $("#a").children().each(function () {
            var item = $(this);
            var index = item.index();
            if (index === 0) return;

            attrOrder.forEach(function (e) {
                if (+e[1] === index) {
                    item.children().first().val(e[0]);
                }
            });
        });
        $("tbody.facts").children().each(function () {
            var item = $(this).children().first();
            var index = $(this).index();

            entityOrder.forEach(function (e) {
                if (+e[1] === index) {
                    if (e[0].toString() === "[object Object]") {
                        delRowBypass();
                        return;
                    }
                    item.children().first().val(e[0]);
                }
            });
        });
        console.log(entityOrder);
        console.log(database);
        $("tbody.facts").children().each(function () {
            var row = $(this);
            database.forEach(function (e) {
                console.log(row.children().first().children().first().val());
                if (row.children().first().children().first().val() === e[1]) {
                    row.children().each(function () {
                        var item = $(this);
                        var index = item.index();
                        // if (index === 0) return;
                        if (e[0] === $($("#a").children()[index]).children().first().val()) {
                            item.children().first().val(e[2]);
                            return;
                        }
                    });
                }
            });
        });
    });

    $(document.body).on('focusout', "input:not(.query)", function () {
        $(this).addClass("disabled");
        $(this).prop("readonly", true);
        if (!$(this).hasClass("field")) {
            return;
        }
        // if ($(this).parent().parent().attr('id') === "a") {
        //  return;
        // }
        var colint = $(this).parent().index();
        if (colint == 0) return;
        var rowint = $(this).parent().parent().index();
        var rowVal = $(this).parent().parent().children().first().children().first().val();
        // console.log(rowVal);
        var colVal = $("#a").children().slice(colint, colint+1).children().first().val();
        // console.log(colVal);
        var data = {
            'type': 'table',
            'text': $(this).val(),
            'tableUpdate': {
                'row': {"index": rowint, "value": rowVal},
                'col': {"index": colint, "value": colVal},
                'value': $(this).val()
            }
        };
        $.post(baseURI, data, function(data) {
            if (!data.success) {
                updateStatus(data.data, true);
            }
        });
    });

    $(document.body).on('dblclick', ".disabled", function () {
        $(this).removeClass("disabled");
        $(this).prop("readonly", false);
    });

    var addRow = function () {
        var cols = $("td").length / $(".facts > tr").length;

        var str = "<tr> ";
        for (var i = 0; i < cols; i++) {
            str += fieldSlot;
        }
        str += "</tr>";

        $("tbody.facts").append(str);
        updateStatus("Row added.");
    };

    $("#add-row").click(addRow);

    var delRowBypass = function () {
        if ($(".facts > tr").length < 2) return;
        $(".facts > tr").last().remove();
    };

    var delRow = function () {
        if ($(".facts > tr").length < 2) {
            updateStatus("Cannot delete only row.", true);
            return;
        }
        if (confirm("Are you sure you want to delete a row?")) {
            var row = +prompt("Delete which row?");
            if (row < 1) {
                updateStatus("Cannot delete Row 1.", true);
                return;
            }
            var delRow = $(".facts > tr")[row];
            $(delRow).children().each(function () {
                var colint = $(this).index();
                if (colint == 0) return;
                var colint = $(this).index();
                var rowVal = $(this).parent().children().first().children().first().val();
                // console.log(rowVal);
                var colVal = $("#a").children().slice(colint, colint+1).children().first().val();
                // console.log(colVal);
                console.log([colVal, rowVal, $(this).children().first().val()]);
                var data = {
                    'type': 'delete-row',
                    'text': $(this).children().first().val(),
                    'tableUpdate': {
                        'row': rowVal,
                        'col': colVal,
                        'value': $(this).children().first().val()
                    }
                };
                $.post(baseURI, data, function(data) {
                    console.log(data);
                });
            });
            $(delRow).remove();
            updateStatus("Row " + row + " deleted.");
        }
    }

    $("#del-row").click(delRow);

    var addCol = function () {
        $(".facts > tr").append(fieldSlot);
        updateStatus("Column added.");
    }

    $("#add-col").click(addCol);

    var delColBypass = function () {
        if ($("td").length / $("tr").length < 2) return;
        $(".facts > tr").each(function () {
            $(this).children().last().remove();
        });
    }

    var delCol = function () {
        if ($("td").length / $(".facts > tr").length < 2) {
            updateStatus("Cannot delete only column.", true);
            return;
        }
        if (confirm("Are you sure you want to delete a column?")) {
            var col = +prompt("Delete which column?");
            if (col < 1) {
                updateStatus("Cannot delete Column 1.", true);
                return;
            }
            $(".facts > tr").each(function () {
                if ($(this).prop("id") === "a") {
                    return;
                }
                var delCol = $(this).children()[col];
                var rowint = $(this).parent().index();
                var rowVal = $(delCol).parent().children().first().children().first().val();
                // console.log(rowVal);
                var colVal = $($("#a").children()[col]).children().first().val();
                // console.log(colVal);
                console.log([colVal, rowVal, $(delCol).children().first().val()]);
                var data = {
                    'type': 'delete-col',
                    'text': $(delCol).children().first().val(),
                    'tableUpdate': {
                        'row': rowVal,
                        'col': colVal,
                        'value': $(delCol).children().first().val()
                    }
                };
                $.post(baseURI, data, function(data) {
                    console.log(data);
                });
                $(this).children()[col].remove();
            });
            $("#a").children()[col].remove();
            updateStatus("Column " + col + " deleted.");
        }
    };

    $("#del-col").click(delCol);

    $('.query').first().keydown(function(event){
        if(event.keyCode==13){
            $('#solve').trigger('click');
        }
    });
    $("#solve").click(function () {
        var data = {
            'type': 'query',
            'text': $(".query").first().val()
        };
        $.post(baseURI, data, function(data) {
            console.log(data);
            if (data.success) {
                if (data.data.length > 0) {
                    var str = Object.values(data.data[0]).join(", ");
                    $status.html("Possible answers are: " + str);

                    $("#properties").html("");
                    $("#values").html("");
                    Object.keys(data.data[0]).forEach((k) => {
                        $("#properties").append("<td><strong>" + k + "</strong></td>");
                        $("#values").append("<td>" + data.data[0][k] + "</td>");
                    });
                } else {
                    $status.html(
                        ' <strong>No data satisfied this query.</strong>\
 Either I need more data or one of your rules was incorrect, or it was contradictory.', true);
                }
            } else {
                $status.html(
                    "I didn\'t understand that.");
            }
        });
    });
});
