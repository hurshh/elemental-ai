# Elemental AI

**Reverse-engineer any product into its raw materials, weight breakdown, and trade impact.**

Upload a product image → Get a complete bill of materials → See tariff implications instantly.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-green.svg)
![React](https://img.shields.io/badge/react-18+-61dafb.svg)

---

## What is this?

Elemental AI analyzes product images to extract:

- **Component breakdown** — What parts make up this product?
- **Material composition** — Wood, steel, plastic percentages
- **Weight estimates** — Per-component and total weight
- **Trade impact** — HS codes, duty rates, compliance requirements

Built for procurement teams, customs brokers, and supply chain analysts who need quick material intelligence without disassembling products or waiting for supplier specs.

---

## How it works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Upload Image  │────▶│  Vision AI Agent │────▶│  Bill of        │
│   (product/CAD) │     │  (Qwen VL 72B)   │     │  Materials      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌─────────────────────────────────┘
                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  MongoDB Atlas  │◀───▶│  RAG Matching    │────▶│  Weight &       │
│  (product DB)   │     │  Agent           │     │  Materials      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
                        ┌─────────────────────────────────┘
                        ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  HTS Database   │◀───▶│  Tariff Agent    │────▶│  Trade Impact   │
│  (duty rates)   │     │  (GPT-4o)        │     │  Report         │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Agent Workflow

The system uses a multi-agent pipeline where each agent specializes in one task:

**1. Vision Agent** (`components_parsing/`)
- Input: Product image (photo, sketch, CAD render)
- Model: Qwen VL 72B via OpenRouter
- Output: Structured BOM with component names, quantities, materials, dimensions
- Prompt engineering for industrial/procurement context

**2. Matching Agent** (`components_matching/`)
- Input: BOM from Vision Agent
- First: Query MongoDB vector index for known components
- Fallback: GPT-4o-mini for weight/material estimation
- Output: Enriched BOM with weights (kg) and raw material percentages

**3. Tariff Agent** (`tariff_estimation/`)
- Input: Enriched BOM with materials
- Model: GPT-4o with customs expertise prompt
- Output: HS codes, MFN rates, Section 301 duties, compliance requirements
- Includes cost optimization suggestions

**4. Orchestrator** (`pipeline.py`)
- Chains all agents together
- Handles errors gracefully (agent failures don't break the pipeline)
- Aggregates material percentages across all components
- Generates final report with metadata

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+ (for frontend)
- MongoDB Atlas account (optional, for component database)

### 1. Clone and setup

```bash
git clone https://github.com/hurshh/elemental-ai.git
cd elemental-ai
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:

```env
OPEN_API_KEY=sk-...          # OpenAI API key
OPEN_RAILS_KEY=sk-or-...     # OpenRouter API key (for vision model)
MONGO_STRING=mongodb+srv://... # MongoDB Atlas connection (optional)
```

### 3. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
```

### 4. Run the app

```bash
# Terminal 1 - Backend (port 5001)
cd backend
python app.py

# Terminal 2 - Frontend (port 5174)
cd frontend
npm run dev
```

Open http://localhost:5174

---

## Project Structure

```
elemental-ai/
├── backend/
│   ├── app.py                      # Flask API server
│   ├── pipeline.py                 # Main orchestrator
│   ├── requirements.txt
│   │
│   ├── components_parsing/         # Vision Agent
│   │   ├── component_analysis.py   # Image → BOM extraction
│   │   └── test/                   # Test images
│   │
│   ├── components_matching/        # Matching Agent
│   │   └── component_matching.py   # RAG + weight estimation
│   │
│   └── tariff_estimation/          # Tariff Agent
│       └── tariff_estimation.py    # HS codes + duties
│
├── frontend/
│   ├── src/
│   │   ├── App.tsx                 # Main React component
│   │   └── index.css               # Tailwind styles
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

---

## API Reference

### `POST /api/analyze`

Upload an image for analysis.

**Request:**
```bash
curl -X POST http://localhost:5001/api/analyze \
  -F "image=@product.jpg" \
  -F "context=wooden furniture" \
  -F "origin_country=China" \
  -F "destination_country=United States" \
  -F "declared_value=500"
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "report": {
      "components": [...],
      "weight_summary": { "total_weight_kg": 67.7 },
      "material_composition": {
        "aggregate_percentages": {
          "softwood": 50.2,
          "hardwood": 22.4,
          "steel": 4.5
        }
      }
    },
    "tariff_estimation": {
      "hs_code_classification": {
        "primary_hs_code": "9403.50.9045",
        "hs_code_description": "Wooden bedroom furniture"
      },
      "tariff_rates": {
        "effective_total_rate_percent": 27.5
      },
      "estimated_duties": {
        "total_estimated_duty_usd": 123.75
      }
    }
  }
}
```

### `GET /api/demo`

Returns sample data for testing the frontend without API keys.

### `GET /api/health`

Health check endpoint.

---

## Using the Agents Directly

Each agent can be used independently:

### Vision Agent

```python
from components_parsing.component_analysis import analyze_components

