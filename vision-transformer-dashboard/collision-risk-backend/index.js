// Import express
const express = require('express');
const fs = require('fs');

// Create express app
const app = express();

// Middleware for parsing JSON
const cors = require('cors');
app.use(cors());
app.use(express.json()); // Parse JSON bodies

// Basic route
app.get('/', (req, res) => {
  res.send('Hello from Express backend!');
});

// Store simulations as JSON strings to avoid any object reference issues
let simulations = [
  // Only real simulation data - no default examples
];

// Debug route to inspect stored data
app.get('/api/debug', (req, res) => {
  const parsed = simulations.map((sim, idx) => {
    const parsedSim = typeof sim === 'string' ? JSON.parse(sim) : sim;
    return {
      index: idx,
      storedAs: typeof sim,
      name: parsedSim.name,
      keys: Object.keys(parsedSim),
      hasSpeedStats: !!parsedSim.speedStats,
      speedStatsKeys: parsedSim.speedStats ? Object.keys(parsedSim.speedStats) : [],
      rawStringPreview: typeof sim === 'string' ? sim.substring(0, 300) : 'N/A (object)',
      containsSpeedStatsInString: typeof sim === 'string' ? sim.includes('speedStats') : 'N/A',
      fullObject: parsedSim
    };
  });
  res.json({
    count: simulations.length,
    simulations: parsed
  });
});

// Route to clear all simulations (for testing)
app.delete('/api/simulations', (req, res) => {
  simulations = [];
  res.json({ message: 'All simulations cleared' });
});

app.get('/api/simulations', (req, res) => {
  // Parse all stored JSON strings back to objects
  const parsedSimulations = simulations.map(sim => {
    if (typeof sim === 'string') {
      return JSON.parse(sim);
    }
    return sim; // Fallback for any non-string entries
  });
  
  console.log('[GET] Returning', parsedSimulations.length, 'simulation(s)');
  if (parsedSimulations.length > 0) {
    console.log('[GET] First simulation keys:', Object.keys(parsedSimulations[0]));
    if (parsedSimulations[0].speedStats) {
      console.log('[GET] First simulation speedStats:', JSON.stringify(parsedSimulations[0].speedStats));
    } else {
      console.log('[GET] WARNING: speedStats is missing from stored data!');
    }
  }
  
  // Serialize and send
  const jsonString = JSON.stringify(parsedSimulations);
  console.log('[GET] Serialized JSON contains speedStats:', jsonString.includes('speedStats'));
  
  res.setHeader('Content-Type', 'application/json');
  res.send(jsonString);
});

