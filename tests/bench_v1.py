"""Benchmark the original Fraymus_Sovereign_Prime.html using its own functions.

Usage: python3 tests/bench_v1.py path/to/Fraymus_Sovereign_Prime.html [trials]
"""
import asyncio, json, pathlib, sys
from _browser import open_page

PASS, USER = "CorrectHorse!42", "alice"

async def main(path, trials):
    async with open_page() as page:
        await page.goto(pathlib.Path(path).resolve().as_uri())
        await page.wait_for_timeout(1000)

        await page.fill("#blueUser", USER)
        await page.fill("#bluePass", PASS)
        await page.click("text=GENERATE LOCK")
        await page.wait_for_function("document.getElementById('redInput').value.length>0", timeout=120000)
        await page.click("text=EXECUTE BREACH")
        await page.wait_for_function("/BREACH|FAILURE/.test(document.getElementById('redOutput').innerText)", timeout=300000)
        log = await page.inner_text("#systemLog")
        print("=== UI log ===\n" + log)
        print("password halves visible in log:", PASS[:7] in log and PASS[7:] in log)

        res = await page.evaluate("""async (T) => {
          const out = [];
          for (let i = 0; i < T; i++) {
            const u = 'user' + i, p = 'pw' + Math.random().toString(36).slice(2, 12), m = Math.floor(p.length / 2);
            let t = performance.now();
            const a = await system.textToPrime(u + p.slice(0, m) + '_A'), b = await system.textToPrime(u + p.slice(m) + '_B');
            const gen = performance.now() - t, N = a * b;
            t = performance.now();
            const f = await system.pollardsRho(N);
            out.push({ gen: Math.round(gen), ms: Math.round(performance.now() - t), Nbits: N.toString(2).length,
                       result: f === null ? 'TIMEOUT' : ((f === a || f === b) ? 'OK' : 'WRONG') });
          }
          return out;
        }""", trials)
        for r in res:
            print(json.dumps(r))
        ok = [r for r in res if r["result"] == "OK"]
        med = lambda x: sorted(x)[len(x) // 2] if x else None
        print(f"SUMMARY v1: {len(ok)}/{len(res)} factored, timeouts {sum(r['result'] == 'TIMEOUT' for r in res)}, "
              f"lock gen median {med([r['gen'] for r in res])} ms, factor median {med([r['ms'] for r in ok])} ms")

        g = await page.evaluate("""async ([u, real]) => {
          const lock = async p => { const k = Math.floor(p.length / 2);
            return (await system.textToPrime(u + p.slice(0, k) + '_A')) * (await system.textToPrime(u + p.slice(k) + '_B')); };
          const N = await lock(real), guesses = ['password', 'letmein', '123456', 'CorrectHorse!41', real];
          const t = performance.now(); let hit = -1;
          for (let i = 0; i < guesses.length; i++) if (await lock(guesses[i]) === N) { hit = i + 1; break; }
          return { hit_on_guess: hit, ms: Math.round(performance.now() - t) };
        }""", [USER, PASS])
        print("GUESS ATTACK v1:", json.dumps(g))

if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 20))
