// TODO:
// Handle out of bound values (doesn't cause exceptions but still doesn't look good)
// Tabbing goes to the next (and wraps around)
// Enter = focusout
// Reduce verbosity

var input = "<input type=\"text\" readonly=\"true\" class=\"field form-control disabled\"></input>";
var fieldSlot = "<td> " + input + " </td>";

$(document).ready(function () {
	var $status = $("#status");

	var s = "<thead> <tr id=\"a\"> "
	for (var i = 0; i < 5; i++) {
		s += "<td> <input type=\"text\" readonly=\"true\" class=\"form-control disabled\"></input> </td>";
	}
	s += "</tr> </thead>";
	$("table").prepend(s);
	$("input").first().prop("disabled", true);
	$("input").first().prop("readonly", false);

	s = "<tr> "
	for (var i = 0; i < 5; i++) {
		s += fieldSlot;
	}
	s += "</tr>";
	for (var i = 0; i < 4; i++)
		$("tbody").append(s);

	$(document.body).on('focusout', "input:not(.query)", function () {
		$(this).addClass("disabled"); 
		$(this).prop("readonly", true);
		if (!$(this).hasClass("field")) {
			return;
		}
		// if ($(this).parent().parent().attr('id') === "a") {
		// 	return;
		// }
		var colint = $(this).parent().index();
		if (colint == 0) return;
		var rowVal = $(this).parent().parent().children().first().children().first().val();
		// console.log(rowVal);
		var colVal = $("#a").children().slice(colint, colint+1).children().first().val();
		// console.log(colVal);
		var data = {
			'type': 'table',
			'text': $(this).val(),
			'tableUpdate': {
				'row': rowVal,
				'col': colVal,
				'value': $(this).val()
			}
		};
		$.post(document.baseURI, data, function(data) {
			console.log(data);
		})
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

		$("tbody").append(str);
		$status.text("Row added.");
	});

	$("#del-row").click(function () {
		if ($("tr").length < 2) {
			$status.text("ERROR: Cannot delete only row.");
			return;
		}
		if (confirm("Are you sure you want to delete a row?")) {
			var row = +prompt("Delete which row?");
			if (row < 1) {
				$status.text("ERROR: Cannot delete Row 1.");
				return;
			}
			var delRow = $("tr")[row];
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
						'value': $(this).children().first().val()
					}
				};
				$.post(document.baseURI, data, function(data) {
					console.log(data);
				});
			});
			$(delRow).remove();
			$status.text("Row " + row + " deleted.");
		}
	});

	$("#add-col").click(function () {
		$("tr").append(fieldSlot);
		$status.text("Column added.");
	});

	$("#del-col").click(function () {
		if ($("td").length / $("tr").length < 2) {
			$status.text("ERROR: Cannot delete only column.");
			return;
		}
		if (confirm("Are you sure you want to delete a column?")) {
			var col = +prompt("Delete which column?");
			if (col < 1) {
				$status.text("ERROR: Cannot delete Column 1.");
				return;
			}
			$("tr").each(function () {
				if ($(this).prop("id") === "a") {
					return;
				}
				var delCol = $(this).children()[col];
				var rowVal = $(delCol).parent().children().first().children().first().val();
				// console.log(rowVal);
				var colVal = $($("#a").children()[col]).children().first().val();
				// console.log(colVal);
				console.log([colVal, rowVal, $(delCol).children().first().val()]);
				var data = {
					'type': 'delete-col',
					'text': $(delCol).children().first().val(),
					'tableUpdate': {
						'col': colVal,
						'value': $(delCol).children().first().val()
					}
				};
				$.post(document.baseURI, data, function(data) {
					console.log(data);
				});
				$(this).children()[col].remove();
			});
			$("#a").children()[col].remove();
			$status.text("Column " + col + " deleted.");
		}
	});

	$("#solve").click(function () {
		var data = {
			'type': 'query',
			'text': $(".query").first().val()
		}
		var answer = $.post(document.baseURI, data, function(data) {
			console.log(data);
		})

	});
});
