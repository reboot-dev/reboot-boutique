import os
import uuid
from boutique.v1 import demo_pb2, demo_pb2_grpc
from boutique.v1.demo_rsm import Cart, Checkout, ProductCatalog, Shipping
from constants import PRODUCT_CATALOG_ACTOR_ID, SHIPPING_ACTOR_ID
from jinja2 import Environment, FileSystemLoader, select_autoescape
from logger import logger
from resemble.aio.call import Options
from resemble.aio.contexts import (
    ReaderContext,
    TransactionContext,
    WriterContext,
)
from resemble.aio.secrets import Secrets
from resemble.thirdparty.mailgun import MAILGUN_API_KEY_SECRET_NAME
from resemble.thirdparty.mailgun.v1.mailgun_rsm import Message
from typing import Optional


class CheckoutServicer(Checkout.Interface):

    def __init__(self):
        try:
            self._secrets: Optional[Secrets] = Secrets()
        except:
            # TODO(rjh,stuhood): remove this when secrets are supported on the
            #                    Cloud.
            # TODO(rjh,stuhood): make an error reading the Cloud API key more
            #                    specific than `Exception` so this use case
            #                    doesn't need to catch everything?
            logger.warning(
                "Failed to get secrets access, probably because secrets are "
                "not supported on the Reboot Cloud yet. Will not use secrets."
            )
            self._secrets = None

    async def Create(
        self,
        context: WriterContext,
        state: Checkout.State,
        request: demo_pb2.Empty,
    ) -> demo_pb2.Empty:
        return demo_pb2.Empty()

    async def PlaceOrder(
        self,
        context: TransactionContext,
        state: Checkout.State,
        request: demo_pb2.PlaceOrderRequest,
    ) -> demo_pb2.PlaceOrderResponse:
        # Get user cart.
        cart = Cart.lookup(request.user_id)

        get_items_response = await cart.GetItems(context)

        # For each item in the cart, verify that it is a real product, get its
        # price, and convert the price to user currency.
        product_catalog = ProductCatalog.lookup(PRODUCT_CATALOG_ACTOR_ID)

        # Convert to user currency.
        order_items: list[demo_pb2.OrderItem] = []
        async with context.legacy_grpc_channel() as channel:
            stub = demo_pb2_grpc.CurrencyConverterStub(channel)
            for item in get_items_response.items:
                product_info = await product_catalog.GetProduct(
                    context,
                    id=item.product_id,
                )

                conversion_request = demo_pb2.CurrencyConversionRequest(
                    products=[product_info],
                    to_code=request.user_currency,
                )
                converted_product = await stub.Convert(conversion_request)

                order_items.append(
                    demo_pb2.OrderItem(
                        item=item,
                        cost=converted_product.products[0].price,
                    )
                )

        order_id = str(uuid.uuid4())

        # Prepare the shipping.
        #
        # NOTE: WE MUST PREPARE THE SHIPPING FIRST BECAUSE WE "RETURN"
        # ERRORS THAT ARE NOT SEEN AS FAILURES SO THE TRANSACTION WILL
        # COMMIT!
        shipping = Shipping.lookup(SHIPPING_ACTOR_ID)

        await shipping.PrepareShipOrder(
            context,
            quote=request.quote,
        )

        # TODO: convert request.quote.cost to user currency.

        # TODO: Total up the price for the user.

        # TODO: Charge the user's credit card.

        # Empty the user's cart.
        await cart.EmptyCart(context)

        # Send a confirmation email to the user.
        order_result = demo_pb2.OrderResult(
            order_id=order_id,
            shipping_cost=request.quote.cost,
            shipping_address=request.address,
            items=order_items,
        )

        state.orders.append(order_result)

        # Use a template in the 'templates' folder.
        env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), 'templates')
            ),
            autoescape=select_autoescape(['html', 'xml']),
        )
        template = env.get_template('thanks_for_listening_to_demo.html')

        confirmation = template.render(order=order_result)

        if self._secrets is not None:
            mailgun_api_key = await self._secrets.get(
                MAILGUN_API_KEY_SECRET_NAME
            )

            await Message.construct().Send(
                context,
                Options(bearer_token=mailgun_api_key.decode()),
                recipient=request.email,
                sender='Reboot Team <team@reboot.dev>',
                domain='reboot.dev',
                subject='Thanks from the team at reboot.dev!',
                html=confirmation,
            )
        else:
            # TODO(rjh,stuhood): remove this when secrets are supported on the
            #                    Cloud.
            logger.warning(
                "No secrets available. Will not send order confirmation email."
            )
        logger.info(f"Order placed for '{request.email}'")

        return demo_pb2.PlaceOrderResponse(order=order_result)

    async def Orders(
        self,
        context: ReaderContext,
        state: Checkout.State,
        request: demo_pb2.OrdersRequest,
    ) -> demo_pb2.OrdersResponse:
        return demo_pb2.OrdersResponse(orders=reversed(state.orders))
