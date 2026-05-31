#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blogplatform.settings')
    
    # Task 1 & 2: Monkeypatch Django's autoreloader to completely ignore the media folder
    # This prevents infinite loops, aborted uploads, and spam logs during ImageField uploads.
    try:
        from django.utils import autoreload
        
        # Patch BaseReloader.watch_dir
        original_watch_dir = autoreload.BaseReloader.watch_dir
        def new_watch_dir(self, path, glob):
            try:
                from django.conf import settings
                media_root = str(settings.MEDIA_ROOT).replace('\\', '/')
                path_str = str(path).replace('\\', '/')
                if media_root in path_str or '/media/' in path_str or path_str.endswith('/media') or 'media' in path_str:
                    return  # Skip watching the media directory
            except Exception:
                pass
            return original_watch_dir(self, path, glob)
        autoreload.BaseReloader.watch_dir = new_watch_dir

        # Patch BaseReloader.watch_file
        original_watch_file = autoreload.BaseReloader.watch_file
        def new_watch_file(self, path):
            try:
                from django.conf import settings
                media_root = str(settings.MEDIA_ROOT).replace('\\', '/')
                path_str = str(path).replace('\\', '/')
                if media_root in path_str or '/media/' in path_str or 'media' in path_str:
                    return  # Skip watching media files
            except Exception:
                pass
            return original_watch_file(self, path)
        autoreload.BaseReloader.watch_file = new_watch_file
    except Exception:
        pass

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
