import { Product as pb_Product } from "gen/demo_pb";
import { Cart as CartActor, ProductCatalog } from "gen/demo_rsm";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import {
  productToEntry,
  renderMoney,
  useCurrencyConvertProducts,
} from "./helpers";

interface ProductProps {
  cartId: string;
  userCurrency: string;
}

export const Product = ({ cartId, userCurrency }: ProductProps) => {
  let { productId } = useParams();
  const navigate = useNavigate();
  const [selectedQuantity, setSelectedQuantity] = useState("1");

  const { AddItem } = CartActor({ Id: cartId });
  const { GetProduct } = ProductCatalog({ Id: "product-catalog" });
  const [product, setProduct] = useState<pb_Product>();

  useEffect(() => {
    const response = GetProduct({ id: productId });
    response.then((product: pb_Product) => {
      setProduct(product);
    });
  }, []);

  const products = useCurrencyConvertProducts(product, userCurrency);

  if (products.length === 0) return <>Loading...</>;
  const productEntry = productToEntry(products[0]);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    try {
      await AddItem({
        item: {
          productId: productEntry.item.id,
          quantity: +selectedQuantity,
          addedAt: BigInt(Date.now()),
        },
      });
      navigate("/cart");
    } catch (e: unknown) {
      console.log(e);
    }
  };

  return (
    <>
      <div className="local">
        <span className="platform-flag">local</span>
      </div>
      <main role="main">
        <div className="h-product container">
          <div className="row">
            <div className="col-md-6">
              <img
                className="product-image"
                alt=""
                src={productEntry.item.picture}
              />
            </div>
            <div className="product-info col-md-5">
              <div className="product-wrapper">
                <h2>{productEntry.item.name}</h2>
                <p className="product-price">
                  {renderMoney(productEntry.price)}
                </p>
                <p>{productEntry.item.description}</p>

                <form onSubmit={handleSubmit}>
                  <input
                    type="hidden"
                    name="product_id"
                    value={productEntry.item.id}
                  />
                  <div className="product-quantity-dropdown">
                    <select
                      onChange={(e) => setSelectedQuantity(e.target.value)}
                      name="quantity"
                      id="quantity"
                      value={selectedQuantity}
                    >
                      <option>1</option>
                      <option>2</option>
                      <option>3</option>
                      <option>4</option>
                      <option>5</option>
                      <option>10</option>
                    </select>
                    <img src="/static/icons/Hipster_DownArrow.svg" alt="" />
                  </div>
                  <button type="submit" className="cymbal-button-primary">
                    Add To Cart
                  </button>
                </form>
              </div>
            </div>
          </div>
        </div>
      </main>
    </>
  );
};
