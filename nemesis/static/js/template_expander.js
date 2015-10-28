var TemplateExpander = function () {
    var make_list = function(items, attrs) {
        attrs = attrs || "";
        var build = "<ul" + attrs + ">";

        for (var i = 0 ; i < items.length; i++) {
            build += "<li>" + items[i] + "</li>";
        }

        build += "</ul>";
        return build;
    };

    return {
        "escape" : function(text) {
            return $('<div/>').text(text).html().replace(/'/g, '&#39;').replace(/"/g, '&quot;');
        },
        "template" : function(template_name) {
            return new Template($("#" + template_name).html());
        },
        "make_select" : function(name, options, selected) {
            var build = "<select name='" + name + "'>";

            for (var i = 0 ; i < options.length; i++) {
                var opt = options[i];
                var selectAttr = selected == opt ? "' selected='selected" : '';
                build += "<option value='" + opt + selectAttr + "'>" + opt + "</option>";
            }

            build += "</select>";
            return build;
        },
        "make_list" : make_list,
        "make_checkboxes" : function(name, options, selected) {
            if (!(selected instanceof Array)) {
                selected = [selected];
            }

            var items = [];
            for (var i = 0 ; i < options.length; i++) {
                var opt = options[i];
                var selectAttr = $.inArray(opt, selected) >= 0 ? "' checked='checked" : '';
                var input = "<input type='checkbox' name='" + name + selectAttr + "' value='" + opt + "'>";
                items.push("<label>" + input + opt + "</label>");
            }

            var build = make_list(items);
            return build;
        }
    };
}();

var Template = function() {
    return function(template_text) {
        var template_text = template_text;

        this.escape = TemplateExpander.escape;

        this.render_with = function(hash) {
            var build = "";
            for (var i = 0; i < template_text.length; i++) {
                if (template_text.charAt(i) == "{") {
                    var end_of_section = template_text.indexOf("}", i);
                    var key = template_text.substring(i+1, end_of_section);
                    var split = key.split(".");
                    var value = '';
                    var majorkey = split[0];
                    var at_idx = majorkey.indexOf(':');
                    if (at_idx >= 0) {
                        majorkey = majorkey.substring(at_idx + 1);
                    }
                    if (split.length == 1) {
                        value = hash[majorkey];
                    } else {
                        var minorkey = split[1];
                        value = hash[majorkey][minorkey];
                    }
                    if (at_idx == -1) {
                        value = this.escape(value);
                    }
                    build += value;
                    i = end_of_section;
                } else {
                    build += template_text.charAt(i);
                }
            }
            return build;
        };

        this.render = function() {
            return this.render_with({});
        };

        this.map_over = function(key, values) {
            var build = [];
            for (var i = 0; i < values.length; i++) {
                var h = {};
                h[key] = values[i];
                build.push(this.render_with(h));
            }
            return build.join("\n");
        };
    };
}();

// node require() based exports.
if (typeof(exports) != 'undefined') {
	exports.Template = Template;
	exports.TemplateExpander = TemplateExpander;
}
