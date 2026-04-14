import express from 'express';
import { createProxyMiddleware } from 'http-proxy-middleware';
import cors from 'cors';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const app = express();

// Enable CORS for local development testing
app.use(cors());

// 1. Proxy all /api traffic to AWS API Gateway
app.use('/api', createProxyMiddleware({
    target: 'https://l9hs049p42.execute-api.us-east-1.amazonaws.com',
    changeOrigin: true,
    secure: false,
}));

// 2. Serve the compiled React Dashboard locally
app.use(express.static(path.join(__dirname, 'dist')));

// 3. Match all other routes to index.html (SPA Fallback)
app.use((req, res) => {
    res.sendFile(path.join(__dirname, 'dist', 'index.html'));
});

const PORT = 8080;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Smart Parking Proxy Server running on port ${PORT}`);
});
