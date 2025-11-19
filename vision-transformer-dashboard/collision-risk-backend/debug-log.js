// Debug script to test backend storage
const fs = require('fs');
const http = require('http');

const testData = {
  name: "FileDebugTest",
  collisions: 5,
  safeRuns: 95,
  safetyRate: 95.0,
  gradeLevel: "A",
  speedStats: { mean: 5.5, std: 1.2, variance: 1.44 },
  steeringStats: { mean: 0.1, std: 0.05 },
  totalFrames: 1000,
  avgFPS: 30.0
};

const postData = JSON.stringify(testData);
const logFile = 'debug-output.txt';

fs.writeFileSync(logFile, `=== Debug Test Started ===\n`);
fs.appendFileSync(logFile, `Sending data: ${postData}\n\n`);

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

const req = http.request(options, (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    fs.appendFileSync(logFile, `POST Response: ${data}\n\n`);
    
    setTimeout(() => {
      http.get('http://localhost:4000/api/simulations', (getRes) => {
        let getData = '';
        getRes.on('data', (chunk) => { getData += chunk; });
        getRes.on('end', () => {
          fs.appendFileSync(logFile, `GET Response: ${getData}\n\n`);
          fs.appendFileSync(logFile, `Contains speedStats: ${getData.includes('speedStats')}\n`);
          
          const parsed = JSON.parse(getData);
          const testEnv = parsed.find(s => s.name === 'FileDebugTest');
          if (testEnv) {
            fs.appendFileSync(logFile, `\nFileDebugTest found\n`);
            fs.appendFileSync(logFile, `Properties: ${Object.keys(testEnv).join(', ')}\n`);
            fs.appendFileSync(logFile, `Has speedStats: ${!!testEnv.speedStats}\n`);
            if (testEnv.speedStats) {
              fs.appendFileSync(logFile, `speedStats: ${JSON.stringify(testEnv.speedStats)}\n`);
            }
          }
          
          fs.appendFileSync(logFile, `\n=== Debug Test Complete ===\n`);
          console.log('Debug log written to', logFile);
        });
      });
    }, 1000);
  });
});

req.on('error', (e) => {
  fs.appendFileSync(logFile, `Error: ${e.message}\n`);
});

req.write(postData);
req.end();

