frappe.listview_settings['Bale Registration'] = {
    // get_indicator: function (doc) {
    //       console.log(`Doc loaded: ${doc.name}, Status: ${doc.bale_status}`);   

    //     if (doc.bale_status === 'In Registration') {
    //         return [__('In Registration'), 'orange', 'bale_status,=,In Registration'];
    //     } else if (doc.bale_status === 'In Buying') {
    //         return [__('In Buying'), 'blue', 'bale_status,=,In Buying'];
    //     } else if (doc.bale_status === 'In Weighment') {
    //         return [__('In Weighment'), 'purple', 'bale_status,=,In Weighment'];
    //     } else if (doc.bale_status === 'Completed') {
    //         return [__('Completed'), 'green', 'bale_status,=,Completed'];
    //     } else if (doc.bale_status === 'Cancelled') {
    //         return [__('Cancelled'), 'red', 'bale_status,=,Cancelled'];
    //     }
    // },
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
