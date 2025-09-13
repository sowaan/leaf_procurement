frappe.listview_settings['Bale Audit'] = {
    onload: function(listview) {
        //console.log("Bale Audit list view loaded:", listview);
        hide_filters_from_list_view(listview);
    },
    refresh: function (listview) {
        hide_filters_from_list_view(listview);
    }
}
function hide_filters_from_list_view(list_view) {
    if (!list_view) return;

    // ✅ Check for Administrator
    if (frappe.session.user === "Administrator") {
        return; // show all records
    }

frappe.db.get_single_value("Leaf Procurement Settings", "live_server")
        .then(live_server => {
            if (live_server) {
                return; // show all records
            }
            apply_last_two_days_filter(list_view);
        });
}

function apply_last_two_days_filter(list_view) {
    // Hide sidebar
    if (list_view.page && list_view.page.sidebar) {
        try { list_view.page.sidebar.toggle(false); } catch (e) {}
    }

    // Date range: last 2 days
    const today = frappe.datetime.get_today();
    const two_days_ago = frappe.datetime.add_days(today, -2);

    // Reset and add filters
    try {
        list_view.filter_area.clear();
    } catch (e) {}

    list_view.filter_area.add([
        ["Bale Audit", "date", ">=", two_days_ago],
        ["Bale Audit", "date", "<=", today]
    ]);

    // Hide filter bar and filter button
    setTimeout(() => {
        if (list_view.filter_area && list_view.filter_area.wrapper) {
            $(list_view.filter_area.wrapper).hide();
        }

        const $filter_btn = list_view.page.wrapper.find('.filter-button');
        if ($filter_btn.length) {
            $filter_btn.hide();
        }

        // Refresh list to apply filter
        list_view.refresh();
    }, 500);
}
