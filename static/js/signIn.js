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
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    });
});