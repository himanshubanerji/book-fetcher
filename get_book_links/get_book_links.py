import requests
from bs4 import BeautifulSoup
import os
import re

def search_google_books(book_name, author_name):
    """Search Google Books API for books by author and title."""
    api_url = "https://www.googleapis.com/books/v1/volumes"
    params = {
        'q': f"intitle:{book_name}+inauthor:{author_name}",
        'maxResults': 5
    }
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        books = response.json().get('items', [])
        return [
            {
                'title': book['volumeInfo'].get('title'),
                'authors': book['volumeInfo'].get('authors', []),
                'download_link': book['accessInfo'].get('webReaderLink', 'N/A')
            }
            for book in books
        ]
    except requests.RequestException as e:
        print(f"Error fetching data from Google Books: {e}")
        return []

def search_open_library(book_name, author_name):
    """Search Open Library API for books by author and title."""
    api_url = "https://openlibrary.org/search.json"
    params = {
        'title': book_name,
        'author': author_name
    }
    try:
        response = requests.get(api_url, params=params)
        response.raise_for_status()
        books = response.json().get('docs', [])
        return [
            {
                'title': book.get('title'),
                'authors': book.get('author_name', []),
                'download_link': f"https://openlibrary.org{book.get('key')}"
            }
            for book in books
        ]
    except requests.RequestException as e:
        print(f"Error fetching data from Open Library: {e}")
        return []

def fetch_books():
    print("Welcome to the Book Fetcher!")
    book_name = input("Enter the book name: ").strip()
    author_name = input("Enter the author's name: ").strip()

    if not book_name or not author_name:
        print("Both book name and author name are required.")
        return

    print("Fetching books from Google Books...")
    google_books = search_google_books(book_name, author_name)
    print(f"Found {len(google_books)} books on Google Books.")

    print("Fetching books from Open Library...")
    open_library_books = search_open_library(book_name, author_name)
    print(f"Found {len(open_library_books)} books on Open Library.")

    all_books = google_books + open_library_books

    if not all_books:
        print("No books found for your query.")
        return

    print("\nBooks found:")
    for idx, book in enumerate(all_books, start=1):
        title = book['title']
        authors = ", ".join(book['authors'])
        download_link = book['download_link']
        print(f"{idx}. {title} by {authors}\n   Download/Read Link: {download_link}\n")

if __name__ == "__main__":
    fetch_books()
