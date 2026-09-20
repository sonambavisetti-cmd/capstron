from dataclasses import dataclass

@dataclass
class ProductSchema:
    id: int
    sku: str
    title: str
    description: str
    price: float
    inventory: int
