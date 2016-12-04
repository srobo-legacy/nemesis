var current_user = null;
var lastHash = "";
var av = null;

$(document).ready(function() {
    var init_data = $.parseJSON($('#init-data').text());
    $.ajaxSetup({
        'cache': false,
        'beforeSend': function(xhr, settings) {
            settings.url = init_data.root + settings.url;
        }
    });

    current_user = new User(init_data.username);

    av = new ChangePasswordView($('#data-user-set-password'), current_user);

    current_user.login(init_data.password, function(user) {
        av.show(user);
    });
});
