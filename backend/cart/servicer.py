import os
import time
import uuid
from datetime import timedelta
from jinja2 import Environment, FileSystemLoader, select_autoescape
from microservices_demo.api import demo_pb2
from microservices_demo.api.demo_rsm import Cart, Emailer
# Import the whole `mailgun` module, and not only the
# `mailgun.send_email_idempotently` method, so that tests can still
# mock `mailgun.send_email_idempotently` for us.
from microservices_demo.backend.helpers import mailgun
from resemble.aio.contexts import ReaderContext, WriterContext
from typing import Optional


class CartServicer(Cart.Interface):

    async def AddItem(
        self,
        context: WriterContext,
        state: demo_pb2.CartState,
        request: demo_pb2.AddItemRequest,
    ) -> Cart.AddItemEffects:

        now = int(time.time())

        request.item.added_at = now
        state.items.append(request.item)

        email_reminder_task = self.schedule(
            timedelta(minutes=2.),
        ).EmailReminderTask(
            context,
            time_of_item_add=now,
        )

        return Cart.AddItemEffects(
            response=demo_pb2.Empty(),
            state=state,
            tasks=[
                email_reminder_task,
            ]
        )

    async def GetItems(
        self,
        context: ReaderContext,
        state: demo_pb2.CartState,
        request: demo_pb2.GetItemsRequest,
    ) -> demo_pb2.GetItemsResponse:
        return demo_pb2.GetItemsResponse(items=state.items)

    async def EmptyCart(
        self,
        context: WriterContext,
        state: demo_pb2.CartState,
        request: demo_pb2.EmptyCartRequest,
    ) -> demo_pb2.Empty:
        del state.items[:]
        return Cart.EmptyCartEffects(
            response=demo_pb2.Empty(),
            state=state,
        )

    async def EmailReminderTask(
        self,
        context: WriterContext,
        state: demo_pb2.CartState,
        request: demo_pb2.EmailReminderTaskRequest,
    ) -> demo_pb2.EmailReminderTaskResponse:
        if (len(state.items) != 0):
            last_item_added_at = max([item.added_at for item in state.items])

            if request.time_of_item_add == last_item_added_at:
                await self._send_email_reminder(context, str(uuid.uuid4()))

        return Cart.EmailReminderTaskEffects(
            response=demo_pb2.EmailReminderTaskResponse(),
            state=state,
        )

    async def _send_email_reminder(
        self, context: WriterContext, mail_id: str
    ) -> None:
        # Use a template in the 'templates' folder.
        env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), 'templates')
            ),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template('cart_reminder.html')
        confirmation = template.render()

        await mailgun.Mailgun(
            os.environ['MAILGUN_API_KEY'].strip(),
        ).send_email_idempotently(
            sender='hipsterstore@reboot.dev',
            recipient='team@reboot.dev',
            subject='You still have items in your cart.',
            domain='reboot.dev',
            idempotency_key=mail_id,
            body=confirmation,
            body_type='html',
        )
