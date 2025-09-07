// Import express
const express = require('express');

// Create express app
const app = express();

// Middleware for parsing JSON
const cors = require('cors');
app.use(cors());

// Basic route
app.get('/', (req, res) => {
  res.send('Hello from Express backend!');
});

let simulations = [
  { name: 'Urban Intersection', collisions: 2, safeRuns: 18 },
  { name: 'Highway Merge', collisions: 1, safeRuns: 19 },
];

app.get('/api/simulations', (req, res) => {
  res.json(simulations);
});

app.post('/api/simulations', (req, res) => {
  const newSim = req.body;
  simulations.push(newSim);
  res.json({ message: 'Simulation added', data: newSim });
});

// Start server listening
const PORT = 4000;
app.listen(PORT, () => {
  console.log(`✅ Server running on http://localhost:${PORT}`);
});
