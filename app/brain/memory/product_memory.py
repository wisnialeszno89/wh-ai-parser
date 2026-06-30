class ProductMemory:

    def __init__(self):

        self.products = {}

    def add(
        self,
        product
    ):

        self.products[
            product.code
        ] = product

    def get(
        self,
        code
    ):

        return self.products.get(
            code
        )