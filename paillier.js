// static/paillier.js  ← FINAL WORKING VERSION (matches app.js perfectly)

const Paillier = (() => {
    // Fast modular exponentiation for BigInt
    function modPow(base, exp, mod) {
        let result = 1n;
        base = base % mod;
        while (exp > 0n) {
            if (exp & 1n) {
                result = (result * base) % mod;
            }
            base = (base * base) % mod;
            exp >>= 1n;
        }
        return result;
    }

    // Generate random r where 1 < r < n
    function getRandomR(n) {
        const byteLength = (n.toString(2).length + 7) >> 3;
        let r;
        do {
            const bytes = new Uint8Array(byteLength + 4);
            crypto.getRandomValues(bytes);
            r = 0n;
            for (const b of bytes) {
                r = (r << 8n) | BigInt(b);
            }
            r = r % n;
        } while (r <= 1n);
        return r;
    }

    // Public encrypt function used by app.js
    return {
        encrypt: function (m, n) {
            const nn = n * n;           // n²
            const g = n + 1n;           // g = n+1 (standard Paillier)
            const r = getRandomR(n);    // random blinding factor

            // c = g^m * r^n mod n²
            const c = (modPow(g, BigInt(m), nn) * modPow(r, n, nn)) % nn;

            return {
                ciphertext: c.toString(10),  // string so it's safe in JSON
                exponent: 0                  // always 0 in standard Paillier
            };
        }
    };
})();