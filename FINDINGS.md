# Findings: v1 audit and v2 changes

Source audited: [`Fraymus_Sovereign_Prime.html`](https://github.com/eyeoverthink/java-memory-V1/blob/main/Fraymus_Sovereign_Prime.html) and [`FRAYMUS_PRIME_MANIFEST.md`](https://github.com/eyeoverthink/java-memory-V1/blob/main/FRAYMUS_PRIME_MANIFEST.md), commit `630a19f` (2026-02-16).

Every number below was measured by running the page's own functions in Chrome 137. Raw output is in [`tests/results/`](tests/results).

## The screenshot that started this

The original run produced this lock and factor:

- Lock `28861027409913973808187683789`
- Factor `61471746272869`, found in 7.1 s

The arithmetic checks out: `28861027409913973808187683789 = 61471746272869 × 469500691940681`.

That is a 95-bit lock made from a 46-bit and a 49-bit prime. The breach found a real factor. It succeeded because the smaller prime happened to be small for this page.

## v1 problems, in order of importance

1. **The password was shown on screen.** The log printed `DNA A Encoded: <user><first half of password>_A` and the same for B. Anyone looking at the screen, or at a screenshot of it, could read the full password.
2. **The breach usually failed.** v1 caps every prime below 2⁵⁰ and stops Pollard's rho after 5,000,000 cycles. Finding a 48–50-bit factor needs about 21–42 million steps, so most runs time out. In a 20-lock batch run, 5 of 20 locks were factored and 15 timed out after about 20–40 s each (an earlier identical run: 1 of 20).
3. **Guessing the password beats factoring.** The lock is a fixed function of username and password, so an attacker can rebuild it from each guess and compare. In v1 this found a test password on guess 5 in 354 ms, with no factoring at all.
4. **"Identity Verified" could not fail.** The Purple Team re-hashed the DNA strings the page already held in memory and compared them to the factor. That proves nothing about where the lock came from. A factor never recovers the password, because SHA-256 can't be reversed.
5. **Splitting the password helped the attacker.** Each prime came from half the password. Once N is factored, each half can be guessed separately, so the search is half as long, which is exponentially easier.
6. **Mislabelled parts.**
   - "Quantum Sieve" is classical Pollard's rho.
   - The "Rule 30" visual used the update table `[0,1,1,1,1,0,0,0][7-idx]`, which is Rule 120.
   - "Quantum Coherence 100%" and "Evolution 1.00" were fixed strings that nothing ever updated.
7. **Prime test by trial division.** `isPrime` divided by every odd number up to √n, which is up to 16 million BigInt divisions per prime candidate. This made lock generation slow (62 ms median). The cost had nothing to do with security.

## Manifest claims vs measurement

| Claim in `FRAYMUS_PRIME_MANIFEST.md` | Measured |
|---|---|
| Example `LOCK: 1267650600228229401496703205376` | That number is exactly 2¹⁰⁰. It can't be a product of two odd primes, and the listed factor `35604928818740881` doesn't divide it. |
| "50 bits: ~50,000 cycles, 30–100 ms, 100% success" | 50-bit primes need about 42M steps. In v1: 5 of 20 locks were factored and 15 timed out after about 20–40 s each (an earlier identical run: 1 of 20). |
| "Pollard's Rho completes in <100ms for 50-bit semiprimes" | The original screenshot took 7.1 s, and that was one of the lucky runs. |

## What v2 changes

| Area | v1 | v2 |
|---|---|---|
| Credentials on screen | Password halves logged | Never logged; password field cleared after use; page text checked by test |
| Prime derivation | `SHA-256(user + half password + "_A")` mod 2⁵⁰ | `SHA-256("fraymus-prime-v2|A|" + user + "|" + full password)`, top *k* bits, exact bit length |
| Prime test | Trial division | Miller-Rabin, 13 bases, deterministic below 3.3 × 10²⁴ |
| Factoring | Floyd rho, gcd every step, 5M cycle cap | Brent rho, gcd per 256 steps, up to 16 restarts, budget selectable (10M / 50M / 200M) |
| Prime size | Fixed below 2⁵⁰ | Selectable 32 / 40 / 48 / 56 / 64 bits, labelled with the expected effort |
| Verification | "IDENTITY VERIFIED" | "Factor matches stored prime A/B. This does not recover the password." |
| Password guessing | Not shown | Gold Team panel, with per-guess timing |
| Cellular automaton | Rule 120 labelled Rule 30 | Rule 30, checked against a Python reference |
| Log rendering | `innerHTML` with user input | `textContent` only |

## v2 test results

| Check | Result |
|---|---|
| Miller-Rabin vs Python reference, 3,010 numbers (incl. Carmichael numbers, strong pseudoprimes) | 0 mismatches |
| Rule 30, 50 generations vs Python reference | match |
| Generated primes: exact bit length and prime (100 samples, 32–64 bits) | all pass |
| Credential text anywhere on page after the full UI flow | none |
| 32-bit primes | 20 / 20 factored, median 8 ms, max 20 ms, median 0.10M steps (theory 0.08M) |
| 40-bit primes | 20 / 20 factored, median 386 ms, max 921 ms, median 1.58M steps (theory 1.31M) |
| 48-bit primes | 10 / 10 factored, median 7.7 s, max 13.5 s, median 26.8M steps (theory 21.0M) |
| JS errors | none |

## What is still true in v2, on purpose

- **Fast guessing is the point of the demo.** v2 makes a lock in about 2 ms, so each guess is cheap (0.18 ms per guess). That is the lesson of the Gold Team panel, and it's the reason real systems use slow, salted password hashes.
- **The sizes are toys.** The largest option, 64-bit primes, makes a 128-bit N, and Pollard's rho can't factor that in a browser. Real RSA moduli are 2048 bits or more.
