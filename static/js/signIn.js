/**
 * Created by zaraperumal on 9/9/16.
 */
$(function() {
    $('#signInBtn').click(function() {

        $.ajax({
            url: '/signIn',
            data: $('form').serialize(),
            type: 'POST',
            success: function(response) {
                document.getElementById("messageSpan").innerHTML=response;
                location.href = "showUserPortal"
                console.log(response);
            },
            error: function(error) {
                document.getElementById("messageSpan").innerHTML=error;
                console.log(error);
            }
        });
    });
});