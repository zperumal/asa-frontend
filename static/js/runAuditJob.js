/**
 * Created by zaraperumal on 9/10/16.
 */
function hideDiv() {
    document.getElementById('uploadDiv').style.display = "none";
    }
function showDiv() {
    document.getElementById('uploadDiv').style.display = "block";
    }

$(function() {
    $('#btnRunJob').click(function() {

        $.ajax({
            url: '/addJob',
            data: $('form').serialize(),
            type: 'POST',
            success: function(response) {
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});