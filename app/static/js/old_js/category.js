<script type="text/javascript">
	$(document).ready(function() {
    var counter = 1;

    $("#addrow").on("click", function () {
        counter++;

        var newRow = $("<tr>");
        var cols = "";
	    cols += '<td> <input id="catname" name="catname" type="text" value=""/></td>';
	    cols += '<td> <input id="description" name="description" type="text" value=""></td>';
	    cols += '<td><a class="deleteRow"> X </a></td>';
        newRow.append(cols);

        $("table.order-list").append(newRow);
    });

    $("table.order-list").on("change", 'input[name^="weight"], input[name^="price"]', function (event) {
        calculateRow($(this).closest("tr"));
        calculateGrandTotal();
    });

    $("table.order-list").on("click", "a.deleteRow", function (event) {
        $(this).closest("tr").remove();
        calculateGrandTotal();
    });
});

function calculateRow(row) {
    var price = +row.find('input[name^="price"]').val();
    var weight = +row.find('input[name^="weight"]').val();
    row.find('input[name^="gst"]').val((price * weight).toFixed(2));
}

function calculateGrandTotal() {
    var grandTotal = 0;
    $("table.order-list").find('input[name^="linetotal"]').each(function () {
        grandTotal += +$(this).val();
    });
    $("#grandtotal").text(grandTotal.toFixed(2));
}
</script>
