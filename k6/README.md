Install K6 from https://grafana.com/docs/k6/latest/set-up/install-k6/
Once installed can run the command 

k6 run k6-script.js 

The output from my run is added below:

```

         /\      Grafana   /‾‾/  
    /\  /  \     |\  __   /  /   
   /  \/    \    | |/ /  /   ‾‾\ 
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/ 

     execution: local
        script: k6-script-2.js
        output: -

     scenarios: (100.00%) 1 scenario, 50 max VUs, 15m30s max duration (incl. graceful stop):
              * random_requests: 50.00 iterations/s for 15m0s (maxVUs: 10-50, gracefulStop: 30s)

WARN[0003] Insufficient VUs, reached 50 active VUs and cannot initialize more  executor=constant-arrival-rate scenario=random_requests

     ✓ login status is 200
     ✗ get items status is 200
      ↳  0% — ✓ 0 / ✗ 3351
     ✓ get users status is 200
     ✗ create user status is 201
      ↳  4% — ✓ 143 / ✗ 3016
     ✗ place order status is 201
      ↳  19% — ✓ 649 / ✗ 2643
     ✗ place order duration is ok
      ↳  98% — ✓ 3232 / ✗ 60
     ✓ add item status is 201

     checks.........................: 60.32% 13788 out of 22858
     data_received..................: 34 MB  38 kB/s
     data_sent......................: 2.3 MB 2.5 kB/s
     dropped_iterations.............: 25434  28.158851/s
     http_req_blocked...............: avg=6.88ms   min=208ns    med=1.16µs   max=1.2s     p(90)=1.76µs   p(95)=1.95µs  
     http_req_connecting............: avg=2.19ms   min=0s       med=0s       max=265.34ms p(90)=0s       p(95)=0s      
   ✓ http_req_duration..............: avg=274.04ms min=224.16ms med=259.92ms max=2.14s    p(90)=339.38ms p(95)=355.3ms 
       { expected_response:true }...: avg=268.04ms min=226.67ms med=260.77ms max=2.14s    p(90)=288.63ms p(95)=343.03ms
   ✗ http_req_failed................: 46.04% 9010 out of 19566
     http_req_receiving.............: avg=685.12µs min=19.51µs  med=116.14µs max=239.73ms p(90)=2.51ms   p(95)=4.99ms  
     http_req_sending...............: avg=211.6µs  min=26.99µs  med=141.49µs max=1.34s    p(90)=206.45µs p(95)=229.48µs
     http_req_tls_handshaking.......: avg=4.49ms   min=0s       med=0s       max=526.16ms p(90)=0s       p(95)=0s      
     http_req_waiting...............: avg=273.14ms min=223.94ms med=259.17ms max=2.14s    p(90)=338.26ms p(95)=354.25ms
     http_reqs......................: 19566  21.662188/s
     iteration_duration.............: avg=2.28s    min=1.22s    med=2.26s    max=4.47s    p(90)=3.27s    p(95)=3.33s   
     iterations.....................: 19566  21.662188/s
     vus............................: 4      min=4              max=50
     vus_max........................: 50     min=30             max=50


running (15m03.2s), 00/50 VUs, 19566 complete and 0 interrupted iterations
random_requests ✓ [======================================] 00/50 VUs  15m0s  50.00 iters/s

```

Result of running after Jaeger setup:

```

         /\      Grafana   /‾‾/  
    /\  /  \     |\  __   /  /   
   /  \/    \    | |/ /  /   ‾‾\ 
  /          \   |   (  |  (‾)  |
 / __________ \  |_|\_\  \_____/ 

     execution: local
        script: k6-script-2.js
        output: -

     scenarios: (100.00%) 1 scenario, 50 max VUs, 15m30s max duration (incl. graceful stop):
              * random_requests: 50.00 iterations/s for 15m0s (maxVUs: 10-50, gracefulStop: 30s)

WARN[0003] Insufficient VUs, reached 50 active VUs and cannot initialize more  executor=constant-arrival-rate scenario=random_requests

     ✗ get items status is 200
      ↳  0% — ✓ 0 / ✗ 3206
     ✓ add item status is 201
     ✓ get users status is 200
     ✗ create user status is 201
      ↳  0% — ✓ 0 / ✗ 3289
     ✓ login status is 200
     ✗ place order status is 201
      ↳  20% — ✓ 658 / ✗ 2626
     ✗ place order duration is ok
      ↳  97% — ✓ 3192 / ✗ 92

     checks.........................: 59.71% 13657 out of 22870
     data_received..................: 35 MB  39 kB/s
     data_sent......................: 2.3 MB 2.5 kB/s
     dropped_iterations.............: 25414  28.137197/s
     http_req_blocked...............: avg=6.68ms   min=209ns    med=1.16µs   max=1.14s    p(90)=1.81µs   p(95)=2.01µs  
     http_req_connecting............: avg=2.16ms   min=0s       med=0s       max=267.05ms p(90)=0s       p(95)=0s      
   ✓ http_req_duration..............: avg=281.55ms min=226.14ms med=265.89ms max=2.41s    p(90)=352.71ms p(95)=373.45ms
       { expected_response:true }...: avg=273.75ms min=227.63ms med=265.7ms  max=1.87s    p(90)=299.93ms p(95)=353.76ms
   ✗ http_req_failed................: 46.56% 9121 out of 19586
     http_req_receiving.............: avg=797.89µs min=18.67µs  med=116.18µs max=729.38ms p(90)=4.22ms   p(95)=5.23ms  
     http_req_sending...............: avg=188µs    min=25.18µs  med=145.81µs max=800.22ms p(90)=215.22µs p(95)=239.58µs
     http_req_tls_handshaking.......: avg=4.33ms   min=0s       med=0s       max=576.4ms  p(90)=0s       p(95)=0s      
     http_req_waiting...............: avg=280.57ms min=225.53ms med=265.08ms max=2.41s    p(90)=351.41ms p(95)=372.34ms
     http_reqs......................: 19586  21.684707/s
     iteration_duration.............: avg=2.28s    min=1.22s    med=2.26s    max=5.41s    p(90)=3.27s    p(95)=3.34s   
     iterations.....................: 19586  21.684707/s
     vus............................: 3      min=3              max=50
     vus_max........................: 50     min=30             max=50


running (15m03.2s), 00/50 VUs, 19586 complete and 0 interrupted iterations
random_requests ✓ [======================================] 00/50 VUs  15m0s  50.00 iters/s
```