import asyncio
from boutique.v1.demo_rsm import Checkout, ProductCatalog
from cart.servicer import CartServicer
from checkout.servicer import CheckoutServicer
from constants import CHECKOUT_ACTOR_ID, PRODUCT_CATALOG_ACTOR_ID
from currencyconverter.servicer import CurrencyConverterServicer
from logger import logger
from productcatalog.servicer import ProductCatalogServicer
from resemble.aio.applications import Application
from resemble.aio.workflows import Workflow
from resemble.integrations.mailgun.servicers import MessageServicer
from shipping.servicer import ShippingServicer

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
    await Checkout.Create(CHECKOUT_ACTOR_ID, workflow)

    await ProductCatalog.LoadProducts(PRODUCT_CATALOG_ACTOR_ID, workflow)


async def main():

    application = Application(
        servicers=servicers,
        initialize=initialize,
    )

    logger.info('🛒 🛒 🛒 Online Boutique is open for business! 🛍️  🛍️  🛍️  ')

    await application.run()


if __name__ == '__main__':
    asyncio.run(main())
