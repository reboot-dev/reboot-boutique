import asyncio
import resemble.thirdparty.mailgun
from boutique.v1.demo_rsm import Checkout, ProductCatalog
from cart.servicer import CartServicer
from checkout.servicer import CheckoutServicer
from constants import CHECKOUT_ACTOR_ID, PRODUCT_CATALOG_ACTOR_ID
from currencyconverter.servicer import CurrencyConverterServicer
from productcatalog.servicer import ProductCatalogServicer
from resemble.aio.applications import Application, Servicer
from resemble.aio.external import ExternalContext
from shipping.servicer import ShippingServicer

# All of the servicers that we need to run!
servicers: list[type[Servicer]] = [
    ProductCatalogServicer,
    CartServicer,
    CheckoutServicer,
    ShippingServicer,
] + resemble.thirdparty.mailgun.servicers()

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
