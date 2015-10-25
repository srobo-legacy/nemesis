var Colleges = {}

var College = function() {
    return function(college_name) {
        var that = this;
        this.canonical_name = college_name;
        this.english_name = "";
        this.users = [];
        this.teams = [];

        var fetch_helper = function(callback) {
            $.get("colleges/" + that.canonical_name, function(response) {
                if (typeof(response) == "string") {
                    response = JSON.parse(response);
                }

                that.english_name = response.name;
                that.teams = response.teams;
                var user_requests = response.users.length;
                that.users = $.map(response.users, function(v) { return new User(v); });
                Colleges[that.canonical_name] = that;
                callback(that);
            });
        };

        this.fetch = function(callback) {
            wv.start("Loading colleges");
            fetch_helper(function() {
                wv.start("Fetching users");
                that.load_users(function(college) {
                    wv.hide();
                    callback(college);
                });
            });
        };

        this.load_users = function(callback) {
            var user_requests = that.users.length;
            $.map(that.users, function(u) {
                u.fetch(function() {
                    user_requests--;
                    if (user_requests == 0) {
                        callback(that);
                    }
                });
            });
        };
    };
}();
