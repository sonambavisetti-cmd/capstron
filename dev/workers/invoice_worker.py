import time
from dev.services.invoice import generate_invoice

# Simple worker loop (for local use, not production)
def process(order_id: int):
    # simulate queue delay
    time.sleep(0.5)
    return generate_invoice(order_id)
