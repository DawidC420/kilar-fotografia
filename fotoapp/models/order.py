from django.db import models
from decimal import Decimal

class Order(models.Model):
    """
    Reprezentuje zamówienie wygenerowane po płatności.
    Zawiera link (relatywny) do ZIP-a, email klienta, sumę oraz session_key,
    żeby wyświetlać zamówienia tylko dla danej sesji klienta.
    """
    email = models.EmailField(null=True, blank=True)
    zip_url = models.CharField(max_length=500)  # np. '/media/zips/plik.zip'
    date = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    session_key = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Zamówienie #{self.id} — {self.date:%Y-%m-%d %H:%M}"


class OrderItem(models.Model):
    """
    Pozycja zamówienia: powiązanie z Photo oraz cena w chwili zakupu.
    """
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    photo = models.ForeignKey("Photo", on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        pid = self.photo.id if self.photo else "brak"
        return f"OrderItem: order={self.order.id} photo={pid} price={self.price}"
