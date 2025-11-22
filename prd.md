Here is the Product Requirement Document (PRD) followed by the fully functional MVP code.

### **Product Requirement Document (PRD): GridLens Weather Overlay MVP**

**1. Executive Summary**
* **Product Name:** GridLens Weather Overlay
* **Goal:** Enable power analysts to instantly validate if load deviations are caused by weather events (cloud cover/temp) without leaving their browser tab.
* **Target User:** Power Market Analysts (e.g., at Grid Status, Genscape) who monitor Real-Time (RT) vs. Day-Ahead (DA) load.

**2. Problem Statement**
Analysts often see a "Load Drop" (Actual < Forecast) on a price map. To confirm if this is due to "embedded solar" (cloud cover clearing) or a "demand drop" (temperature cooling), they must manually cross-reference a separate weather model (e.g., HRRR). This context switching slows down decision-making and reporting.

**3. MVP Solution**
A Chrome Extension side-panel that:
1.  Accepts natural language queries (e.g., *"Why is Dominion load dropping?"*).
2.  Retrieves pre-loaded grid & weather data (simulated 6-month history).
3.  Overlays **Cloud Opacity** directly on the **Load Curve**.
4.  Uses an AI Agent to find "Similar Historical Days" to validate the hypothesis.

**4. Functional Requirements**
* **Data Layer:**
    * Store a "Mock Database" of PJM/Dominion load and weather data.
    * Simulate "SQL-like" filtering to find days with high cloud cover and high load deviation.
* **Visualization:**
    * Dual-Axis Chart: Left Axis = Load (MW), Right Axis = Cloud Cover (%).
    * Visual correlation: Show how spikes in cloud cover align with drops in load.
* **AI Analyst (Agent):**
    * Input: Current data + "Best Match" historical day data.
    * Output: A concise, analyst-style explanation (e.g., *"Deviation confirmed. 85% Cloud Cover matches the profile of Nov 17, 2024."*).

**5. Success Metrics**
* **Speed:** Time to insight < 5 seconds (vs. 2 mins manually).
* **Clarity:** User can identify the "cause" of deviation solely from the overlay chart.

---

### **MVP Implementation (Chrome Extension Prototype)**

This is a self-contained, single-file prototype. It mimics the "Chrome Extension Side Panel" experience. It includes a **Mock Database** (JSON) of grid data, a **Chart.js** visualization, and uses **Gemini** to act as the AI Analyst.


http://googleusercontent.com/immersive_entry_chip/0