/**
 * Created by zaraperumal on 9/9/16.
 */
$(function() {
    $('#signUpBtn').click(function() {

        $.ajax({
            url: '/signUp',
            data: $('form').serialize(),
            type: 'POST',
            success: function(response) {
                document.getElementById("messageSpan").innerHTML=response;
                console.log(response);
            },
            error: function(error) {
                document.getElementById("messageSpan").innerHTML=error;
                console.log(error);
            }
        });
    });
});