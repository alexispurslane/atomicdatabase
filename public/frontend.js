// TODO:
// Handle out of bound values (doesn't cause exceptions but still doesn't look good)

var input = "<input type=\"text\" readonly=\"true\" class=\"form-control disabled\"></input>";
var fieldSlot = "<td> " + input + " </td>";

$(document).ready(function () {
    var s = "<tr id=\"a\"> "
    for (var i = 0; i < 5; i++) {
        s += fieldSlot;
    }
    s += "</tr>"

    $("#tbl").html(s);

    $(document.body).on('focusout', "input", function () {
        $(this).addClass("disabled");
        $(this).prop("readonly", true);
    });

    $(document.body).on('dblclick', ".disabled", function () {
        $(this).removeClass("disabled");
        $(this).prop("readonly", false);
    });

    $("#add-row").click(function () {
        var cols = $("td").length / $("tr").length;

        var str = "<tr> "
        for (var i = 0; i < cols; i++) {
            str += fieldSlot;
        }
        str += "</tr>"

        $("tr:last").after(str);
    });

    $("#del-row").click(function () {
        if ($("tr").length < 2) {
            $("#status").html("ERROR: Cannot delete only row.");
            return;
        }
        if (confirm("Are you sure you want to delete a row?")) {
            var row = prompt("Delete which row?")-1;
            $("tr").get(row).remove();
            $("#status").html("Row " + (row+1) + " deleted.");
        }
    });

    $("#add-col").click(function () {
        $("tr").append(fieldSlot);
    });

    $("#del-col").click(function () {
        if ($("td").length / $("tr").length < 2) {
            $("#status").html("ERROR: Cannot delete only column.");
            return;
        }
        if (confirm("Are you sure you want to delete a column?")) {
            var col = prompt("Delete which column?")-1;
            $("tr").each(function () {
                $(this).children().slice(col, col+1).remove();
            });
            $("#status").html("Row " + (col+1) + " deleted.");
        }
    });
});
