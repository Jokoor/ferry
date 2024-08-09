// Copyright (c) 2024, Royalsmb and contributors
// For license information, please see license.txt

frappe.ui.form.on("Scan", {
    refresh(frm) {
        // Flag to prevent multiple scans within the delay period
        let scanning = false;

        new frappe.ui.Scanner({
            dialog: true, // open camera scanner in a dialog
            multiple: true, // stop after scanning one value
            on_scan(data) {
                
                // remove the url from the the data https://qr.wave.com/wQ7P8QMLgXu9
                data = data.decodedText.split("/").pop();

                
                if (!scanning) {
                    scanning = true; // Set the flag to true
                    console.log(data);
                    frappe.call({
                        method: "ferry.api.make_sales_invoice",
                        args: {
                            "customer": data,
                        },
                        callback: function(r) {
                            // if (r.message) {
                            //     frappe.utils.play_sound("submit");
                            //     console.log(r)
                            // } else {
                            //     console.log("No Customer found")
                            // }
                            if (r.message == 0) {
                                console.log(data)
                                d = frappe.msgprint(__('Customer has no active subscription'));
                                d.show();
                                setTimeout(function() {
                                    d.hide();
                                    scanning = false;
                                }, 2000);
                            } else if (r.message == 1) {
                                d = frappe.msgprint(__('Customer balance is less than the fare'));
                                d.show();
                                setTimeout(function() {
                                    d.hide();
                                    scanning = false;
                                }, 2000);

                            } else {
                                frappe.utils.play_sound("submit");
                                console.log(r)
                                d = frappe.msgprint(__('Ticket Purchased Successfully'));
                                d.show();
                                setTimeout(function() {
                                    d.hide();
                                    scanning = false;
                                }, 2000);
                                
                            }
                        }
                    });

                    // Set a timeout to reset the scanning flag after 5 seconds
                    
                }
            }
        });
    },
    display_message: function(frm, message) {
        frappe.msgprint(message);
        // hide the message after 2 seconds


    }
});
