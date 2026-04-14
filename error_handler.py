import traceback
import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def safe_handler(func):
    """Decorator to securely handle exceptions in async functions without crashing."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logging.error(f"❌ [CRITICAL ERROR] in {func.__name__}: {e}")
            traceback.print_exc()
            
            # Optionally notify user if Update object is in args
            update = next((arg for arg in args if isinstance(arg, Update)), None)
            if update and getattr(update, 'message', None):
                try:
                    await update.message.reply_text("⚠️ An internal error occurred. Please try again later.")
                except Exception:
                    pass
            return None
    return wrapper

def safe_sync(func):
    """Decorator to safely handle exceptions in sync functions."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logging.error(f"❌ [CRITICAL ERROR] in {func.__name__}: {e}")
            traceback.print_exc()
            return None
    return wrapper
