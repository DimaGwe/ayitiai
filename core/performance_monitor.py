"""
Performance Monitoring for AYITI AI
Tracks request metrics and system performance
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import defaultdict, deque
import logging
import time

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """
    Monitor system performance metrics
    Features:
    - Request latency tracking
    - Throughput measurement
    - Error rate monitoring
    - Resource usage tracking
    """

    def __init__(self, window_size: int = 100):
        """
        Initialize performance monitor

        Args:
            window_size: Number of recent requests to track
        """
        self.window_size = window_size
        self.request_times = deque(maxlen=window_size)
        self.request_costs = deque(maxlen=window_size)
        self.error_count = 0
        self.total_requests = 0

        # Sector-specific metrics
        self.sector_latencies = defaultdict(list)
        self.sector_counts = defaultdict(int)

        # Language-specific metrics
        self.language_latencies = defaultdict(list)
        self.language_counts = defaultdict(int)

        self.start_time = datetime.now()

    def record_request(
        self,
        latency: float,
        cost: float,
        sector: str,
        language: str,
        success: bool = True
    ) -> None:
        """
        Record a request for metrics

        Args:
            latency: Request latency in seconds
            cost: Request cost in USD
            sector: Primary sector
            language: Language code
            success: Whether request was successful
        """
        self.total_requests += 1

        if success:
            self.request_times.append(latency)
            self.request_costs.append(cost)

            # Track by sector
            self.sector_latencies[sector].append(latency)
            self.sector_counts[sector] += 1

            # Track by language
            self.language_latencies[language].append(latency)
            self.language_counts[language] += 1
        else:
            self.error_count += 1

    def get_metrics(self) -> Dict:
        """
        Get current performance metrics

        Returns:
            Dict with performance statistics
        """
        if not self.request_times:
            return {
                "status": "no_data",
                "message": "No requests recorded yet"
            }

        # Calculate latency statistics
        latencies = list(self.request_times)
        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        # Calculate percentiles
        sorted_latencies = sorted(latencies)
        p50_index = int(len(sorted_latencies) * 0.5)
        p95_index = int(len(sorted_latencies) * 0.95)
        p99_index = int(len(sorted_latencies) * 0.99)

        p50_latency = sorted_latencies[p50_index] if p50_index < len(sorted_latencies) else 0
        p95_latency = sorted_latencies[p95_index] if p95_index < len(sorted_latencies) else 0
        p99_latency = sorted_latencies[p99_index] if p99_index < len(sorted_latencies) else 0

        # Calculate cost statistics
        costs = list(self.request_costs)
        total_cost = sum(costs)
        avg_cost = total_cost / len(costs) if costs else 0

        # Calculate throughput
        uptime = (datetime.now() - self.start_time).total_seconds()
        requests_per_second = self.total_requests / uptime if uptime > 0 else 0

        # Error rate
        error_rate = self.error_count / self.total_requests if self.total_requests > 0 else 0

        return {
            "latency": {
                "avg_seconds": round(avg_latency, 3),
                "min_seconds": round(min_latency, 3),
                "max_seconds": round(max_latency, 3),
                "p50_seconds": round(p50_latency, 3),
                "p95_seconds": round(p95_latency, 3),
                "p99_seconds": round(p99_latency, 3)
            },
            "cost": {
                "total_usd": round(total_cost, 4),
                "avg_per_request_usd": round(avg_cost, 4)
            },
            "throughput": {
                "total_requests": self.total_requests,
                "successful_requests": self.total_requests - self.error_count,
                "error_count": self.error_count,
                "error_rate": round(error_rate, 4),
                "requests_per_second": round(requests_per_second, 2)
            },
            "uptime_seconds": round(uptime, 2)
        }

    def get_sector_metrics(self) -> Dict:
        """
        Get metrics broken down by sector

        Returns:
            Dict with sector-specific metrics
        """
        sector_stats = {}

        for sector, latencies in self.sector_latencies.items():
            if latencies:
                sector_stats[sector] = {
                    "request_count": self.sector_counts[sector],
                    "avg_latency_seconds": round(sum(latencies) / len(latencies), 3),
                    "min_latency_seconds": round(min(latencies), 3),
                    "max_latency_seconds": round(max(latencies), 3)
                }

        return sector_stats

    def get_language_metrics(self) -> Dict:
        """
        Get metrics broken down by language

        Returns:
            Dict with language-specific metrics
        """
        language_stats = {}

        for language, latencies in self.language_latencies.items():
            if latencies:
                language_stats[language] = {
                    "request_count": self.language_counts[language],
                    "avg_latency_seconds": round(sum(latencies) / len(latencies), 3),
                    "percentage_of_total": round(
                        self.language_counts[language] / self.total_requests * 100, 2
                    ) if self.total_requests > 0 else 0
                }

        return language_stats

    def get_full_report(self) -> Dict:
        """
        Get comprehensive performance report

        Returns:
            Full performance report
        """
        return {
            "overall": self.get_metrics(),
            "by_sector": self.get_sector_metrics(),
            "by_language": self.get_language_metrics(),
            "system_info": {
                "start_time": self.start_time.isoformat(),
                "window_size": self.window_size
            }
        }

    def reset(self) -> None:
        """Reset all metrics"""
        self.request_times.clear()
        self.request_costs.clear()
        self.sector_latencies.clear()
        self.sector_counts.clear()
        self.language_latencies.clear()
        self.language_counts.clear()
        self.error_count = 0
        self.total_requests = 0
        self.start_time = datetime.now()

        logger.info("Performance metrics reset")


# Global instance
performance_monitor = PerformanceMonitor()
