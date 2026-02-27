#!/usr/bin/env python3
"""
Web server launcher for the Bybit Grid Trading Bot.

This script starts the FastAPI web server with the trading bot interface.
"""

import argparse
import asyncio
import sys
import uvicorn
from pathlib import Path

from web.app import create_app
from utils.logger import setup_logger, get_logger
from utils.config import load_config


def main():
    """Main entry point for the web server."""
    parser = argparse.ArgumentParser(
        description="Bybit Grid Trading Bot - Web Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind the server to (default: 8000)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logger(log_level=args.log_level, log_file="logs/web.log")
    logger = get_logger("WebServer")
    
    # Validate configuration
    try:
        config = load_config(args.config)
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        sys.exit(1)
    
    # Create FastAPI app
    app = create_app()
    
    # Server configuration
    server_config = {
        "app": app,
        "host": args.host,
        "port": args.port,
        "log_level": args.log_level.lower(),
        "access_log": True,
        "reload": args.reload
    }
    
    logger.info(f"Starting web server on {args.host}:{args.port}")
    logger.info(f"Web interface will be available at: http://{args.host}:{args.port}")
    
    if args.reload:
        logger.info("Auto-reload enabled for development")
    
    try:
        # Start the server
        uvicorn.run(**server_config)
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
