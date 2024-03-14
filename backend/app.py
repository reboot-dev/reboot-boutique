import asyncio
from resemble.aio.applications import Application
from resemble.aio.workflows import Workflow
from resemble.examples.boutique.api.demo_rsm import Checkout, ProductCatalog
from resemble.examples.boutique.backend.cart.servicer import CartServicer
from resemble.examples.boutique.backend.checkout.servicer import (
    CheckoutServicer,
)
from resemble.examples.boutique.backend.constants import (
    CHECKOUT_ACTOR_ID,
    PRODUCT_CATALOG_ACTOR_ID,
)
from resemble.examples.boutique.backend.currencyconverter.servicer import (
    CurrencyConverterServicer,
)
from resemble.examples.boutique.backend.logger import logger
from resemble.examples.boutique.backend.productcatalog.servicer import (
    ProductCatalogServicer,
)
from resemble.examples.boutique.backend.shipping.servicer import (
    ShippingServicer,
)
from resemble.integrations.mailgun.servicers import MessageServicer

# All of the servicers that we need to run!
servicers: list[type] = [
    ProductCatalogServicer,
    CartServicer,
    CheckoutServicer,
    ShippingServicer,
    MessageServicer,
    CurrencyConverterServicer,
]


async def initialize(workflow: Workflow):
    checkout = Checkout(CHECKOUT_ACTOR_ID)
    await checkout.Create(workflow)

    product_catalog = ProductCatalog(PRODUCT_CATALOG_ACTOR_ID)

    await product_catalog.LoadProducts(workflow)


async def main():

    application = Application(
        servicers=servicers,
        initialize=initialize,
    )

    logger.info('🛒 🛒 🛒 Online Boutique is open for business! 🛍️  🛍️  🛍️  ')

    await application.run()


if __name__ == '__main__':
    asyncio.run(main())
