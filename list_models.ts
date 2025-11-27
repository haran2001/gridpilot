import 'dotenv/config';
import { GoogleGenerativeAI } from '@google/generative-ai';

const apiKey = process.env.GEMINI_API_KEY;

if (!apiKey) {
    console.error('GEMINI_API_KEY is not set in environment variables.');
    process.exit(1);
}

const genAI = new GoogleGenerativeAI(apiKey);

async function listModels() {
    try {
        // For the Node.js SDK, we might not have a direct listModels method on genAI.
        // We usually access it via the model manager if available, but the SDK structure varies.
        // Let's try to just use a known model that usually works or check the error more closely.
        // Actually, the error message says "Call ListModels".
        // In the v1beta API via REST it is GET /v1beta/models.
        // In the Node SDK, it might not be exposed directly in the main entry point in older versions,
        // but we updated to latest.

        // Let's try to assume 'gemini-pro' is the safest bet if 1.5 failed, 
        // but let's try to see if we can find a working one.

        // Since I cannot easily browse documentation, I will try to use 'gemini-pro' again 
        // but maybe the issue is the region or the key type.

        // However, I will try to write a script that uses the REST API directly to list models
        // to be absolutely sure, as the SDK might hide details.

        const url = `https://generativelanguage.googleapis.com/v1beta/models?key=${apiKey}`;

        const response = await fetch(url);
        const data = await response.json() as { models?: { name: string }[] };

        if (data.models) {
            console.log("Available models:");
            data.models.forEach(m => console.log(`- ${m.name}`));
        } else {
            console.log("Error listing models:", data);
        }

    } catch (error) {
        console.error('Error:', error);
    }
}

listModels();
