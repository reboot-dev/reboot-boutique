import asyncio
import grpc
import os
from concurrent import futures
from microservices_demo.api import demo_pb2, demo_pb2_grpc, demo_rsm
from microservices_demo.api.demo_rsm import (
    Cart,
    Checkout,
    Emailer,
    ProductCatalog,
)
from microservices_demo.backend.cart.servicer import CartServicer
from microservices_demo.backend.checkout.servicer import CheckoutServicer
from microservices_demo.backend.constants import (
    CHECKOUT_ACTOR_ID,
    EMAILER_ACTOR_ID,
    PRODUCT_CATALOG_ACTOR_ID,
)
from microservices_demo.backend.currencyconverter.servicer import (
    CurrencyConverterServicer,
)
from microservices_demo.backend.emailer.servicer import MailgunServicer
from microservices_demo.backend.logger import logger
from microservices_demo.backend.productcatalog.servicer import (
    ProductCatalogServicer,
)
from microservices_demo.backend.shipping.servicer import ShippingServicer
from resemble.aio.applications import Application
from resemble.aio.servicers import Serviceable, Servicer
from resemble.aio.types import assert_type
from resemble.aio.workflows import Workflow
from resemble.rsm import fail
from respect.logging import formatter

# All of the servicers that we need to run!
servicers: list[type] = [
    ProductCatalogServicer,
    CartServicer,
    CheckoutServicer,
    ShippingServicer,
    MailgunServicer,
    CurrencyConverterServicer,
]


async def initialize(workflow: Workflow):
    if 'MAILGUN_API_KEY' not in os.environ or len(
        os.environ['MAILGUN_API_KEY']
    ) == 0:
        fail('Please set MAILGUN_API_KEY environment variable')

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
