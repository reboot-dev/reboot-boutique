import time
from boutique.v1 import demo_pb2
from boutique.v1.demo_rsm import Cart
from resemble.aio.contexts import ReaderContext, WriterContext


class CartServicer(Cart.Interface):

    async def AddItem(
        self,
        context: WriterContext,
        state: Cart.State,
        request: demo_pb2.AddItemRequest,
    ) -> demo_pb2.Empty:

        now = int(time.time())

        request.item.added_at = now
        state.items.append(request.item)

        # Re-enable email reminder after we support tasks in transactions.
        # See https://github.com/reboot-dev/respect/issues/2550
        # email_reminder_task = await self.lookup().schedule(
        #     when=timedelta(minutes=2.),
        # ).EmailReminderTask(
        #     context,
        #     time_of_item_add=now,
        # )

        return demo_pb2.Empty()

    async def GetItems(
        self,
        context: ReaderContext,
        state: Cart.State,
        request: demo_pb2.GetItemsRequest,
    ) -> demo_pb2.GetItemsResponse:
        return demo_pb2.GetItemsResponse(items=state.items)

    async def EmptyCart(
        self,
        context: WriterContext,
        state: Cart.State,
        request: demo_pb2.EmptyCartRequest,
    ) -> demo_pb2.Empty:
        del state.items[:]
        return demo_pb2.Empty()
