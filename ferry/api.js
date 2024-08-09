frappe.ui.form.on('Subcontracting Receipt', {
	// refresh(frm) {
	// 	// your code here
	// }
    //update reject_qty if accepted_qty is updated in child table
    accepted_qty: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];
        frm.set_value('rejected_qty', 0);
    },

})