var CollegeListView = function() {
    return function(jquery_node) {
        var node = jquery_node;
        var colleges = [];
        var that = this;
        var current_username;
        var allow_registration_last;

        var college_template = TemplateExpander.template("college");
        var user_template = TemplateExpander.template("user_link");
        var media_consent_template = TemplateExpander.template('media_consent');
        var register_template = TemplateExpander.template("register_link");

        var expand_college_template = function(college, allow_registration) {
            $(college.users).each(function(idx, u) {
                var args = {
                    'first': u.first_name,
                    'last': u.last_name
                };
                if (u.has_media_consent) {
                    args.not = '';
                    args.icon = 'camera';
                } else {
                    args.not = 'not ';
                    args.icon = 'none';
                }
                u.media = media_consent_template.render_with(args);
            });
            $.each(college.users, function (index, user) {
                user.class = user.has_withdrawn ? "disabled" : undefined;
            });
            var user_templates = user_template.map_over("user", college.users);
            var register_link = '';
            if (allow_registration) {
                register_link = register_template.render_with({"college":college});
            }
            var final_render = college_template.render_with({
                "users": user_templates,
                "register": register_link,
                "college": college
            });

            return final_render;
        };

        this.render_colleges = function(college_list, allow_registration) {
            colleges = college_list;
            allow_registration_last = allow_registration;

            var result = "";
            for (var i = 0; i < college_list.length; i++) {
                var college = college_list[i];
                result += expand_college_template(college, allow_registration);
            }

            node.html(result);

            $('#data-college-list button.refresh').click(that.refresh_all);
        };

        this.set_active = function(username) {
            this.set_all_inactive();
            var u = $("." + username);
            if (u.length) {
                u.addClass("active");
                current_username = username;
            } else {
                // not a valid username
                clear_view();
            }
        };

        this.set_all_inactive = function() {
            $(".active").removeClass("active");
            current_username = null;
        };

        this.set_register_active = function(college_name) {
            $("#" + college_name + " .register").addClass("active");
            current_username = null;
        };

        this.refresh_all = function() {
            var count = colleges.length;
            $(colleges).each(function(i, college) {
                college.fetch(function() {
                    count -= 1;
                    if (count == 0) {
                        that.render_colleges(colleges, allow_registration_last);
                        if (current_username) {
                            that.set_active(current_username);
                        }
                    }
                });
            });
        };
    };
}();
