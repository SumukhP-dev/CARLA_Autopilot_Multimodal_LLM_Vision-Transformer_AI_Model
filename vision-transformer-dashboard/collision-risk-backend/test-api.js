// Quick test script to verify backend is storing advanced stats
const http = require('http');

const testData = {
  name: "TestEnv3",
  collisions: 5,
  safeRuns: 95,
  safetyRate: 95.0,
  gradeLevel: "A",
  speedStats: { mean: 5.5, std: 1.2, variance: 1.44 },
  steeringStats: { mean: 0.1, std: 0.05, variance: 0.0025 },
  fpsStats: { mean: 30.0, std: 2.0 },
  processingStats: {
    vision: { mean: 0.1 },
    audio: { mean: 0.2 },
    llm: { mean: 0.3 },
    total: { mean: 0.6 }
  },
  speedCV: 21.82,
  steeringCV: 50.0,
  totalFrames: 1000,
  avgFPS: 30.0
};

const postData = JSON.stringify(testData);

const options = {
  hostname: 'localhost',
  port: 4000,
  path: '/api/simulations',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(postData)
  }
};

console.log('Sending test data...');
const req = http.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    console.log('POST Response:', data);
    
    // Now GET the data back
    setTimeout(() => {
      http.get('http://localhost:4000/api/simulations', (getRes) => {
        let getData = '';
        getRes.on('data', (chunk) => { getData += chunk; });
        getRes.on('end', () => {
          console.log('\nGET Response (raw JSON):');
          console.log(getData);
          
          const parsed = JSON.parse(getData);
          const testEnv = parsed.find(s => s.name === 'TestEnv3');
          if (testEnv) {
            console.log('\n✓ TestEnv3 found');
            console.log('Properties:', Object.keys(testEnv));
            if (testEnv.speedStats) {
              console.log('✓ speedStats present:', JSON.stringify(testEnv.speedStats));
            } else {
              console.log('✗ speedStats missing');
            }
          } else {
            console.log('✗ TestEnv3 not found');
          }
        });
      });
    }, 500);
  });
});

req.on('error', (e) => {
  console.error(`Problem with request: ${e.message}`);
});

req.write(postData);
req.end();

