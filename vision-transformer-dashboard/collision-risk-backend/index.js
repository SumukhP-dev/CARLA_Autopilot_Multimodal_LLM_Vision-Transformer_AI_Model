// Import express
const express = require('express');

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

let simulations = [
  // Only real simulation data - no default examples
];

app.get('/api/simulations', (req, res) => {
  res.json(simulations);
});

app.post('/api/simulations', (req, res) => {
  const newSim = req.body;
  
  // Find existing simulation with same name
  const existingIndex = simulations.findIndex(sim => sim.name === newSim.name);
  
  if (existingIndex >= 0) {
    // Update existing simulation (use latest values, or accumulate based on your preference)
    // For now, we'll use the latest values sent
    simulations[existingIndex] = {
      name: newSim.name,
      collisions: newSim.collisions || 0,
      safeRuns: newSim.safeRuns || 0
    };
    res.json({ message: 'Simulation updated', data: simulations[existingIndex] });
  } else {
    // Add new simulation
    simulations.push(newSim);
    res.json({ message: 'Simulation added', data: newSim });
  }
});

// Start server listening
const PORT = 4000;
app.listen(PORT, () => {
  console.log(`✅ Server running on http://localhost:${PORT}`);
});
