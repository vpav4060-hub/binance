window.addEventListener("load", () => {
    new TradingView.widget({
        width: "100%",
        height: "100%",
        symbol: "FX:EURUSD",
        interval: "1",
        theme: "dark",
        locale: "es",
        container_id: "tradingview_chart"
    });
});

function openTrade(type){
    const amount = document.getElementById("amount").value;
    if(!amount || amount <= 0) return alert("Ingrese un monto válido");

    const now = new Date().toLocaleTimeString();
    const color = type === "buy" ? "#16a34a" : "#dc2626";
    const action = type === "buy" ? "Compra" : "Venta";

    const row = `
        <tr>
            <td>${now}</td>
            <td>EUR/USD</td>
            <td>$${amount}</td>
            <td style="color:${color};">${action} en curso</td>
        </tr>
    `;

    document.getElementById("history-body").innerHTML += row;
    document.getElementById("amount").value = "";
}
