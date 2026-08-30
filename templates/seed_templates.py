"""High-quality project templates for RAG-based generation.

These templates serve as the knowledge base for the TemplateRetriever.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.knowledge.template_store import TemplateStore, ProjectTemplate

TEMPLATES = [
    ProjectTemplate(
        template_id="pygame_game",
        name="Pygame 2D Game Template",
        description="Minimal Pygame template with game loop, events, and rendering",
        project_type="game",
        tech_stack={"runtime": "python", "frameworks": ["pygame"], "tools": ["pytest"]},
        files={
            "main.py": '''import pygame
import sys

class Game:
    def __init__(self, width=800, height=600):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Game")
        self.clock = pygame.time.Clock()
        self.running = True

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def update(self):
        pass

    def render(self):
        self.screen.fill((0, 0, 0))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
''',
            "requirements.txt": "pygame>=2.0.0\n",
            "README.md": "# Pygame Game Template\n\nRun: `python main.py`\n",
        },
        config={"entry_point": "main.py"},
        tags=["game", "pygame", "2d", "arcade"],
        quality_score=98.0,
    ),
    ProjectTemplate(
        template_id="fastapi_api",
        name="FastAPI REST API Template",
        description="Production-ready FastAPI template with CRUD, validation, and error handling",
        project_type="api",
        tech_stack={"runtime": "python", "backend": "fastapi", "database": "sqlite", "frameworks": ["fastapi", "uvicorn", "pydantic"]},
        files={
            "main.py": '''from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import sqlite3
import uvicorn

app = FastAPI(title="API", version="1.0.0")

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

items_db: dict[int, Item] = {}
_id_counter = 1

@app.get("/")
def read_root():
    return {"message": "API is running"}

@app.post("/items/", response_model=Item)
def create_item(item: Item):
    global _id_counter
    items_db[_id_counter] = item
    _id_counter += 1
    return item

@app.get("/items/", response_model=List[Item])
def list_items():
    return list(items_db.values())

@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int):
    if item_id not in items_db:
        raise HTTPException(status_code=404, detail="Item not found")
    return items_db[item_id]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
''',
            "requirements.txt": "fastapi>=0.100.0\nuvicorn[standard]>=0.23.0\npydantic>=2.0.0\n",
            "README.md": "# FastAPI Template\n\nRun: `uvicorn main:app --reload`\nDocs: `http://localhost:8000/docs`\n",
        },
        config={"entry_point": "main.py", "port": 8000},
        tags=["api", "fastapi", "rest", "backend"],
        quality_score=97.0,
    ),
    ProjectTemplate(
        template_id="react_portfolio",
        name="React Portfolio Template",
        description="Clean React portfolio with Vite and modern CSS",
        project_type="web_app",
        tech_stack={"runtime": "javascript", "frontend": "react", "frameworks": ["react", "vite"]},
        files={
            "src/App.jsx": '''import { useState } from 'react'

function App() {
  const [projects] = useState([
    { title: "Project 1", desc: "Description" },
    { title: "Project 2", desc: "Description" },
  ])

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow">
        <div className="max-w-7xl mx-auto py-6 px-4">
          <h1 className="text-3xl font-bold text-gray-900">My Portfolio</h1>
        </div>
      </header>
      <main className="max-w-7xl mx-auto py-6 px-4">
        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Projects</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {projects.map((p, i) => (
              <div key={i} className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-xl font-medium">{p.title}</h3>
                <p className="text-gray-600 mt-2">{p.desc}</p>
              </div>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
''',
            "src/main.jsx": '''import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
''',
            "src/index.css": """@tailwind base;
@tailwind components;
@tailwind utilities;

body {
  margin: 0;
  font-family: system-ui, -apple-system, sans-serif;
}
""",
            "package.json": '{"name": "portfolio", "private": true, "version": "0.0.0", "type": "module", "scripts": {"dev": "vite", "build": "vite build", "preview": "vite preview"}, "dependencies": {"react": "^18.2.0", "react-dom": "^18.2.0"}, "devDependencies": {"@vitejs/plugin-react": "^4.0.0", "vite": "^4.4.0", "tailwindcss": "^3.3.0", "postcss": "^8.4.0", "autoprefixer": "^10.4.0"}}',
            "vite.config.js": "import { defineConfig } from 'vite'\nimport react from '@vitejs/plugin-react'\n\nexport default defineConfig({ plugins: [react()] })",
            "tailwind.config.js": "/** @type {import('tailwindcss').Config} */\nexport default { content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'], theme: { extend: {} }, plugins: [], }",
            "postcss.config.js": "export default { plugins: { tailwindcss: {}, autoprefixer: {}, }, }",
            "index.html": '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8" /><meta name="viewport" content="width=device-width, initial-scale=1.0" /><title>Portfolio</title></head><body><div id="root"></div><script type="module" src="/src/main.jsx"></script></body></html>',
            "README.md": "# React Portfolio\n\nRun: `npm install && npm run dev`\n",
        },
        config={"entry_point": "src/main.jsx", "port": 5173},
        tags=["portfolio", "react", "vite", "frontend"],
        quality_score=96.0,
    ),
    ProjectTemplate(
        template_id="python_cli",
        name="Python CLI Template",
        description="Robust CLI tool with Click and Rich",
        project_type="cli",
        tech_stack={"runtime": "python", "frameworks": ["click", "rich"], "tools": ["pytest"]},
        files={
            "main.py": '''import click
from rich.console import Console
from rich.table import Table

console = Console()

@click.group()
def cli():
    """My CLI Tool"""
    pass

@cli.command()
@click.argument("name")
def greet(name: str):
    """Greet someone"""
    console.print(f"[bold green]Hello, {name}![/bold green]")

@cli.command()
def status():
    """Show status"""
    table = Table(title="Status")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_row("Database", "Connected")
    table.add_row("Cache", "Running")
    console.print(table)

if __name__ == "__main__":
    cli()
''',
            "requirements.txt": "click>=8.0.0\nrich>=13.0.0\n",
            "README.md": "# CLI Template\n\nRun: `python main.py --help`\n",
        },
        config={"entry_point": "main.py"},
        tags=["cli", "click", "rich", "terminal"],
        quality_score=97.0,
    ),
]


def seed_templates():
    """Seed the template store with high-quality templates."""
    store = TemplateStore()
    for template in TEMPLATES:
        if not store.get(template.template_id):
            store.save(template)
            print("Seeded template: %s" % template.template_id)
    print("Total templates: %d" % len(store.list()))


if __name__ == "__main__":
    seed_templates()
