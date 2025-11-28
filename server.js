require('dotenv').config();
const express = require('express');
const path = require('path');

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());
app.use(express.static('public'));

app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body;
    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    const { spawn } = require('child_process');
    // Use python from conda environment if available
    const pythonPath = process.env.PYTHON_PATH || 'python';
    const pythonProcess = spawn(pythonPath, ['agents/gridpilot_agent.py', message], {
      env: { ...process.env }
    });

    let dataString = '';
    let errorString = '';

    pythonProcess.stdout.on('data', (data) => {
      dataString += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
      errorString += data.toString();
    });

    pythonProcess.on('close', (code) => {
      if (code !== 0) {
        console.error(`Python process exited with code ${code}`);
        console.error('Python Error:', errorString);
        return res.status(500).json({ error: 'Failed to process request. Please check server logs.' });
      }

      // Parse the agent output to extract meaningful responses
      const lines = dataString.split('\n');
      const agentResponses = [];

      for (const line of lines) {
        // Capture agent responses in format [AgentName]: Response
        const agentMatch = line.match(/^\[([\w_]+)\]: (.+)$/);
        if (agentMatch && agentMatch[2] !== 'None') {
          agentResponses.push({
            agent: agentMatch[1],
            message: agentMatch[2]
          });
        }
      }

      // Format the response for the frontend
      let formattedResponse = '';
      if (agentResponses.length > 0) {
        // Get the last meaningful response (usually from Coordinator or the final agent)
        const lastResponse = agentResponses[agentResponses.length - 1];
        formattedResponse = lastResponse.message;

        // If there are market data responses, combine them
        const marketData = agentResponses.filter(r => r.agent === 'CAISO_Market');
        const weatherData = agentResponses.filter(r => r.agent === 'Weather');

        if (marketData.length > 0 || weatherData.length > 0) {
          formattedResponse = agentResponses
            .filter(r => r.message !== 'None' && r.message.length > 10)
            .map(r => r.message)
            .join('\n\n');
        }
      } else {
        // Fallback to raw output if no structured responses found
        formattedResponse = dataString
          .split('\n')
          .filter(line => !line.startsWith('User:') &&
                         !line.includes('UserWarning') &&
                         !line.includes('INFO') &&
                         !line.includes('DEBUG') &&
                         !line.includes('Warning:') &&
                         line.trim().length > 0)
          .join('\n');
      }

      res.json({ response: formattedResponse || 'No response generated' });
    });

  } catch (error) {
    console.error('Error communicating with backend:', error);
    res.status(500).json({ error: 'Failed to get response' });
  }
});

app.listen(port, () => {
  console.log(`Server running at http://localhost:${port}`);
});