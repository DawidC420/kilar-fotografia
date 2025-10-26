# fotoapp/cart.py
from decimal import Decimal

CART_SESSION_KEY = "cart"

def _cart(request):
    return request.session.setdefault(CART_SESSION_KEY, {})

def add(request, photo_id, price, qty=1):
    cart = _cart(request)
    key = str(photo_id)
    item = cart.get(key, {"qty": 0, "price": str(price)})
    item["qty"] += qty
    item["price"] = str(price)
    cart[key] = item
    request.session.modified = True
    return cart

def remove(request, photo_id, qty=1):
    cart = _cart(request)
    key = str(photo_id)
    if key in cart:
        cart[key]["qty"] -= qty
        if cart[key]["qty"] <= 0:
            cart.pop(key)
        request.session.modified = True
    return cart

def set_qty(request, photo_id, qty, price):
    cart = _cart(request)
    key = str(photo_id)
    if qty <= 0:
        cart.pop(key, None)
    else:
        cart[key] = {"qty": qty, "price": str(price)}
    request.session.modified = True
    return cart

def count(request):
    return sum(i["qty"] for i in _cart(request).values())