app.post('/api/simulations', (req, res) => {
  const newSim = req.body;
  
  // Debug: Log received data structure to file for inspection
  const debugLog = {
    timestamp: new Date().toISOString(),
    receivedKeys: Object.keys(newSim),
    hasSpeedStats: !!newSim.speedStats,
    speedStatsType: typeof newSim.speedStats,
    speedStatsValue: newSim.speedStats,
    fullBody: newSim
  };
  fs.writeFileSync('post-debug.json', JSON.stringify(debugLog, null, 2));
  console.log('[POST] Debug log written to post-debug.json');
  
  // Debug: Log received data structure
  console.log('[POST] Received simulation data keys:', Object.keys(newSim));
  if (newSim.speedStats) {
    console.log('[POST] speedStats received:', JSON.stringify(newSim.speedStats));
  } else {
    console.log('[POST] WARNING: speedStats is missing or undefined');
  }

  // Find existing simulation with same name (parse strings for comparison)
  const existingIndex = simulations.findIndex((sim) => {
    const parsed = typeof sim === 'string' ? JSON.parse(sim) : sim;
    return parsed.name === newSim.name;
  });

  // CRITICAL: Log what we receive BEFORE any processing
  console.log('[POST] ===== RAW REQUEST BODY =====');
  console.log('[POST] RAW newSim keys:', Object.keys(newSim));
  console.log('[POST] RAW newSim has speedStats:', !!newSim.speedStats);
  console.log('[POST] RAW newSim.speedStats type:', typeof newSim.speedStats);
  console.log('[POST] RAW newSim.speedStats value:', JSON.stringify(newSim.speedStats));
  console.log('[POST] RAW newSim full object:', JSON.stringify(newSim, null, 2));
  
  // Write raw request to file immediately
  try {
    fs.writeFileSync('raw-request.json', JSON.stringify({
      timestamp: new Date().toISOString(),
      keys: Object.keys(newSim),
      hasSpeedStats: !!newSim.speedStats,
      speedStats: newSim.speedStats,
      fullBody: newSim
    }, null, 2));
    console.log('[POST] Raw request written to raw-request.json');
  } catch (e) {
    console.error('[POST] Error writing raw request:', e);
  }
  
  // Store the raw object as JSON string - no processing at all
  const simulationData = newSim;
  
  // Verify simulationData has speedStats
  console.log('[POST] ===== AFTER ASSIGNMENT =====');
  console.log('[POST] simulationData has speedStats:', !!simulationData.speedStats);
  console.log('[POST] simulationData.speedStats:', JSON.stringify(simulationData.speedStats));
  
  // Debug: Log what we're storing
  console.log('[POST] Storing simulation data:');
  console.log('  - speedStats keys:', Object.keys(simulationData.speedStats));
  console.log('  - speedStats mean:', simulationData.speedStats.mean);
  console.log('  - totalFrames:', simulationData.totalFrames);
  console.log('  - avgFPS:', simulationData.avgFPS);
  console.log('  - Full simulationData keys:', Object.keys(simulationData));
  console.log('  - Full simulationData:', JSON.stringify(simulationData, null, 2));

  // Store directly - no deep copy needed, the object is already correct
  // Deep copy was potentially causing issues, so store the object as-is
  // Write simulationData to file BEFORE storing
  const beforeStoreLog = {
    timestamp: new Date().toISOString(),
    existingIndex: existingIndex,
    simulationDataKeys: Object.keys(simulationData),
    hasSpeedStats: !!simulationData.speedStats,
    speedStatsValue: simulationData.speedStats,
    fullSimulationData: simulationData
  };
  fs.writeFileSync('before-store.json', JSON.stringify(beforeStoreLog, null, 2));
  console.log('[POST] Before store log written');
  
  if (existingIndex >= 0) {
    // Update existing simulation - store raw object as JSON string
    console.log('[POST] UPDATING existing simulation at index', existingIndex);
    console.log('[POST] BEFORE STORE - simulationData keys:', Object.keys(simulationData));
    console.log('[POST] BEFORE STORE - simulationData.speedStats:', JSON.stringify(simulationData.speedStats));
    
    const stringToStore = JSON.stringify(simulationData);
    console.log('[POST] UPDATE - String to store contains speedStats:', stringToStore.includes('speedStats'));
    console.log('[POST] UPDATE - String to store (first 300 chars):', stringToStore.substring(0, 300));
    
    // Write to file for verification
    try {
      fs.writeFileSync('update-string-to-store.json', stringToStore);
      console.log('[POST] UPDATE - String written to update-string-to-store.json');
    } catch (e) {
      console.error('[POST] UPDATE - Error writing file:', e);
    }
    
    simulations[existingIndex] = stringToStore;
    console.log('[POST] AFTER STORE - stored string contains speedStats:', simulations[existingIndex].includes('speedStats'));
    
    // Immediate verification - parse the stored string
    const verify = JSON.parse(simulations[existingIndex]);
    console.log('[POST] IMMEDIATE VERIFY - speedStats exists?', !!verify.speedStats);
    console.log('[POST] IMMEDIATE VERIFY - speedStats keys:', verify.speedStats ? Object.keys(verify.speedStats) : 'N/A');
    console.log('[POST] IMMEDIATE VERIFY - verify keys:', Object.keys(verify));
    
    // Write to file
    const afterStoreLog = {
      timestamp: new Date().toISOString(),
      action: 'UPDATE',
      index: existingIndex,
      storedKeys: Object.keys(verify),
      hasSpeedStats: !!verify.speedStats,
      speedStatsValue: verify.speedStats,
      fullStored: verify,
      arrayLength: simulations.length
    };
    fs.writeFileSync('after-store.json', JSON.stringify(afterStoreLog, null, 2));
    console.log('[POST] After store log written');
    
    res.json({ message: 'Simulation updated', data: verify });
  } else {
    // Add new simulation - store as JSON string
    console.log('[POST] ADDING new simulation');
    console.log('[POST] BEFORE PUSH - simulationData keys:', Object.keys(simulationData));
    console.log('[POST] BEFORE PUSH - simulationData has speedStats:', !!simulationData.speedStats);
    console.log('[POST] BEFORE PUSH - simulationData.speedStats:', JSON.stringify(simulationData.speedStats));
    
    const beforePushLength = simulations.length;
    const stringToStore = JSON.stringify(simulationData);
    console.log('[POST] String to store contains speedStats:', stringToStore.includes('speedStats'));
    console.log('[POST] String to store (first 300 chars):', stringToStore.substring(0, 300));
    
    // Write string to file for verification
    fs.writeFileSync('string-to-store.json', stringToStore);
    console.log('[POST] String written to string-to-store.json');
    
    simulations.push(stringToStore);
    const lastIndex = simulations.length - 1;
    console.log('[POST] Pushed to index', lastIndex, '(was', beforePushLength, 'before)');
    console.log('[POST] Stored string contains speedStats:', simulations[lastIndex].includes('speedStats'));
    
    // Immediate verification - parse the stored string
    const verify = JSON.parse(simulations[lastIndex]);
    console.log('[POST] AFTER PUSH - verify keys:', Object.keys(verify));
    console.log('[POST] AFTER PUSH - verify has speedStats:', !!verify.speedStats);
    console.log('[POST] AFTER PUSH - verify.speedStats:', JSON.stringify(verify.speedStats));
    console.log('[POST] IMMEDIATE VERIFY - speedStats exists?', !!verify.speedStats);
    console.log('[POST] IMMEDIATE VERIFY - speedStats keys:', verify.speedStats ? Object.keys(verify.speedStats) : 'N/A');
    
    // Write to file
    const afterStoreLog = {
      timestamp: new Date().toISOString(),
      action: 'ADD',
      index: lastIndex,
      storedKeys: Object.keys(verify),
      hasSpeedStats: !!verify.speedStats,
      speedStatsValue: verify.speedStats,
      fullStored: verify,
      arrayLength: simulations.length
    };
    fs.writeFileSync('after-store.json', JSON.stringify(afterStoreLog, null, 2));
    console.log('[POST] After store log written');
    
    res.json({ message: 'Simulation added', data: simulationData });
  }
});

// Start server listening
const PORT = 4000;
app.listen(PORT, () => {
  console.log(`✅ Server running on http://localhost:${PORT}`);
});
