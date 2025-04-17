import time
from boutique.v1 import demo_pb2
from boutique.v1.demo_rbt import Cart
from reboot.aio.auth.authorizers import allow
from reboot.aio.contexts import ReaderContext, WriterContext


class CartServicer(Cart.Servicer):

    def authorizer(self):
        return allow()

    async def AddItem(
        self,
        context: WriterContext,
        state: Cart.State,
        request: demo_pb2.AddItemRequest,
    ) -> demo_pb2.Empty:

        now = int(time.time())

        # If the item was already in the cart, increase the count instead of
        # adding it again.
        previous_item = next(
            (
                item for item in state.items
                if item.product_id == request.item.product_id
            ),
            None,
        )
        if previous_item is not None:
            previous_item.quantity += request.item.quantity
            previous_item.added_at = now
        else:
            request.item.added_at = now
            state.items.append(request.item)

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
