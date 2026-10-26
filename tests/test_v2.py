"""End-to-end and benchmark tests for index.html (v2).

Usage: python3 tests/test_v2.py
"""
import asyncio, json, pathlib, random, sys
from _browser import open_page
PASS='CorrectHorse!42'; USER='alice'
ROOT=pathlib.Path(__file__).resolve().parent.parent
def mr(n):
    if n<2: return False
    for p in [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71]:
        if n%p==0: return n==p
    d,s=n-1,0
    while d%2==0: d//=2; s+=1
    for _ in range(40):
        a=random.randrange(2,n-1); x=pow(a,d,n)
        if x in(1,n-1): continue
        for _ in range(s-1):
            x=x*x%n
            if x==n-1: break
        else: return False
    return True
def r30(c):
    n=len(c); return [(30>>((c[(x-1)%n]<<2)|(c[x]<<1)|c[(x+1)%n]))&1 for x in range(n)]
async def main():
    async with open_page() as page:
        errs=[]; page.on("pageerror", lambda e: errs.append(str(e))); page.on("console", lambda m: m.type=="error" and errs.append(m.text))
        await page.set_viewport_size({"width":1400,"height":1300})
        await page.goto((ROOT/"index.html").as_uri()); await page.wait_for_timeout(800)
        # --- correctness ---
        random.seed(1)
        nums=[random.getrandbits(random.choice([20,33,48,64,80]))|1 for _ in range(3000)]
        nums+= [561,1105,1729,2465,2821,6601,8911,3215031751,3825123056546413051,318665857834031151167461]
        js=await page.evaluate("ns=>ns.map(s=>FP.isPrime(BigInt(s)))",[str(n) for n in nums])
        mism=[n for n,j in zip(nums,js) if j!=mr(n)]
        print("isPrime: tested",len(nums),"primes found",sum(js),"mismatches vs Python",len(mism))
        cells=[random.getrandbits(1) for _ in range(200)]; ok=True; c=cells
        jsrows=await page.evaluate("c=>{let r=[];for(let i=0;i<50;i++){c=FP.rule30Step(c);r.push(c)}return r}",cells)
        for row in jsrows:
            c=r30(c); ok&= (c==row)
        print("rule30 50 rows match Python reference:",ok)
        lens=await page.evaluate("""async()=>{const o={};for(const b of [32,40,48,56,64]){const s=[];for(let i=0;i<20;i++){const p=await FP.hashToPrime('t'+i+'|'+b,b);s.push(p.toString(2).length+':'+p.toString())}o[b]=s}return o}""")
        bad=0
        for bits,v in lens.items():
            bl=set(int(x.split(':')[0]) for x in v); bad+=sum(not mr(int(x.split(':')[1])) for x in v)
            print(f"hashToPrime {bits}: bit lengths {sorted(bl)}")
        print("hashToPrime non-primes (Python check):",bad)
        # --- UI flow ---
        await page.fill('#blueUser',USER); await page.fill('#bluePass',PASS)
        await page.click('#btnBlue'); await page.wait_for_function("document.getElementById('redInput').value.length>0",timeout=60000)
        print("password field after lock:", repr(await page.input_value('#bluePass')))
        await page.click('#btnRed'); await page.wait_for_function("/FACTORED|Not factored/.test(document.getElementById('redOutput').innerText)",timeout=600000)
        await page.fill('#guesses', "password\nletmein\n123456\nCorrectHorse!41\n"+PASS)
        await page.click('#btnGold'); await page.wait_for_function("/MATCH|No match/.test(document.getElementById('goldOutput').innerText)",timeout=60000)
        await page.wait_for_timeout(500)
        log=await page.inner_text('#systemLog'); print("=== UI LOG ===\n"+log)
        print("RED:",await page.inner_text('#redOutput')); print("GOLD:",await page.inner_text('#goldOutput'))
        await page.fill('#guesses','')
        body=await page.evaluate("document.body.innerText")
        print("password text anywhere on page:", PASS in body, "| 'Correct' substring:", "Correct" in body, "| username in log:", USER in log)
        await page.screenshot(path=str(ROOT/"docs"/"screenshot.png"), full_page=True)
        # --- batch ---
        for bits,T in [(32,20),(40,20),(48,10)]:
            res=await page.evaluate("""async([bits,T])=>{const o=[];for(let i=0;i<T;i++){
               const p='pw'+Math.random().toString(36).slice(2,12);let t=performance.now();
               const L=await FP.makeLock('user'+i,p,bits);const gen=performance.now()-t;t=performance.now();
               const r=await FP.brentRho(L.N,200000000);const ms=performance.now()-t;
               o.push({gen,ms,steps:r.steps,ok:r.factor!==null&&(r.factor===L.a||r.factor===L.b)});}return o}""",[bits,T])
            ok=[r for r in res if r['ok']]; med=lambda x: sorted(x)[len(x)//2] if x else None
            print(f"BATCH {bits}-bit primes: {len(ok)}/{T} factored, median {med([r['ms'] for r in ok]):.0f} ms, max {max(r['ms'] for r in ok):.0f} ms, median steps {med([r['steps'] for r in ok])/1e6:.2f}M (expected {(3.14159/2*2**bits)**.5/1e6:.2f}M), lock gen median {med([r['gen'] for r in res]):.1f} ms", flush=True)
        g=await page.evaluate("""async()=>{const L=await FP.makeLock('alice','x',40);const t=performance.now();for(let i=0;i<500;i++)await FP.makeLock('alice','g'+i,40);return (performance.now()-t)/500}""")
        print(f"Guess cost at 40-bit: {g:.2f} ms per guess")
        print("JS errors:",errs)
asyncio.run(main())
