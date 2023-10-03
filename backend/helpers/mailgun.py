import aiohttp
import asyncio
import random
from abc import ABC, abstractmethod
from resemble.boutique.api.v1 import demo_pb2
from typing import Any, Optional


class MailgunAPIError(RuntimeError):
    pass


class _AbstractMailgunAPI(ABC):

    @abstractmethod
    async def send_email(
        self,
        *,
        sender: str,
        recipient: str,
        subject: str,
        domain: str,
        idempotency_key: str,
        body: str,
        body_type: str,
    ):
        pass

    @abstractmethod
    async def is_email_with_idempotency_key_sent_to_recipient(
        self,
        recipient: str,
        domain: str,
        idempotency_key: str,
    ) -> bool:
        pass


class MailgunAPI(_AbstractMailgunAPI):

    def __init__(self, api_key: str):
        super().__init__()
        self._api_key = api_key

    async def send_email(
        self,
        *,
        sender: str,
        recipient: str,
        subject: str,
        domain: str,
        idempotency_key: str,
        body: str,
        body_type: str,
    ):
        """Sends an email from the 'sender' to the 'recipient' using the
        provided fields. The 'domain' parameter is used to access your Mailgun
        API associated with the given domain name, and it needs to be accessible
        by Mailgun for usage.
        The 'text' field contains the plain text that will serve as the email
        body. The 'html' parameter accepts plain HTML content, which will be
        rendered in the email by Mailgun. To ensure the tracking of specific
        emails for POST API calls, include the 'idempotency_key' as a generated
        string. This key is added as a user variable and helps in uniquely
        identifying and managing emails."""

        async with aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(login="api", password=self._api_key)
        ) as session:
            async with session.post(
                f"https://api.mailgun.net/v3/{domain}/messages",
                data={
                    "from": sender,
                    "to": recipient,
                    "subject": subject,
                    body_type: body,
                    "v:idempotency_message_key": idempotency_key,
                }
            ) as response:
                if response.status != 200:
                    raise MailgunAPIError(
                        f"Something went wrong while running POST on Mailgun API, error {response.status}"
                    )

    async def is_email_with_idempotency_key_sent_to_recipient(
        self,
        recipient: str,
        domain: str,
        idempotency_key: str,
    ) -> bool:
        async with aiohttp.ClientSession(
            auth=aiohttp.BasicAuth(login="api", password=self._api_key)
        ) as session:
            user_variables = f"{{'idempotency_message_key': '{idempotency_key}'}}"

            async with session.get(
                f"https://api.mailgun.net/v3/{domain}/events",
                params={
                    "recipient": recipient,
                    "user-variables": user_variables,
                    # Mailgun retains the detailed data for one day for free accounts and
                    # up to 30 days for paid accounts based on subscription plan. While
                    # using the service you may probably change the
                    # requirements that suits for your current situation.
                    "event": "accepted",
                }
            ) as response:
                if response.status == 200:
                    body = await response.json()
                    if (len(body['items']) != 0):
                        # Since `items` is not empty, it means that the email
                        # with such key has already been sent.
                        return True
                else:
                    raise MailgunAPIError(
                        f"Something went wrong while running GET on Mailgun API, error {response.status}"
                    )

        return False


def _get_mailgun_api(api_key: str):
    return MailgunAPI(api_key)


class Mailgun:

    def __init__(self, api_key: str):
        self._mailgun_api = _get_mailgun_api(api_key)

    async def send_email_idempotently(
        self,
        *,
        sender: str,
        recipient: str,
        subject: str,
        domain: str,
        idempotency_key: str,
        body: str,
        body_type: str,
    ):
        # To ensure idempotency for our email sending process, we rely on
        # querying an endpoint that provides a list of events related to the
        # email delivery. The endpoint we query for events operates on an
        # eventually consistent basis, which means that there might be a
        # slight delay in reflecting the latest events. To guarantee that
        # the endpoint has fully caught up and to avoid any potential
        # duplicates, we wait for 10 seconds (according to our statistics 10
        # seconds should be enough for the worst case) after sending the
        # email before concluding that the email has either been
        # successfully delivered or not.
        await asyncio.sleep(10)

        if (
            not await
            self._mailgun_api.is_email_with_idempotency_key_sent_to_recipient(
                recipient,
                domain,
                idempotency_key,
            )
        ):
            await self._mailgun_api.send_email(
                sender=sender,
                recipient=recipient,
                subject=subject,
                domain=domain,
                body=body,
                body_type=body_type,
                idempotency_key=idempotency_key,
            )


# Mock version for testing with no actual email sending.
class MockMailgunAPI(_AbstractMailgunAPI):

    def __init__(self):
        self.emails_sent: list[tuple[str, str]] = []
        self.last_idempotency_key = ''
        self.success = asyncio.Event()

    async def wait_and_append(
        self, recipient: str, idempotency_key: Optional[str]
    ):
        # Trying to emulate mailgun, that doesn't immediately send an email,
        # but is eventually consistent, so if we remove wait at 'Mailgun' we
        # will fail.
        await asyncio.sleep(random.uniform(1.0, 5.0))
        if idempotency_key is not None:
            self.emails_sent.append((recipient, idempotency_key))
            self.success.set()

    async def send_email(
        self,
        *,
        sender: str,
        recipient: str,
        subject: str,
        domain: str,
        idempotency_key: str,
        body: str,
        body_type: str,
    ):
        if idempotency_key is not None:
            self.last_idempotency_key = idempotency_key
        if (recipient, idempotency_key) not in self.emails_sent:
            asyncio.create_task(
                self.wait_and_append(recipient, idempotency_key)
            )

    async def is_email_with_idempotency_key_sent_to_recipient(
        self,
        recipient: str,
        domain: str,
        idempotency_key: str,
    ) -> bool:
        return self.emails_sent.count((recipient, idempotency_key)) == 1
