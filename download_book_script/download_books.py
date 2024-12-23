import requests
import os
from pathlib import Path
import json
from typing import List, Dict, Optional
import time
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich import print as rprint
import urllib.parse

@dataclass
class BookResult:
    title: str
    author: str
    format: str
    source: str
    download_url: str
    file_size: Optional[str] = None

class BookFetcher:
    def __init__(self):
        self.console = Console()
        self.desktop_path = str(Path.home() / "Desktop")
        self.download_folder = os.path.join(self.desktop_path, "book_fetcher")
        self._ensure_download_folder()
        
        # API keys would typically be stored in environment variables
        self.open_library_api = "https://openlibrary.org/search.json"
        self.project_gutenberg_api = "https://gutendex.com/books"
        self.libgen_api = "http://libgen.rs/json.php"
    
    def _ensure_download_folder(self):
        """Create download folder if it doesn't exist"""
        if not os.path.exists(self.download_folder):
            os.makedirs(self.download_folder)
    
    def search_open_library(self, title: str, author: str) -> List[BookResult]:
        """Search OpenLibrary API for books"""
        query = f"title:{title} author:{author}"
        params = {"q": query, "fields": "title,author_name,formats"}
        
        try:
            response = requests.get(self.open_library_api, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for doc in data.get("docs", []):
                formats = doc.get("formats", [])
                for fmt in formats:
                    if ".pdf" in fmt.lower() or ".epub" in fmt.lower():
                        results.append(
                            BookResult(
                                title=doc.get("title", "Unknown"),
                                author=", ".join(doc.get("author_name", ["Unknown"])),
                                format="PDF" if ".pdf" in fmt.lower() else "EPUB",
                                source="OpenLibrary",
                                download_url=fmt
                            )
                        )
            return results
        except Exception as e:
            self.console.print(f"[red]Error searching OpenLibrary: {str(e)}[/red]")
            return []

    def search_project_gutenberg(self, title: str, author: str) -> List[BookResult]:
        """Search Project Gutenberg API for books"""
        query = f"{title} {author}"
        params = {"search": query}
        
        try:
            response = requests.get(self.project_gutenberg_api, params=params)
            response.raise_for_status()
            data = response.json()
            
            results = []
            for book in data.get("results", []):
                formats = book.get("formats", {})
                for fmt_type, url in formats.items():
                    if "pdf" in fmt_type.lower() or "epub" in fmt_type.lower():
                        results.append(
                            BookResult(
                                title=book.get("title", "Unknown"),
                                author=", ".join(book.get("authors", [{"name": "Unknown"}])[0].get("name")),
                                format="PDF" if "pdf" in fmt_type.lower() else "EPUB",
                                source="Project Gutenberg",
                                download_url=url
                            )
                        )
            return results
        except Exception as e:
            self.console.print(f"[red]Error searching Project Gutenberg: {str(e)}[/red]")
            return []

    def download_book(self, book_result: BookResult) -> bool:
        """Download the book from the provided URL"""
        try:
            response = requests.get(book_result.download_url, stream=True)
            response.raise_for_status()
            
            # Create filename from title and format
            safe_title = "".join(c for c in book_result.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_title}.{book_result.format.lower()}"
            filepath = os.path.join(self.download_folder, filename)
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(filepath, 'wb') as f, self.console.status(f"[bold green]Downloading {filename}...") as status:
                if total_size == 0:
                    f.write(response.content)
                else:
                    downloaded = 0
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            percent = (downloaded / total_size) * 100
                            status.update(f"[bold green]Downloading {filename}: {percent:.1f}%")
            
            self.console.print(f"[green]Successfully downloaded to: {filepath}[/green]")
            return True
            
        except Exception as e:
            self.console.print(f"[red]Error downloading book: {str(e)}[/red]")
            return False

    def display_results(self, results: List[BookResult]) -> Optional[BookResult]:
        """Display search results in a table and let user choose"""
        if not results:
            self.console.print("[yellow]No results found.[/yellow]")
            return None
            
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim")
        table.add_column("Title")
        table.add_column("Author")
        table.add_column("Format")
        table.add_column("Source")
        
        for idx, result in enumerate(results, 1):
            table.add_row(
                str(idx),
                result.title,
                result.author,
                result.format,
                result.source
            )
        
        self.console.print(table)
        
        while True:
            choice = self.console.input("\n[bold]Enter the number of the book to download (or 'q' to quit): [/bold]")
            if choice.lower() == 'q':
                return None
            try:
                choice_idx = int(choice) - 1
                if 0 <= choice_idx < len(results):
                    return results[choice_idx]
                else:
                    self.console.print("[red]Invalid number. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a valid number.[/red]")

def main():
    console = Console()
    fetcher = BookFetcher()
    
    # Get user input
    title = console.input("[bold]Enter book title: [/bold]")
    author = console.input("[bold]Enter author name: [/bold]")
    
    with console.status("[bold green]Searching for books...") as status:
        # Search all sources
        results = []
        results.extend(fetcher.search_open_library(title, author))
        results.extend(fetcher.search_project_gutenberg(title, author))
        
        # Remove duplicates based on download URL
        unique_results = list({r.download_url: r for r in results}.values())
    
    # Display results and get user choice
    selected_book = fetcher.display_results(unique_results)
    
    if selected_book:
        fetcher.download_book(selected_book)

if __name__ == "__main__":
    main()
