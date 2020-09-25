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
    }
});

frappe.ready(function() {
    shopping_cart.bind_billing_button();
})