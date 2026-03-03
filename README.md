# Neuronova Pro: Intelligent Last-Mile Delivery Optimization

**Neuronova Pro** is a dynamic, city-intelligent routing engine designed to minimize fuel consumption and delivery time by navigating the complexities of urban environments.

## 🚀 Current Project Status (Built & Functional)

We have successfully transitioned from a static roadmap to a live, high-fidelity Logistics Command Center.

### 📍 Core Implementation Highlights:
- **Map Engine**: Migrated to **MapLibre GL** for high-performance vector rendering.
- **Visual Intelligence**: Integrated **OpenFreeMap** for detailed, CORS-friendly street tiles.

---

## 📺 Demo

> [!TIP]
> **View the Logistics Command Center in action!**
> 
> <video src="Demo.mp4" width="100%" controls></video>

---
- **Frontend Architecture**: Built with **React 19**, **Vite**, and **Zustand** for ultra-fast telemetry updates.
- **Optimization Layer**: Powered by **Google OR-Tools**, implementing meta-heuristics for the Vehicle Routing Problem (VRP).
- **Asynchronous Processing**: Implemented a **Background Worker Pattern** (FastAPI + Dedicated Worker) to handle complex matrix calculations without blocking the UI.
- **Weather Integration**: Dynamic cost scaling based on real-time weather data (e.g., 6% penalty during cloud cover/rain).
- **Containerization**: Fully Dockerized for seamless deployment across any environment.

---

## 🛠 Technology Stack

| Category | Tool / Framework |
| :--- | :--- |
| **Frontend** | React 19, Vite, Tailwind CSS, MapLibre GL |
| **Backend** | FastAPI, Pydantic V2, Uvicorn |
| **Optimization** | Google OR-Tools (Constraint Programming) |
| **Data Flow** | Background Worker / Polling Architecture |
| **Containerization** | Docker & Docker Compose |
| **External APIs** | TomTom (Matrix & Routing), OpenWeatherMap |

---

## 📟 Fleet Intelligence Dashboard

The application now features a professional "Operations Command" UI:
- **Telemetry Cards**: Real-time tracking of Fleet Coverage and Efficiency Index.
- **System Intelligence Terminal**: A monochrome live-log feed showing the optimizer's active logic paths.
- **Reactive Design**: Glassmorphic, dark-mode aesthetic optimized for logistics operators.

---

## 📈 Roadmap & Progress

- [x] **Phase 1: Data Infrastructure** (TomTom Matrix v2, MapLibre Engine)
- [x] **Phase 2: Predictive Logic** (Weather impact factors, Service Time heuristics)
- [x] **Phase 3: Optimization Solver** (OR-Tools VRP Implementation)
- [x] **Phase 4: Reactive Deployment** (Real-time telemetry, Advanced UI Dashboard)
- [x] **Phase 5: Containerization** (Docker & Orchestration)
- [ ] **Phase 6: Production Hardening** (Persistence layer, User Authentication)

---

## ⚙️ Deployment & Setup

### 🐳 The Quickest Start (Docker)
Launch the API, Worker, and Frontend with a single command:
```bash
docker compose up --build
```
*Access the dashboard at http://localhost:5173* (or as reported by Vite in the logs).

---

### 💻 Manual Development Setup

#### Backend (API & Worker)
```bash
python3 app/api.py & python3 app/worker.py
```

#### Frontend
```bash
cd frontend && npm run dev
```

---

*© 2026 Neuronova Intelligence Systems // End_Transmission*
