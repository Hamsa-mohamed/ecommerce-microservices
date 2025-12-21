import { useEffect, useState } from "react";

function App() {
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    fetch("http://localhost:30003/orders")
      .then(res => res.json())
      .then(data => setOrders(data))
      .catch(err => console.error(err));
  }, []);

  return (
    <div style={{ padding: "20px", fontFamily: "Arial" }}>
      <h1>📦 Order Tracking Dashboard</h1>

      <ul>
        {orders.map(order => (
          <li key={order.id}>
            Order #{order.id} - <b>{order.status}</b>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default App;
