import os
import unittest
from microservices_demo.api import demo_pb2
from microservices_demo.api.demo_rsm import Emailer
from microservices_demo.backend.constants import EMAILER_ACTOR_ID
from microservices_demo.backend.emailer.servicer import MailgunServicer
# We must import ONLY the method, so that when our test mocks this method later
# it can still call the original method.
from microservices_demo.backend.helpers.mailgun import (
    MailgunAPIError,
    MockMailgunAPI,
)
from resemble.aio.tests import Resemble
from resemble.aio.workflows import Workflow
from resemble.rsm import fail
from typing import Dict, Optional
from unittest import mock


class TestCase(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self) -> None:
        self.rsm = Resemble()

    async def asyncTearDown(self) -> None:
        await self.rsm.down()

    async def test_emailer(self) -> None:
        # Since we are using the 'real' servicers, they are setting Mailgun with
        # a key provided as ENV variable, so need to set one.
        os.environ['MAILGUN_API_KEY'] = 'some Mailgun key'
        workflow: Workflow = self.rsm.create_workflow(name=self.id())

        RECEIVER = "team@reboot.dev"
        DOMAIN = "reboot.dev"
        unexpected_raise = True

        mock_emailer = MockMailgunAPI()

        # Mock mailgun API to not send real emails during the test.
        def mock_get_mailgun_api(api_key: str):
            return mock_emailer

        # Mock out the `send_email` function so that...
        # 1. We can make it seem like the first attempt to send the email
        #    failed, even though we know that the call to fake Mailgun will have
        #    gone through and the email already got sent.
        # 2. Record the idempotency key of the email that was sent.
        # 3. After the task retries and officially succeeds on the second
        #    attempt, set our `success` event, which the test code can wait
        #    for.
        real_send_email = MockMailgunAPI.send_email

        async def mock_send_email(self, *args, **kwargs):
            nonlocal unexpected_raise

            await real_send_email(self, *args, **kwargs)

            if unexpected_raise == True:
                unexpected_raise = False
                raise MailgunAPIError("Ooops, some error, retry the task!")

        with unittest.mock.patch(
            'microservices_demo.backend.helpers.mailgun._get_mailgun_api',
            mock_get_mailgun_api
        ), unittest.mock.patch(
            'microservices_demo.backend.helpers.mailgun.MockMailgunAPI.send_email',
            mock_send_email
        ):
            await self.rsm.up(servicers=[MailgunServicer], in_process=True)

            emailer = Emailer(EMAILER_ACTOR_ID)

            # SendEmail will check key by itself, so if key exists, it won't
            # send another email and we can always see only 1 accepted event
            # per email with unique idempotency key, otherwise it will send
            # exactly one if fake Mailgun has not such key.
            await emailer.PrepareSendEmail(
                workflow,
                recipient=RECEIVER,
                sender=f'hipsterstore@{DOMAIN}',
                subject='jonathan',
                text="jonathan",
            )

            # Wait until the scheduled task to send a reminder email has run.
            await mock_emailer.success.wait()

            self.assertEqual(len(mock_emailer.emails_sent), 1)

            sent_once = await mock_emailer.is_email_with_idempotency_key_sent_to_recipient(
                RECEIVER,
                DOMAIN,
                mock_emailer.last_idempotency_key,
            )
            self.assertTrue(sent_once)


if __name__ == '__main__':
    unittest.main()
