import { Footer } from "Footer";
import HomePage from "HomePage";
import { Product } from "Product";
import { useEffect, useRef, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { Cart } from "./Cart";
import { Header } from "./Header";
import { useCart } from "./gen/boutique/v1/demo_rsm_react";
import "./static/styles/cart.css";
import "./static/styles/order.css";
import "./static/styles/styles.css";

const CART_ACTOR_ID = "my-cart";

const useChaosMonkey = (aborted: unknown | undefined) => {
  const [chaosMonkeyRestarts, setChaosMonkeyRestarts] = useState(0);
  const previousAbortedState = useRef<unknown | undefined>();

  if (previousAbortedState.current === undefined && aborted !== undefined) {
    previousAbortedState.current = aborted;
  }
  if (previousAbortedState.current !== undefined && aborted === undefined) {
    setChaosMonkeyRestarts(chaosMonkeyRestarts + 1);
    previousAbortedState.current = undefined;
  }

  return chaosMonkeyRestarts;
};

function App() {
  const [userCurrency, setUserCurrency] = useState("USD");
  const [currencies, setCurrencies] = useState(["USD"]);

  const { useGetItems } = useCart({ id: CART_ACTOR_ID });

  useEffect(() => {
    fetch(
      `${process.env.REACT_APP_REBOOT_RESEMBLE_ENDPOINT}/get_supported_currencies`
    )
      .then((res) => res.json())
      .then((json: { currencyCodes: string[] }) =>
        setCurrencies(json.currencyCodes)
      )
      .catch((error: unknown) => console.log(error));
  }, []);

  const { response, aborted } = useGetItems();

  const chaosMonkeyRestarts = useChaosMonkey(aborted);

  return (
    <>
      <Header
        frontendMessage={null}
        showCurrency={true}
        userCurrency={userCurrency}
        setUserCurrency={setUserCurrency}
        currencies={currencies}
        chaosMonkeyRestarts={chaosMonkeyRestarts}
        cartSize={response === undefined ? 0 : response.items.length}
      />
      <Routes>
        <Route index element={<HomePage userCurrency={userCurrency} />} />
        <Route
          path="product/:productId"
          element={
            <Product cartId={CART_ACTOR_ID} userCurrency={userCurrency} />
          }
        />
        <Route
          path="cart"
          element={<Cart cartId={CART_ACTOR_ID} userCurrency={userCurrency} />}
        />
      </Routes>
      <Footer />
    </>
  );
}

export default App;
