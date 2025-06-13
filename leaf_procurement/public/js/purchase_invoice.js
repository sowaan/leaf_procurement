

frappe.ui.form.on('Purchase Invoice', {
    refresh(frm) {
        // hide print button
        // frm.page.set_inner_btn_group_as_primary('print');
        $('[data-original-title="Print"]').hide();
        frm.add_custom_button(__('Print'), async () => {

        })
    }
});