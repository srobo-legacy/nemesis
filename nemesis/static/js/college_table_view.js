var CollegeTableView = function() {
    return function(jquery_node) {
        var node = jquery_node;
        var colleges = [];
        var that = this;
        var allow_registration_last;

        var college_table_template = TemplateExpander.template("college_table");
        var college_row_template = TemplateExpander.template("college_table_row");

        this.hide = function() {
            node.hide();
        };

        this.render_colleges = function(college_list, allow_registration) {
            colleges = college_list;
            allow_registration_last = allow_registration;

            var rows = [];
            for (var i = 0; i < college_list.length; i++) {
                var college = college_list[i];
                var media_consent_portion = college.num_media_consent / (
                    college.num_team_leaders +
                    college.num_students -
                    college.num_withdrawn
                );
                var row_render = college_row_template.render_with({
                    'college': college,
                    'media_consent_percent': Math.round(media_consent_portion * 100)
                });
                rows.push(row_render);
            }

            var table_render = college_table_template.render_with({
                'college_rows': rows.join('\n')
            });

            node.html(table_render);
            node.show();
        };

        this.refresh_all = function() {
            var count = colleges.length;
            $(colleges).each(function(i, college) {
                college.fetch(function() {
                    count -= 1;
                    if (count == 0) {
                        that.render_colleges(colleges, allow_registration_last);
                    }
                }, true);
            });
        };
    };
}();
