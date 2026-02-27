#!/usr/bin/env python3
"""
Bybit Grid Trading Bot

A sophisticated grid trading bot for Bybit SPOT trading with individual
Take Profit levels for each grid position.

Usage:
    python main.py [--config CONFIG_PATH] [--mode MODE]

Modes:
    - run: Start the trading bot (default)
    - status: Show current status
    - stop: Stop the trading bot
    - reset: Reset emergency stop
"""

import asyncio
import argparse
import sys
from pathlib import Path

from core.trading_engine import TradingEngine
from utils.logger import setup_logger


async def run_trading_bot(config_path: str = None) -> None:
    """
    Run the trading bot.

    Args:
        config_path: Path to configuration file
    """
    engine = None
    try:
        # Create and initialize trading engine
        engine = TradingEngine(config_path)

        # Start the engine
        await engine.start()

        print("Trading bot started successfully!")
        print("Press Ctrl+C to stop the bot")

        # Keep running until interrupted
        while engine.is_running:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutdown signal received...")
    except Exception as e:
        print(f"Error running trading bot: {e}")
        return 1
    finally:
        if engine:
            await engine.stop()
        print("Trading bot stopped")

    return 0


async def show_status(config_path: str = None) -> None:
    """
    Show current bot status.

    Args:
        config_path: Path to configuration file
    """
    try:
        engine = TradingEngine(config_path)
        success = await engine.initialize()

        if not success:
            print("Failed to initialize trading engine")
            return 1

        status = engine.get_status()
        performance = engine.get_performance_summary()

        print("=== Trading Bot Status ===")
        print(f"Running: {status['is_running']}")
        print(f"Initialized: {status['is_initialized']}")
        print(f"Uptime: {status['uptime_seconds']:.0f} seconds")

        print("\n=== Components ===")
        for component, running in status['components'].items():
            print(f"{component}: {'✓' if running else '✗'}")

        if 'grid_status' in status:
            grid = status['grid_status']
            print(f"\n=== Grid Status ===")
            print(f"Symbol: {grid['config']['symbol']}")
            print(f"Total Levels: {grid['total_levels']}")
            print(f"Last Price: {grid['last_market_price']}")
            print(f"Cycles Completed: {grid['total_cycles_completed']}")
            print(f"Total Profit: {grid['total_profit_realized']}")

        if 'risk_status' in status:
            risk = status['risk_status']
            print(f"\n=== Risk Status ===")
            print(f"Emergency Stop: {'✓' if risk['emergency_stop'] else '✗'}")
            print(f"Positions: {risk['current_positions']}/{risk['max_positions']}")
            print(f"Daily PnL: {risk['daily_pnl']}")
            print(f"Win Rate: {risk['win_rate']:.1f}%")

        await engine.cleanup()
        return 0

    except Exception as e:
        print(f"Error getting status: {e}")
        return 1


async def emergency_stop(config_path: str = None) -> None:
    """
    Trigger emergency stop.

    Args:
        config_path: Path to configuration file
    """
    try:
        engine = TradingEngine(config_path)
        success = await engine.initialize()

        if not success:
            print("Failed to initialize trading engine")
            return 1

        await engine.emergency_stop("Manual emergency stop via CLI")
        print("Emergency stop triggered")

        await engine.cleanup()
        return 0

    except Exception as e:
        print(f"Error triggering emergency stop: {e}")
        return 1


async def reset_emergency_stop(config_path: str = None) -> None:
    """
    Reset emergency stop.

    Args:
        config_path: Path to configuration file
    """
    try:
        engine = TradingEngine(config_path)
        success = await engine.initialize()

        if not success:
            print("Failed to initialize trading engine")
            return 1

        await engine.reset_emergency_stop()
        print("Emergency stop reset")

        await engine.cleanup()
        return 0

    except Exception as e:
        print(f"Error resetting emergency stop: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bybit Grid Trading Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file (default: config/config.yaml)"
    )

    parser.add_argument(
        "--mode",
        choices=["run", "status", "stop", "reset"],
        default="run",
        help="Operation mode (default: run)"
    )

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="Logging level (default: INFO)"
    )

    args = parser.parse_args()

    # Setup basic logging for CLI
    setup_logger(log_level=args.log_level)

    # Validate config file
    if args.config and not Path(args.config).exists():
        print(f"Configuration file not found: {args.config}")
        return 1

    # Run appropriate mode
    try:
        if args.mode == "run":
            exit_code = asyncio.run(run_trading_bot(args.config))
        elif args.mode == "status":
            exit_code = asyncio.run(show_status(args.config))
        elif args.mode == "stop":
            exit_code = asyncio.run(emergency_stop(args.config))
        elif args.mode == "reset":
            exit_code = asyncio.run(reset_emergency_stop(args.config))
        else:
            print(f"Unknown mode: {args.mode}")
            exit_code = 1

        sys.exit(exit_code)

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
