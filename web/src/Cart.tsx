import { PastOrders } from "PastOrders";
import {
  Address,
  CreditCardInfo,
  GetQuoteResponse,
  Money,
  ShippingQuote,
} from "gen/demo_pb";
import {
  Cart as CartActor,
  Checkout,
  ProductCatalog,
  Shipping,
} from "gen/demo_rsm";
import {
  ProductItem,
  convertedShippingCost,
  renderMoney,
  totalOrderCost,
  useCurrencyConvertProductItems,
} from "helpers";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

const USER_ADDRESS = new Address({
  streetAddress: "1600 Amphitheatre Pkwy",
  city: "Mountain View",
  state: "CA",
  zipCode: 94043,
  country: "USA",
});

interface CartProps {
  cartActorId: string;
  userCurrency: string;
}

export const Cart = ({ cartActorId, userCurrency }: CartProps) => {
  const [productItems, setProductItems] = useState<ProductItem[]>([]);
  const [shippingCost, setShippingCost] = useState<Money>(new Money());
  const [shippingQuote, setShippingQuote] = useState<ShippingQuote>();
  const [email, setEmail] = useState("someone@example.com");
  const { GetProduct } = ProductCatalog({ Id: "product-catalog" });
  const { GetQuote } = Shipping({ Id: "shipping" });
  const { useOrders } = Checkout({ Id: "checkout" });
  const { useGetItems, EmptyCart } = CartActor({
    Id: cartActorId,
  });

  const {
    response: useOrdersResponse,
    mutations: { PlaceOrder },
    pendingPlaceOrderMutations,
  } = useOrders();

  const { response: useGetItemsResponse } = useGetItems();

  useEffect(() => {
    if (useGetItemsResponse !== undefined) {
      for (const cartItem of useGetItemsResponse.items) {
        const product = GetProduct({ id: cartItem.productId });

        product.then((productDetails) => {
          if (productDetails !== undefined && cartItem !== undefined) {
            if (
              !productItems.some(
                (productItem: ProductItem) =>
                  productItem.product.id === productDetails.id
              )
            ) {
              setProductItems((productItems) => [
                ...productItems,
                { product: productDetails, item: cartItem },
              ]);
            }
          }
        });
      }

      const quote = GetQuote({
        address: USER_ADDRESS,
        items: useGetItemsResponse.items,
        quoteExpirationSeconds: 5000,
      });
      quote.then((quoteDetails: GetQuoteResponse) => {
        if (quoteDetails !== undefined) {
          if (quoteDetails.quote !== undefined) {
            setShippingQuote(quoteDetails.quote);
            if (quoteDetails.quote.cost !== undefined) {
              convertedShippingCost(quoteDetails.quote.cost, userCurrency).then(
                (cost: Money) => {
                  setShippingCost(cost);
                }
              );
            }
          }
        }
      });
    }
  }, [useGetItemsResponse, userCurrency]);

  const convertedProductItems = useCurrencyConvertProductItems(
    productItems,
    userCurrency
  );

  if (useGetItemsResponse === undefined) return <>Loading...</>;
  const totalCost = totalOrderCost(
    convertedProductItems,
    shippingCost,
    userCurrency
  );

  const placeOrder = async () => {
    // This error is an error that we know about in the backend.
    // For any other error type, just throw.
    const { error } = await PlaceOrder(
      {
        userId: cartActorId,
        userCurrency: userCurrency,
        address: USER_ADDRESS,
        creditCard: new CreditCardInfo({
          creditCardNumber: "ddd",
          creditCardCvv: 389,
          creditCardExpirationYear: 2025,
          creditCardExpirationMonth: 9,
        }),
        quote: shippingQuote,
        email,
      },
      { convertedProductItems }
    );
    if (error !== undefined) {
      console.log(error);
    }
  };

  return (
    <>
      <div className="local">
        <span className="platform-flag">local</span>
      </div>
      <main role="main" className="cart-sections">
        {useGetItemsResponse.items.length === 0 ? (
          <section className="empty-cart-section">
            <h3>Your shopping cart is empty!</h3>
            <p>Items you add to your shopping cart will appear here.</p>
            <Link className="cymbal-button-primary" to="/" role="button">
              Continue Shopping
            </Link>
          </section>
        ) : (
          <section className="container">
            <div className="row">
              <div className="col-lg-6 col-xl-5 offset-xl-1 cart-summary-section">
                <div className="row mb-3 py-2">
                  <div className="col-4 pl-md-0">
                    <h3>Cart ({useGetItemsResponse.items.length})</h3>
                  </div>
                  <div className="col-8 pr-md-0 text-right">
                    <button
                      className="cymbal-button-secondary cart-summary-empty-cart-button"
                      onClick={EmptyCart}
                    >
                      Empty Cart
                    </button>
                    <Link
                      className="cymbal-button-primary"
                      to="/"
                      role="button"
                    >
                      Continue Shopping
                    </Link>
                  </div>
                </div>
                {convertedProductItems.map((productItem: ProductItem) => (
                  <div
                    className="row cart-summary-item-row"
                    key={productItem.product.id}
                  >
                    <div className="col-md-4 pl-md-0">
                      <Link to={`/product/${productItem.item.productId}`}>
                        <img
                          className="img-fluid"
                          alt=""
                          src={productItem.product.picture}
                        />
                      </Link>
                    </div>
                    <div className="col-md-8 pr-md-0">
                      <div className="row">
                        <div className="col">
                          <h4>{productItem.product.name}</h4>
                        </div>
                      </div>
                      <div className="row cart-summary-item-row-item-id-row">
                        <div className="col">SKU #{productItem.product.id}</div>
                      </div>
                      <div className="row">
                        <div className="col">
                          Quantity: {productItem.item.quantity}
                        </div>
                        <div className="col pr-md-0 text-right">
                          <strong>
                            {renderMoney(productItem.product.price)}
                          </strong>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
                <div className="row cart-summary-shipping-row">
                  <div className="col pl-md-0">Shipping</div>
                  <div className="col pr-md-0 text-right">
                    {renderMoney(shippingCost)}
                  </div>
                </div>
                <div className="row cart-summary-total-row">
                  <div className="col pl-md-0">Total</div>
                  <div className="col pr-md-0 text-right">
                    {renderMoney(totalCost)}
                  </div>
                </div>
              </div>
              <div className="col-lg-5 offset-lg-1 col-xl-4">
                <div className="cart-checkout-form">
                  <div className="row">
                    <div className="col">
                      <h3>Shipping Address</h3>
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="col cymbal-form-field">
                      <label htmlFor="email">E-mail Address</label>
                      <input
                        type="email"
                        id="email"
                        name="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                      />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="col cymbal-form-field">
                      <label htmlFor="street_address">Street Address</label>
                      <input
                        type="text"
                        name="street_address"
                        id="street_address"
                        value="1600 Amphitheatre Parkway"
                        readOnly
                        required
                      />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="col cymbal-form-field">
                      <label htmlFor="zip_code">Zip Code</label>
                      <input
                        type="text"
                        name="zip_code"
                        id="zip_code"
                        value="94043"
                        required
                        readOnly
                        pattern="\d{4,5}"
                      />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="col cymbal-form-field">
                      <label htmlFor="city">City</label>
                      <input
                        type="text"
                        name="city"
                        id="city"
                        readOnly
                        value="Mountain View"
                        required
                      />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="col-md-5 cymbal-form-field">
                      <label htmlFor="state">State</label>
                      <input
                        type="text"
                        name="state"
                        id="state"
                        readOnly
                        value="CA"
                        required
                      />
                    </div>
                    <div className="col-md-7 cymbal-form-field">
                      <label htmlFor="country">Country</label>
                      <input
                        type="text"
                        id="country"
                        placeholder="Country Name"
                        name="country"
                        value="United States"
                        readOnly
                        required
                      />
                    </div>
                  </div>
                  <div className="row">
                    <div className="col">
                      <h3 className="payment-method-heading">Payment Method</h3>
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="col cymbal-form-field">
                      <label htmlFor="credit_card_number">
                        Credit Card Number
                      </label>
                      <input
                        type="text"
                        id="credit_card_number"
                        name="credit_card_number"
                        placeholder="0000-0000-0000-0000"
                        value="4432-8015-6152-0454"
                        readOnly
                        required
                        pattern="\d{4}-\d{4}-\d{4}-\d{4}"
                      />
                    </div>
                  </div>
                  <div className="form-row">
                    <div className="col-md-5 cymbal-form-field">
                      <label htmlFor="credit_card_expiration_month">
                        Month
                      </label>
                      <select
                        name="credit_card_expiration_month"
                        id="credit_card_expiration_month"
                      >
                        <option value="1">January</option>
                        <option value="2">February</option>
                        <option value="3">March</option>
                        <option value="4">April</option>
                        <option value="5">May</option>
                        <option value="6">June</option>
                        <option value="7">July</option>
                        <option value="8">August</option>
                        <option value="9">September</option>
                        <option value="10">October</option>
                        <option value="11">November</option>
                        <option value="12">January</option>
                      </select>
                      <img
                        src="/static/icons/Hipster_DownArrow.svg"
                        alt=""
                        className="cymbal-dropdown-chevron"
                      />
                    </div>
                    <div className="col-md-4 cymbal-form-field">
                      <label htmlFor="credit_card_expiration_year">Year</label>
                      <select
                        name="credit_card_expiration_year"
                        id="credit_card_expiration_year"
                      ></select>
                      <img
                        src="/static/icons/Hipster_DownArrow.svg"
                        alt=""
                        className="cymbal-dropdown-chevron"
                      />
                    </div>
                    <div className="col-md-3 cymbal-form-field">
                      <label htmlFor="credit_card_cvv">CVV</label>
                      <input
                        type="password"
                        id="credit_card_cvv"
                        name="credit_card_cvv"
                        value="672"
                        required
                        readOnly
                        pattern="\d{3}"
                      />
                    </div>
                  </div>
                  <div className="form-row justify-content-center">
                    <div className="col text-center">
                      <button
                        className="cymbal-button-primary"
                        onClick={placeOrder}
                        disabled={pendingPlaceOrderMutations.length > 0}
                      >
                        Place Order
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}
        <PastOrders
          getProduct={GetProduct}
          response={useOrdersResponse}
          userCurrency={userCurrency}
          pendingPlaceOrderMutations={pendingPlaceOrderMutations}
        />
      </main>
    </>
  );
};
