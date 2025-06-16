frappe.listview_settings['Bale Registration'] = {
    onload: function(listview) {
        frappe.call({
            method: 'frappe.client.get_list',
            args: {
                doctype: 'Day Setup',
                filters: {
                    status: 'Opened'
                },
                fields: ['date'],
                limit: 1
            },
            callback: function(response) {
                if (response.message && response.message.length > 0) {
                    const opened_date = response.message[0].date;
                    listview.filter_area.add([[ 'Bale Registration', 'date', '=', opened_date ]]);
                }
            }
        });
    }
};
