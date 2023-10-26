import json
import os
from google.protobuf.json_format import ParseDict
from resemble.aio.contexts import ReaderContext, WriterContext
from resemble.examples.boutique.api import demo_pb2
from resemble.examples.boutique.api.demo_rsm import ProductCatalog


class ProductCatalogServicer(ProductCatalog.Interface):

    async def LoadProducts(
        self,
        context: WriterContext,
        request: demo_pb2.Empty,
    ) -> ProductCatalog.LoadProductsEffects:
        with open(
            os.path.join(os.path.dirname(__file__), 'products.json'), 'r'
        ) as file:
            return ProductCatalog.LoadProductsEffects(
                state=ParseDict(
                    json.load(file), demo_pb2.ProductCatalogState()
                ),
                response=demo_pb2.Empty(),
            )

    async def ListProducts(
        self,
        context: ReaderContext,
        state: demo_pb2.ProductCatalogState,
        request: demo_pb2.Empty,
    ) -> demo_pb2.ListProductsResponse:
        return demo_pb2.ListProductsResponse(products=state.products)

    async def GetProduct(
        self,
        context: ReaderContext,
        state: demo_pb2.ProductCatalogState,
        request: demo_pb2.GetProductRequest,
    ) -> demo_pb2.Product:

        for product in state.products:
            if request.id == product.id:
                return product
        # TODO: get parity with original implementation by returning a
        # status code NOT_FOUND + message instead of raising a
        # ValueError.
        raise ValueError(f"No product found with ID '{request.id}'")

    async def SearchProducts(
        self,
        context: ReaderContext,
        state: demo_pb2.ProductCatalogState,
        request: demo_pb2.SearchProductsRequest,
    ) -> demo_pb2.SearchProductsResponse:
        raise NotImplementedError
