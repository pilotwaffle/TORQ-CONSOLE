"""
TORQ Console PWA (Progressive Web App) Support

Service worker, manifest, and offline functionality for mobile and desktop.
"""

from .manifest import generate_manifest
from .service_worker import generate_service_worker
from .register import register_service_worker

__all__ = [
    'generate_manifest',
    'generate_service_worker',
    'register_service_worker'
]

__version__ = '1.0.0'
