var current_user = null;
var lastHash = "";
var hashChangeEventListener = null;
var ev = null;
var clv = null;
var rv = null;
var sv = null;
var wv = null;

$(document).ready(function() {
    $.ajaxSetup({
        'cache': false
    });
    if (location.hash.length >= 1) {
        location.hash = "";
    }
    var av = new AuthView($("#login-error"));
    clv = new CollegeListView($("#data-college-list"));
    ev = new EditView($("#data-edit-user"), clv.refresh_all);
    rv = new RegisterView($("#data-register-users"));
    sv = new SelfView($("#logged-in-user"));
    wv = new WorkingView($("#messages"));
    $("#login").submit(function() {
        wv.start("Logging in...");
        current_user = new User($("#username").val());
        current_user.login($("#password").val(), function(user) {
            user.fetch_colleges(function(user) {
                clv.render_colleges(user.colleges, !user.is_student);
            });
            $("#login").hide();
            $("#login-error").hide();
            sv.show(user.username);
            wv.end("Login succeeded");
            if (user.colleges.length > 0) {
                wv.start("Loading college information");
            }
        },
        function(response) {
            var errors = response && response.authentication_errors || ['BACKEND_FAIL'];
            av.display_auth_error(errors);
            wv.hide();
        });
        return false;
    });

    $("#username").focus();

    hashChangeEventListener = setInterval("hashChangeEventHandler()", 50);
});

$(document).on("click", ".add-row", function(){
    rv.add_row(college_name_from_hash());
});

function hashChangeEventHandler() {
    var newHash = location.hash.split('#')[1];

    if(newHash != lastHash) {
        lastHash = newHash;
        handle_hash();
    }
}

function handle_hash() {
    ev.hide();
    rv.hide();
    clv.set_all_inactive();
    if (location.hash.substring(1,5) == "edit") {
        var username = location.hash.substring(6,location.hash.length);
        rv.hide();
        wv.start("Loading user");
        ev.show(username, current_user);
        clv.set_active(username);
    } else if (location.hash.substring(1,4) == "reg") {
        rv.show(college_name_from_hash());
        clv.set_register_active(college_name_from_hash());
    }
}

function clear_view() {
    location.hash = '';
}

function college_name_from_hash() {
    return location.hash.substring(5,location.hash.length);
}

function isASCII(str) {
    return /^[\x00-\x7F]*$/.test(str);
}

function isEmail(str) {
    return /^.+@.+\...+$/.test(str);
}

setInterval(function() {
    clv.set_all_inactive();
    if (location.hash.substring(1,5) == "edit") {
        var username = location.hash.substring(6,location.hash.length);
        clv.set_active(username);
    } else if (location.hash.substring(1,4) == "reg") {
        clv.set_register_active(college_name_from_hash());
    }
}, 100);
