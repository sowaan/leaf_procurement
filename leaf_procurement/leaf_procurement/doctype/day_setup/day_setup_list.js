frappe.listview_settings['Day Setup'] = {
    add_fields: ['status'],
    get_indicator: function(doc) {
        if (doc.status === 'Opened') {
            return [__('Opened'), 'green'];
        } else if (doc.status === 'Closed') {
            return [__('Closed'), 'blue'];
        } else {
            return [__('Draft'), 'orange'];
        }
    }
};
