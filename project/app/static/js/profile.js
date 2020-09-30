setInterval(function(){ 
    console.log('interval reached');
    $('#retrieve_stock_data').submit();
}, 5000);
$(document).on('submit', '#retrieve_stock_data', function() {
    $.ajax({
        type: $(this).attr('method'),
        url: $(this).attr('action'),
        data: $(this).serialize(),
        success: function (data) {
            $('#table_body').html(data);
        },
        error: function(data) {
            console.log("something went wrong");
        }
    });
    return false;
});
