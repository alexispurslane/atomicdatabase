var input = "<input type=\"text\" readonly=\"true\" class=\"form-control disabled\"></input>";
var fieldSlot = "<td> " + input + " </td>";

$(document).ready(function () {
	var s = "<tr id=\"a\"> "
	for (var i = 0; i < 5; i++) {
		s += fieldSlot;
	}
	s += "</tr>"

	$("#tbl").html(s);

	$("input").on('focusout', function () {
		$(this).addClass("disabled"); 
		$(this).prop("readonly", true);
	});

	$(".disabled").on('dblclick', function () {
		$(this).removeClass("disabled");
		$(this).prop("readonly", false);
	});

	$("#add-row").click(function () {
		var cols = $("td").length / $("tr").length;
		console.log("Register click");

		var str = "<tr> "
		for (var i = 0; i < cols; i++) {
			str += fieldSlot;
		}
		str += "</tr>"

		$("tr:last").after(str);
	});

	$("#del-row").click(function () {
		if ($("tr").length < 2) {
			alert("ERROR: Cannot delete last row.");
			return;
		}
		if (confirm("Are you sure you want to delete this row?")) {
			var row = prompt("Delete which row?")-1;
			$("tr").get(row).remove();
		}
	});
});

function addRow() {
	var s = "";

}

function addColumn() {

}
