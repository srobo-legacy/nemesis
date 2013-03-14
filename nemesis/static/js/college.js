var Colleges = {}

var College = function() {
    return function(college_name) {
        var that = this;
        this.canonical_name = college_name;
        this.english_name = "";
        this.users = [];
        this.teams = [];

        this.fetch = function(callback) {
            $.get("colleges/" + this.canonical_name, function(response) {
                if (typeof(response) == "string") {
                    response = JSON.parse(response);
                }

                that.english_name = response.name;
                that.teams = response.teams;
                user_requests = response.users.length;
                that.users = $.map(response.users, function(v) {
                    u = new User(v);
                    u.fetch(function() {
                        user_requests--;
                        if (user_requests == 0) {
                            Colleges[that.canonical_name] = that;
                            callback(that);
                        }
                    });

                    return u;
                });
            });
        };
    };
}();
