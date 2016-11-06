var User = function() {
    return function(username) {
        this.username = username;
        this.first_name = "";
        this.last_name = "";
        this.email = "";
        this.new_email = false;
        this.is_blueshirt = false;
        this.is_student = false;
        this.is_team_leader = false;
        this.has_media_consent = false;
        this.has_withdrawn = false;
        this.colleges = [];
        this.teams = [];
        this.is_logged_in = false;

        var password = "";
        var that = this;

        this.login = function(pw, success_callback, error_callback) {
            password = pw;
            set_header();
            this.fetch(function(u) {
                that.is_logged_in = true;
                success_callback(u);
            }, error_callback);
        };

        this.fetch = function(success_callback, error_callback) {
            $.get("user/" + this.username, function(response) {
                if (typeof(response) === "string") {
                    response = JSON.parse(response);
                }

                that.colleges = $.map(response.colleges, function(v) { return new College(v);});
                that.teams = response.teams;
                clone_simple_properties(response, that);

                success_callback(that);
            }).error(function(response) {
                if (!error_callback) {
                    return;
                }
                response = response.responseText;
                if (typeof(response) === "string") {
                    try {
                        response = JSON.parse(response);
                    } catch(err) {
                        response = null;
                        if (console && console.log) {
                            console.log(err);
                        }
                    }
                }
                error_callback(response);
            });
        };

        this.fetch_colleges = function(callback, skip_users) {
            var colleges = that.colleges;
            var waiting_colleges = colleges.length;
            for (var i = 0; i < colleges.length; i++) {
                var college = colleges[i];
                college.fetch(function (college) {
                    waiting_colleges--;
                    if (waiting_colleges == 0) {
                        callback(that);
                    }
                }, skip_users);
            }
        };

        var clone_simple_properties = function(from, to) {
            to.first_name   = from.first_name;
            to.last_name    = from.last_name;
            to.email        = from.email;
            to.new_email    = from.new_email;
            to.is_blueshirt = from.is_blueshirt;
            to.is_student   = from.is_student;
            to.is_team_leader = from.is_team_leader;
            to.has_media_consent = from.has_media_consent;
            to.has_withdrawn = from.has_withdrawn;
        };

        var set_header = function() {
            var tok = that.username + ':' + password;
            var hash = Base64.encode(tok);
            $.ajaxSetup({
                headers: {
                    'Authorization': "Basic " + hash
                }
            });
        };

        this.can_withdraw = function(user) {
            return !user.has_withdrawn && !user.is_blueshirt && user.username != that.username && that.is_team_leader;
        };

    };
}();
