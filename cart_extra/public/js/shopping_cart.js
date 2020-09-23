const shopping_cart = erpnext.shopping_cart;

frappe.ready(function() {
    frappe.call({
        method: 'cart_extra.utils.create_cart'
    });
});

erpnext.shopping_cart = $.extend(erpnext.shopping_cart, {
    set_cart_count: function() {
		var cart_count = frappe.get_cookie("cart_count");

		if(cart_count) {
			$(".shopping-cart").toggleClass('hidden', false);
		}

		var $cart = $('.cart-icon');
		var $badge = $cart.find("#cart-count");

		if(parseInt(cart_count) === 0 || cart_count === undefined) {
			$cart.css("display", "none");
			$(".cart-items").html('Cart is Empty');
			$(".cart-tax-items").hide();
			$(".btn-place-order").hide();
			$(".cart-addresses").hide();
		}
		else {
			$cart.css("display", "inline");
		}

		if(cart_count) {
			$badge.html(cart_count);
		} else {
			$badge.remove();
		}
	},
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
