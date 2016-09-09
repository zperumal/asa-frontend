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
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});