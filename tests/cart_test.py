import datetime
import os
import unittest
from resemble.aio.tests import Resemble
from resemble.aio.workflows import Workflow
from resemble.boutique.api.v1 import demo_pb2
from resemble.boutique.api.v1.demo_rsm import Cart
from resemble.boutique.backend.cart.servicer import CartServicer
# We must import ONLY the method, so that when our test mocks this method later
# it can still call the original method.
from resemble.boutique.backend.helpers.mailgun import MockMailgunAPI
from unittest import mock


class TestCase(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.rsm = Resemble()

    async def asyncTearDown(self) -> None:
        await self.rsm.down()

    async def test_cart_email(self) -> None:
        # Since we are using the 'real' servicers, they are setting Mailgun with
        # a key provided as ENV variable, so need to set one.
        os.environ['MAILGUN_API_KEY'] = 'some Mailgun key'
        workflow: Workflow = self.rsm.create_workflow(name=self.id())

        RECEIVER = "team@reboot.dev"
        DOMAIN = "reboot.dev"
        real_schedule = CartServicer.schedule

        def mock_schedule(servicer, _):
            return real_schedule(servicer, datetime.timedelta(seconds=1.))

        mock_emailer = MockMailgunAPI()

        # Mock mailgun API to not send real emails during the test.
        def mock_get_mailgun_api(api_key):
            return mock_emailer

        with unittest.mock.patch(
            'resemble.boutique.backend.helpers.mailgun._get_mailgun_api',
            mock_get_mailgun_api,
        ), unittest.mock.patch(
            'resemble.boutique.backend.cart.servicer.CartServicer.schedule',
            mock_schedule,
        ):
            await self.rsm.up(servicers=[CartServicer], in_process=True)

            cart = Cart("Cart service")

            await cart.AddItem(
                workflow,
                item=demo_pb2.CartItem(
                    product_id='OLJCESPC7Z',
                    quantity=42,
                ),
            )

            # Wait until the scheduled task to send a reminder email has run.
            await mock_emailer.success.wait()

            await cart.EmptyCart(workflow)

            self.assertEqual(len(mock_emailer.emails_sent), 1)
            sent_once = await mock_emailer.is_email_with_idempotency_key_sent_to_recipient(
                RECEIVER,
                DOMAIN,
                mock_emailer.last_idempotency_key,
            )

            self.assertEqual(sent_once, True)


if __name__ == '__main__':
    unittest.main()
