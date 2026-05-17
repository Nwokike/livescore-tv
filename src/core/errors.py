class NetworkError(Exception):
    """Raised when a network request fails."""


class ScraperError(Exception):
    """Raised when web scraping fails."""


class StreamResolutionError(Exception):
    """Raised when a stream URL cannot be resolved."""


class CacheError(Exception):
    """Raised when cache operations fail."""