bom = analyze_components(
    "furniture.jpg",
    user_context="oak wood frame with metal brackets"
)
print(bom)
# {'bill_of_materials': [{'component_name': 'Frame', 'quantity': 4, ...}]}
```

### Matching Agent

```python
from components_matching.component_matching import process_bill_of_materials

enriched = process_bill_of_materials(bom)
print(f"Total weight: {enriched['summary']['total_weight_kg']} kg")
print(f"Materials: {enriched['summary']['aggregate_raw_materials']}")
```

### Tariff Agent

```python
from tariff_estimation import estimate_tariffs, generate_tariff_summary

tariff = estimate_tariffs(
    pipeline_report,
    origin_country="Vietnam",
    destination_country="United States",
    declared_value_usd=500
)
print(generate_tariff_summary(tariff))
```

### Full Pipeline

```python
from pipeline import generate_report

report = generate_report(
    "product.jpg",
    context="steel frame with wooden panels"
)
```

---

## Configuration

### Vision Model

The vision agent uses Qwen VL 72B via OpenRouter. You can swap models in `component_analysis.py`:

```python
model="qwen/qwen-2.5-vl-72b-instruct"  # Current
model="anthropic/claude-3.5-sonnet"    # Alternative
model="openai/gpt-4o"                   # Alternative
```

### MongoDB Vector Search

For production use, set up MongoDB Atlas with vector search:

1. Create a cluster on [MongoDB Atlas](https://cloud.mongodb.com)
2. Create a `products` collection in a `cluster0` database
3. Add documents with `embedding` field (1536-dim for text-embedding-3-small)
4. Create a vector search index named `vector_index`

Schema:
```json
{
  "name": "Steel bracket 10x10cm",
  "part_number": "BRK-1010",
  "weight": 0.4,
  "weight_unit": "kg",
  "material": "Galvanized Steel",
  "price": 2.50,
  "embedding": [0.123, -0.456, ...]
}
```

If MongoDB isn't configured, the system falls back to AI estimation.

---

## Testing

```bash
cd backend

# Test individual agents
python -m components_parsing.test.test_bom
python -m components_matching.test_component_matching
python -m tariff_estimation.test_tariff_estimation

# Test full pipeline
python test_pipeline.py
```

---

## Limitations

- **Weight estimates are approximations** — Based on material density heuristics, not actual measurements
- **Tariff rates may be outdated** — Always verify with CBP or a licensed customs broker
- **Vision model accuracy varies** — Works best with clear product photos or technical drawings
- **No real HTS database** — Uses LLM knowledge of tariff schedules (consider integrating USITC API for production)

---

## Roadmap

- [ ] Integration with USITC HTS API for real-time duty rates
- [ ] PDF/CAD file parsing (not just images)
- [ ] Supplier database with verified component weights
- [ ] Multi-country tariff comparison
- [ ] Export documentation generator
- [ ] Batch processing for catalogs

---

## Contributing

PRs welcome. For major changes, open an issue first.

```bash
# Fork the repo, then:
git checkout -b feature/your-feature
# Make changes
git commit -m "feat: add your feature"
git push origin feature/your-feature
# Open a PR
```

---

## License

MIT — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [OpenRouter](https://openrouter.ai) for vision model access
- [OpenAI](https://openai.com) for embeddings and GPT-4o
- [MongoDB Atlas](https://mongodb.com/atlas) for vector search
- [Tailwind CSS](https://tailwindcss.com) for styling
- [Framer Motion](https://framer.com/motion) for animations

