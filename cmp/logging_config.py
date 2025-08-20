import logging
import sys
from pathlib import Path

from .config import settings


def setup_logging() -> None:
    """Configure logging for the CMP application"""
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO if settings.env == "production" else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler
            logging.FileHandler(logs_dir / "cmp.log"),
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Create AI agent loggers
    for agent in ["accountant", "controller", "director", "cfo"]:
        agent_logger = logging.getLogger(f"cmp.agents.{agent}")
        agent_logger.setLevel(logging.INFO)
        
        # Add agent-specific file handler
        agent_handler = logging.FileHandler(logs_dir / f"agent_{agent}.log")
        agent_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        agent_logger.addHandler(agent_handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the given name"""
    return logging.getLogger(f"cmp.{name}")
