# fotoapp/context_processors.py
from .cart import count

def cart_count(request):
    """
    Zwraca zmienną 'cart_count' z liczbą elementów w koszyku,
    dostępną globalnie w każdym szablonie.
    """
    try:
        return {"cart_count": count(request)}
    except Exception:
        return {"cart_count": 0}
