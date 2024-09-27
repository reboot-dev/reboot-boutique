import asyncio
import reboot.thirdparty.mailgun
from boutique.v1.demo_rbt import Checkout, ProductCatalog
from cart.servicer import CartServicer
from checkout.servicer import CheckoutServicer
from constants import CHECKOUT_ACTOR_ID, PRODUCT_CATALOG_ACTOR_ID
from currencyconverter.servicer import CurrencyConverterServicer
from productcatalog.servicer import ProductCatalogServicer
from reboot.aio.applications import Application, Servicer
from reboot.aio.external import ExternalContext
from shipping.servicer import ShippingServicer

# All of the servicers that we need to run!
servicers: list[type[Servicer]] = [
    ProductCatalogServicer,
    CartServicer,
    CheckoutServicer,
    ShippingServicer,
] + reboot.thirdparty.mailgun.servicers()

legacy_grpc_servicers: list[type] = [
    CurrencyConverterServicer,
]


async def initialize(context: ExternalContext):
    await Checkout.construct(
        id=CHECKOUT_ACTOR_ID,
    ).idempotently().Create(context)

    await ProductCatalog.construct(
        id=PRODUCT_CATALOG_ACTOR_ID,
    ).idempotently().LoadProducts(context)


async def main():

    application = Application(
        servicers=servicers,
        legacy_grpc_servicers=legacy_grpc_servicers,
        initialize=initialize,
    )

    await application.run()


if __name__ == '__main__':
    asyncio.run(main())
