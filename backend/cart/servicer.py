import time
from resemble.aio.contexts import ReaderContext, WriterContext
from resemble.examples.boutique.api import demo_pb2
from resemble.examples.boutique.api.demo_rsm import Cart


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

        # Re-enable email reminder after we support tasks in transactions.
        # See https://github.com/reboot-dev/respect/issues/2550
        # email_reminder_task = self.schedule(
        #     timedelta(minutes=2.),
        # ).EmailReminderTask(
        #     context,
        #     time_of_item_add=now,
        # )

        return Cart.AddItemEffects(
            response=demo_pb2.Empty(),
            state=state,
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
