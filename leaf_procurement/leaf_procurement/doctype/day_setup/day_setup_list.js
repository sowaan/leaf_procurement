frappe.listview_settings['Day Setup'] = {
    add_fields: ['status'],
    get_indicator: function(doc) {
        if (doc.status === 'Opened') {
            return [__('Opened'), 'red'];
        } else if (doc.status === 'Closed') {
            return [__('Closed'), 'green'];
        } else {
            return [__('Draft'), 'orange'];
        }
    }
};
