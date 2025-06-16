frappe.listview_settings['Bale Weight Info'] = {
    add_fields: ['status'],
    get_indicator: function(doc) {
        if (doc.status === 'Cancelled') {
            return [__('Cancelled'), 'red'];
        } else if (doc.status === 'Printed') {
            return [__('Printed'), 'green'];
        } else if (doc.status === 'Re-Printed') {
            return [__('Re-Printed'), 'blue'];
        } else {
            return [__('No Printed'), 'orange'];
        }
    }
};