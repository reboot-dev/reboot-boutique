import asyncio
import grpc
import json
import os
import sys
import time
import uuid
from jinja2 import (
    Environment,
    FileSystemLoader,
    TemplateError,
    select_autoescape,
)
from pyprotoc_plugin.helpers import add_template_path, load_template
from resemble.aio.contexts import (
    ReaderContext,
    TransactionContext,
    WriterContext,
)
from resemble.examples.boutique.api import demo_pb2, demo_pb2_grpc
from resemble.examples.boutique.api.demo_rsm import (
    Cart,
    Checkout,
    Emailer,
    ProductCatalog,
    Shipping,
)
from resemble.examples.boutique.backend.constants import (
    EMAILER_ACTOR_ID,
    PRODUCT_CATALOG_ACTOR_ID,
    SHIPPING_ACTOR_ID,
)
from resemble.examples.boutique.backend.logger import logger


class CheckoutServicer(Checkout.Interface):

    async def Create(
        self,
        context: WriterContext,
        request: demo_pb2.Empty,
    ) -> Checkout.CreateEffects:
        return Checkout.CreateEffects(
            state=demo_pb2.CheckoutState(), response=demo_pb2.Empty()
        )

    async def PlaceOrder(
        self,
        context: TransactionContext,
        request: demo_pb2.PlaceOrderRequest,
    ) -> demo_pb2.PlaceOrderResponse:
        state = await self.read(context)

        # Get user cart.
        cart = Cart(request.user_id)

        get_items_response = await cart.GetItems(context)

        # For each item in the cart, verify that it is a real product, get its
        # price, and convert the price to user currency.
        product_catalog = ProductCatalog(PRODUCT_CATALOG_ACTOR_ID)

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
        shipping = Shipping(SHIPPING_ACTOR_ID)

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
            items=order_items
        )

        async def add_order_result(
            context: WriterContext,
            state: demo_pb2.CheckoutState,
        ) -> Checkout.Interface.Effects:
            state.orders.append(order_result)
            return Checkout.Interface.Effects(state=state)

        await self.write(context, add_order_result)

        # Use a template in the 'templates' folder.
        env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), 'templates')
            ),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template('thanks_for_listening_to_demo.html')

        try:
            confirmation = template.render(order=order_result)
        except TemplateError as err:
            pass

        # Get the actor_id of mailgun service from the state.
        state = await self.read(context)
        await Emailer(state.emailer_id).PrepareSendEmail(
            context,
            recipient=request.email,
            sender='Reboot Team <team@reboot.dev>',
            subject='Thanks from the team at reboot.dev!',
            html=confirmation,
        )

        logger.info(f"Order placed for '{request.email}'")

        return demo_pb2.PlaceOrderResponse(order=order_result)

    async def Orders(
        self,
        context: ReaderContext,
        state: demo_pb2.CheckoutState,
        request: demo_pb2.OrdersRequest,
    ) -> demo_pb2.PlaceOrderResponse:
        return demo_pb2.OrdersResponse(orders=reversed(state.orders))
