import asyncio
import grpc
import os
import unittest
from resemble.aio.tests import Resemble
from resemble.aio.workflows import Workflow
from resemble.examples.boutique.api import demo_pb2, demo_pb2_grpc
from resemble.examples.boutique.api.demo_rsm import Cart, Checkout, Shipping
from resemble.examples.boutique.backend.app import initialize, servicers
from resemble.examples.boutique.backend.constants import (
    CHECKOUT_ACTOR_ID,
    SHIPPING_ACTOR_ID,
)
from resemble.examples.boutique.backend.currencyconverter.servicer import (
    CurrencyConverterServicer,
)


class TestCase(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.rsm = Resemble()
        self.config = await self.rsm.up(servicers=servicers)

        self.workflow: Workflow = self.rsm.create_workflow(
            name=f"test-{self.id()}"
        )

        os.environ['MAILGUN_API_KEY'] = 'potato'

        await initialize(self.workflow)

    async def asyncTearDown(self) -> None:
        await self.rsm.down()

    async def test_checkout(self) -> None:
        """Check out a single item successfully."""
        # Add an item to a cart.
        cart = Cart('jonathan')
        await cart.AddItem(
            self.workflow,
            item=demo_pb2.CartItem(
                product_id='OLJCESPC7Z',
                quantity=42,
            ),
        )

        # Get a shipping quote for that card in preparation for checkout.
        shipping = Shipping(SHIPPING_ACTOR_ID)
        get_quote_response = await shipping.GetQuote(
            self.workflow,
            quote_expiration_seconds=30,
        )

        # Check out the order.
        checkout = Checkout(CHECKOUT_ACTOR_ID)

        place_order_response = await checkout.PlaceOrder(
            self.workflow,
            user_id='jonathan',
            user_currency='USD',
            email='hi@reboot.dev',
            quote=get_quote_response.quote,
        )

        self.assertTrue(place_order_response.HasField('order'))

        # Check a couple of order result fields for correctly filled values.
        self.assertEqual(len(place_order_response.order.items), 1)
        order_item = place_order_response.order.items[0]
        expected_item_cost = demo_pb2.Money(
            currency_code='USD', units=19, nanos=(99 * 10000000)
        )
        self.assertEqual(order_item.cost, expected_item_cost)
        self.assertEqual(order_item.item.quantity, 42)
        expected_shipping_cost = demo_pb2.Money(
            currency_code='USD', units=8, nanos=(99 * 10000000)
        )
        self.assertEqual(
            place_order_response.order.shipping_cost, expected_shipping_cost
        )

        # The cart must have been emptied.
        get_items_response = await cart.GetItems(self.workflow)
        self.assertEqual(len(get_items_response.items), 0)

        # The order must have been registered.
        orders_response = await checkout.Orders(self.workflow)
        self.assertEqual(len(orders_response.orders), 1)
        self.assertEqual(
            orders_response.orders[0].order_id,
            place_order_response.order.order_id
        )

    async def test_checkout_quote_expired(self) -> None:
        """Check out a single item with an expired shipping quote, and see the
        checkout fail to complete."""
        # Add an item to a cart.
        cart = Cart('jonathan')
        await cart.AddItem(
            self.workflow,
            item=demo_pb2.CartItem(
                product_id='OLJCESPC7Z',
                quantity=42,
            ),
        )

        # Get a shipping quote for that card in preparation for checkout.
        # Use an expiration time of 0 so that the quote will expire immediately.
        shipping = Shipping(SHIPPING_ACTOR_ID)
        get_quote_response = await shipping.GetQuote(
            self.workflow,
            quote_expiration_seconds=0,
        )

        await asyncio.sleep(1)

        # The quote should have expired and the order should not have
        # gone through.
        checkout = Checkout(CHECKOUT_ACTOR_ID)

        with self.assertRaises(Checkout.PlaceOrderError) as raised:
            place_order_response = await checkout.PlaceOrder(
                self.workflow,
                user_id='jonathan',
                user_currency='USD',
                email='hi@reboot.dev',
                quote=get_quote_response.quote,
            )

        self.assertTrue(
            isinstance(
                raised.exception.detail,
                demo_pb2.ShippingQuoteInvalidOrExpired,
            )
        )

        self.assertEquals(
            raised.exception.message,
            "Error in 'Checkout.PlaceOrder': Error in 'Shipping.PrepareShipOrder'",
        )

    async def test_currency_conversion(self) -> None:
        """Test a couple of currency conversions to make sure the Money format
        is handled correctly."""
        test_cases = [
            (
                demo_pb2.CurrencyConversionRequest(
                    products=[
                        demo_pb2.Product(
                            price=demo_pb2.Money(
                                currency_code='USD',
                                units=8,
                                nanos=(99 * 10000000)
                            ),
                        )
                    ],
                    to_code='USD'
                ),
                demo_pb2.Money(
                    currency_code='USD', units=8, nanos=(99 * 10000000)
                )
            ),
            (
                demo_pb2.CurrencyConversionRequest(
                    products=[
                        demo_pb2.Product(
                            price=demo_pb2.Money(
                                currency_code='EUR', units=1, nanos=0
                            ),
                        )
                    ],
                    to_code='USD',
                ),
                demo_pb2.Money(
                    currency_code='USD',
                    units=1,
                    nanos=int(0.1305 * 1000000000)
                )
            )
        ]

        # TODO(rjh): remove the need for us to reach into the channel manager
        # and to pass an actor ID when reaching out to a plain gRPC service.
        async with self.workflow.channel_manager.get_channel_from_service_name(
            'resemble.examples.boutique.api.CurrencyConverter',
            actor_id='',
        ) as channel:
            stub = demo_pb2_grpc.CurrencyConverterStub(channel)
            for conversion_request, expected_conversion in test_cases:
                self.assertEqual(len(conversion_request.products), 1)

                conversion = await stub.Convert(conversion_request)

                self.assertEqual(len(conversion.products), 1)
                self.assertEqual(
                    conversion.products[0].price,
                    expected_conversion,
                )


if __name__ == '__main__':
    unittest.main()
