frappe.provide("erpnext.shopping_cart");
var shopping_cart = erpnext.shopping_cart;

$.extend(shopping_cart, {
    bind_billing_button: function() {
        $("#copy").on("click", function() {
            const data = $("#shipping-form").serializeArray();
            data.forEach(item => {
                $(`#billing #${item.name}`).val(item.value);
            });
        })
    },
    harvest_billing_address: function() {
        const data = $("#billing-form").serializeArray();
        const result = {};
        data.forEach(item => {
            result[item.name] = item.value
        });
        return result;
    },
    harvest_shipping_address: function() {
        const data = $("#shipping-form").serializeArray();
        const result = {};
        data.forEach(item => {
            result[item.name] = item.value
        });
        return result;
    },
    place_order: function(btn) {
        let billing_address = null;
        let shipping_address = null;
        let shipping_is_valid = null;
        let billing_is_valid = null;
        let args = {};

        if (frappe.session.user == 'Guest') {
            billing_address = shopping_cart.harvest_billing_address();
            shipping_address = shopping_cart.harvest_shipping_address();
            shipping_is_valid = shopping_cart.validate($("#shipping-form"))
            billing_is_valid = shopping_cart.validate($("#billing-form"));
            args = { billing_address, shipping_address };
        }

        if (frappe.session.user != 'Guest' || (shipping_is_valid && billing_is_valid)) {
            return frappe.call({
                type: "POST",
                method: "erpnext.shopping_cart.cart.place_order",
                args,
                btn: btn,
                callback: function(r) {
                    if(r.exc) {
                        var msg = "";
                        if(r._server_messages) {
                            msg = JSON.parse(r._server_messages || []).join("<br>");
                        }

                        $("#cart-error")
                            .empty()
                            .html(msg || frappe._("Something went wrong!"))
                            .toggle(true);
                    } else {
                        window.location.href = "/orders/" + encodeURIComponent(r.message);
                    }
                }
            });
        }
    },
    validate: function(formElement) {
        return formElement[0].reportValidity();
    }
});

frappe.ready(function() {
    shopping_cart.bind_billing_button();
})