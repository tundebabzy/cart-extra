erpnext.shopping_cart = $.extend(erpnext.shopping_cart, {
    update_cart: function(opts) {
        return frappe.call({
            type: "POST",
            method: "erpnext.shopping_cart.cart.update_cart",
            args: {
                item_code: opts.item_code,
                qty: opts.qty,
                with_items: opts.with_items || 0
            },
            btn: opts.btn,
            callback: function(r) {
                shopping_cart.set_cart_count();
                if (r.message.shopping_cart_menu) {
                    $('.shopping-cart-menu').html(r.message.shopping_cart_menu);
                }
                if(opts.callback)
                    opts.callback(r);
            }
        });
    }
});
