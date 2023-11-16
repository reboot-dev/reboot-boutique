import { Footer } from "Footer";
import HomePage from "HomePage";
import { Product } from "Product";
import { useEffect, useRef, useState } from "react";
import { Route, Routes } from "react-router-dom";
import { Cart } from "./Cart";
import { Header } from "./Header";
import { Cart as CartActor } from "./gen/demo_rsm_react";
import "./static/styles/cart.css";
import "./static/styles/order.css";
import "./static/styles/styles.css";

const CART_ACTOR_ID = "my-cart";

const useChaosMonkey = (error: unknown | undefined) => {
  const [chaosMonkeyRestarts, setChaosMonkeyRestarts] = useState(0);
  const previousErrorState = useRef<unknown | undefined>();

  if (previousErrorState.current === undefined && error !== undefined) {
    previousErrorState.current = error;
  }
  if (previousErrorState.current !== undefined && error === undefined) {
    setChaosMonkeyRestarts(chaosMonkeyRestarts + 1);
    previousErrorState.current = undefined;
  }

  return chaosMonkeyRestarts;
};

function App() {
  const [userCurrency, setUserCurrency] = useState("USD");
  const [currencies, setCurrencies] = useState(["USD"]);

  const { useGetItems } = CartActor({
    id: CART_ACTOR_ID,
  });

  useEffect(() => {
    fetch("https://localhost.direct:9991/get_supported_currencies")
      .then((res) => res.json())
      .then((json: { currencyCodes: string[] }) =>
        setCurrencies(json.currencyCodes)
      )
      .catch((error: unknown) => console.log(error));
  }, []);

  const { response, error } = useGetItems();

  const chaosMonkeyRestarts = useChaosMonkey(error);

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
