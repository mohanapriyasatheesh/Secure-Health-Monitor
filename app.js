// static/app.js  ← THIS IS THE FINAL WORKING VERSION
let n = null;

async function loadPublicKey() {
    const resp = await fetch('/pubkey');
    const data = await resp.json();
    n = BigInt(data.n);
    console.log("Public key loaded:", n.toString().slice(0, 50) + "...");
}

document.addEventListener('DOMContentLoaded', async () => {
    await loadPublicKey();

    const form = document.getElementById('readingForm');
    const resetBtn = document.getElementById('resetBtn');

    // THIS IS THE EXACT WORKING SUBMIT CODE
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log("Submit button clicked!");

        const hr = document.getElementById('heart_rate').value.trim();
        const spo2 = document.getElementById('spo2').value.trim();
        const temp = document.getElementById('temperature').value.trim();

        const readings = [
            { type: "heart_rate", value: hr },
            { type: "spo2", value: spo2 },
            { type: "temperature", value: temp }
        ];

        for (const reading of readings) {
            if (!reading.value) continue;

            const scale = reading.type === "temperature" ? 10 : 1;
            const plainNumber = Math.round(parseFloat(reading.value) * scale);

            const encrypted = Paillier.encrypt(plainNumber, n);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        type: reading.type,
                        ciphertext: encrypted.ciphertext,
                        exponent: encrypted.exponent
                    })
                });

                if (response.ok) {
                    console.log(`Sent ${reading.type}: ${reading.value}`);
                } else {
                    console.error("Server error:", await response.text());
                }
            } catch (err) {
                console.error("Send failed:", err);
            }
        }

        // Clear form
        document.getElementById('heart_rate').value = '';
        document.getElementById('spo2').value = '';
        document.getElementById('temperature').value = '';

        updateTable();  // Refresh immediately
    });

    resetBtn.addEventListener('click', () => {
        fetch('/reset', { method: 'POST' }).then(updateTable);
    });

    updateTable();
    setInterval(updateTable, 3000);
});

async function updateTable() {
    try {
        const resp = await fetch('/status');
        const data = await resp.json();

        let html = `<table class="table table-striped">
            <thead class="table-dark">
                <tr><th>Metric</th><th>Readings</th><th>Average</th><th>Status</th></tr>
            </thead><tbody>`;

        const names = { heart_rate: "Heart Rate", spo2: "SpO₂", temperature: "Temperature" };
        for (const key of ['heart_rate', 'spo2', 'temperature']) {
            const d = data[key] || { count: 0, avg: null, status: "No data" };
            const avg = d.avg !== null ? d.avg : "—";
            const statusClass = d.status === "ABNORMAL" ? "text-danger fw-bold" : "text-success";
            html += `<tr>
                <td>${names[key]}</td>
                <td>${d.count}</td>
                <td>${avg}</td>
                <td class="${statusClass}">${d.status}</td>
            </tr>`;
        }
        html += `</tbody></table>`;
        document.getElementById('status').innerHTML = html;
    } catch (e) {
        document.getElementById('status').innerHTML = "<p class='text-danger'>Server offline</p>";
    }
}