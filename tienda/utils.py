# utils.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO
import random
import string

def generate_order_pdf(order):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)

    # 🔹 Información del cliente
    c.drawString(50, 730, f"Cliente: {order.user.nombre} {order.user.apellidos}")
    c.drawString(50, 710, f"Email: {order.user.email}")

    # 🔹 Información de la orden
    c.drawString(50, 690, f"Número de pedido: {order.id}")
    c.drawString(50, 670, f"Subtotal: S/ {order.subtotal}")
    c.drawString(50, 650, f"Envío: S/ {order.shipping}")
    c.drawString(50, 630, f"Total: S/ {order.total}")

    # 🔹 Items de la orden
    y = 600
    for item in order.items.all():
        c.drawString(50, y, f"{item.producto.nombre_producto} x {item.cantidad} - S/ {item.subtotal}")
        y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer


# ✅ Nueva función para generar código único de orden
def generate_unique_order_code():
    """
    Genera un código único de pedido con formato ORD-XXXXXX.
    """
    prefix = "ORD-"
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return prefix + code
