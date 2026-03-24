from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

def print_weather(data: dict):
    """Beautiful weather display."""
    weather = data.get("weather", {})
    
    table = Table(title=f"🌤️ Weather in {weather.get('city', 'Unknown')}")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Temperature", weather.get("temperature", "N/A"))
    table.add_row("Feels Like", weather.get("feels_like", "N/A"))
    table.add_row("Description", weather.get("description", "N/A"))
    table.add_row("Humidity", weather.get("humidity", "N/A"))
    table.add_row("Wind Speed", weather.get("wind_speed", "N/A"))
    
    console.print(table)

def print_repos(data: dict):
    """Beautiful GitHub repos display."""
    repos = data.get("repositories", [])
    
    table = Table(title="🐙 Top GitHub Repositories")
    table.add_column("#", style="cyan", width=3)
    table.add_column("Name", style="magenta")
    table.add_column("⭐ Stars", style="yellow", justify="right")
    table.add_column("Language", style="green")
    
    for i, repo in enumerate(repos[:5], 1):
        table.add_row(
            str(i),
            repo.get("name", "Unknown"),
            f"{repo.get('stars', 0):,}",
            repo.get("language", "Unknown")
        )
    
    console.print(table)

def print_combined(data: dict):
    """Print all results beautifully."""
    if "weather" in data:
        print_weather(data)
        console.print()
    
    if "repositories" in data:
        print_repos(data)