"""Async query execution and optimization utilities."""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class QueryExecutionResult:
    """Result of an async query execution."""
    query_id: str
    dataframe: Optional[pd.DataFrame]
    execution_time: float
    error: Optional[str]
    metadata: Dict[str, Any]


class AsyncQueryExecutor:
    """Async query executor with thread pool management."""

    def __init__(self, max_workers: int = 4, timeout: int = 300):
        self.max_workers = max_workers
        self.timeout = timeout
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    async def execute_query_async(self,
                                 query_func: Callable,
                                 query_id: str,
                                 *args,
                                 **kwargs) -> QueryExecutionResult:
        """Execute a query asynchronously."""
        start_time = time.time()

        try:
            # Run query in thread pool
            future = self.loop.run_in_executor(
                self.executor,
                query_func,
                *args,
                **kwargs
            )

            dataframe = await asyncio.wait_for(future, timeout=self.timeout)
            execution_time = time.time() - start_time

            return QueryExecutionResult(
                query_id=query_id,
                dataframe=dataframe,
                execution_time=execution_time,
                error=None,
                metadata={"status": "success"}
            )

        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            return QueryExecutionResult(
                query_id=query_id,
                dataframe=None,
                execution_time=execution_time,
                error=f"Query timeout after {self.timeout}s",
                metadata={"status": "timeout"}
            )

        except Exception as e:
            execution_time = time.time() - start_time
            return QueryExecutionResult(
                query_id=query_id,
                dataframe=None,
                execution_time=execution_time,
                error=str(e),
                metadata={"status": "error", "error_type": type(e).__name__}
            )

    async def execute_multiple_queries(self,
                                      queries: List[Dict[str, Any]]) -> List[QueryExecutionResult]:
        """Execute multiple queries concurrently."""
        tasks = []

        for query_spec in queries:
            query_func = query_spec["func"]
            query_id = query_spec["id"]
            args = query_spec.get("args", [])
            kwargs = query_spec.get("kwargs", {})

            task = self.execute_query_async(query_func, query_id, *args, **kwargs)
            tasks.append(task)

        # Execute all queries concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle any exceptions that occurred during gather
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error result for failed task
                final_results.append(QueryExecutionResult(
                    query_id=queries[i]["id"],
                    dataframe=None,
                    execution_time=0.0,
                    error=f"Task failed: {result}",
                    metadata={"status": "task_error"}
                ))
            else:
                final_results.append(result)

        return final_results

    def shutdown(self):
        """Shutdown the executor."""
        self.executor.shutdown(wait=True)
        self.loop.close()


class QueryOptimizer:
    """Query optimization utilities."""

    def __init__(self):
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.execution_stats: Dict[str, List[float]] = {}

    def optimize_query(self, sql: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Apply basic query optimizations."""
        optimized = sql

        # Remove unnecessary whitespace
        optimized = ' '.join(optimized.split())

        # Add query hints for better performance (database-specific)
        if "SELECT" in optimized.upper():
            # Add LIMIT if not present and result set might be large
            if "LIMIT" not in optimized.upper() and len(optimized) > 100:
                optimized += " LIMIT 10000"  # Reasonable default limit

        return optimized

    def should_use_cache(self, query_hash: str, max_age: int = 300) -> bool:
        """Determine if cached result should be used."""
        if query_hash not in self.query_cache:
            return False

        cache_entry = self.query_cache[query_hash]
        cache_age = time.time() - cache_entry["timestamp"]

        return cache_age < max_age

    def get_cached_result(self, query_hash: str) -> Optional[pd.DataFrame]:
        """Get cached query result."""
        if self.should_use_cache(query_hash):
            return self.query_cache[query_hash]["result"]
        return None

    def cache_result(self, query_hash: str, result: pd.DataFrame):
        """Cache query result."""
        self.query_cache[query_hash] = {
            "result": result.copy(),
            "timestamp": time.time()
        }

        # Keep cache size manageable
        if len(self.query_cache) > 100:
            # Remove oldest entries
            oldest_key = min(self.query_cache.keys(),
                           key=lambda k: self.query_cache[k]["timestamp"])
            del self.query_cache[oldest_key]

    def record_execution_time(self, query_hash: str, execution_time: float):
        """Record query execution time for analysis."""
        if query_hash not in self.execution_stats:
            self.execution_stats[query_hash] = []

        self.execution_stats[query_hash].append(execution_time)

        # Keep only last 10 executions
        if len(self.execution_stats[query_hash]) > 10:
            self.execution_stats[query_hash].pop(0)

    def get_query_performance_stats(self, query_hash: str) -> Dict[str, Any]:
        """Get performance statistics for a query."""
        if query_hash not in self.execution_stats:
            return {"executions": 0, "avg_time": 0, "min_time": 0, "max_time": 0}

        times = self.execution_stats[query_hash]
        return {
            "executions": len(times),
            "avg_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times)
        }

    def identify_slow_queries(self, threshold: float = 5.0) -> List[Dict[str, Any]]:
        """Identify queries that are running slower than threshold."""
        slow_queries = []

        for query_hash, times in self.execution_stats.items():
            avg_time = sum(times) / len(times)
            if avg_time > threshold:
                slow_queries.append({
                    "query_hash": query_hash,
                    "avg_execution_time": avg_time,
                    "execution_count": len(times),
                    "last_execution": max(times) if times else 0
                })

        return sorted(slow_queries, key=lambda x: x["avg_execution_time"], reverse=True)


class LoadTestRunner:
    """Load testing framework for queries."""

    def __init__(self, query_executor: AsyncQueryExecutor):
        self.executor = query_executor
        self.results: List[Dict[str, Any]] = []

    async def run_load_test(self,
                           query_func: Callable,
                           query_id: str,
                           concurrent_users: int = 10,
                           duration_seconds: int = 60,
                           *args,
                           **kwargs) -> Dict[str, Any]:
        """Run load test with specified parameters."""
        start_time = time.time()
        end_time = start_time + duration_seconds

        completed_queries = 0
        failed_queries = 0
        response_times = []

        logger.info(f"Starting load test: {concurrent_users} users, {duration_seconds}s duration")

        while time.time() < end_time:
            # Create batch of concurrent queries
            query_specs = []
            for i in range(concurrent_users):
                query_specs.append({
                    "func": query_func,
                    "id": f"{query_id}_{completed_queries + i}",
                    "args": args,
                    "kwargs": kwargs
                })

            # Execute batch
            try:
                results = await self.executor.execute_multiple_queries(query_specs)

                for result in results:
                    if result.error:
                        failed_queries += 1
                    else:
                        completed_queries += 1
                        response_times.append(result.execution_time)

            except Exception as e:
                logger.error(f"Load test batch error: {e}")
                failed_queries += concurrent_users

            # Small delay between batches
            await asyncio.sleep(0.1)

        total_time = time.time() - start_time
        actual_duration = min(total_time, duration_seconds)

        # Calculate metrics
        total_requests = completed_queries + failed_queries
        requests_per_second = total_requests / actual_duration if actual_duration > 0 else 0
        success_rate = (completed_queries / total_requests * 100) if total_requests > 0 else 0

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        min_response_time = min(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0

        # Calculate percentiles
        if response_times:
            sorted_times = sorted(response_times)
            p50 = sorted_times[int(len(sorted_times) * 0.5)]
            p95 = sorted_times[int(len(sorted_times) * 0.95)]
            p99 = sorted_times[int(len(sorted_times) * 0.99)]
        else:
            p50 = p95 = p99 = 0

        result = {
            "test_duration": actual_duration,
            "total_requests": total_requests,
            "completed_queries": completed_queries,
            "failed_queries": failed_queries,
            "requests_per_second": requests_per_second,
            "success_rate": success_rate,
            "avg_response_time": avg_response_time,
            "min_response_time": min_response_time,
            "max_response_time": max_response_time,
            "p50_response_time": p50,
            "p95_response_time": p95,
            "p99_response_time": p99,
            "concurrent_users": concurrent_users
        }

        self.results.append(result)
        return result

    def get_test_summary(self) -> Dict[str, Any]:
        """Get summary of all load tests."""
        if not self.results:
            return {"total_tests": 0}

        total_tests = len(self.results)
        avg_rps = sum(r["requests_per_second"] for r in self.results) / total_tests
        avg_success_rate = sum(r["success_rate"] for r in self.results) / total_tests

        return {
            "total_tests": total_tests,
            "avg_requests_per_second": avg_rps,
            "avg_success_rate": avg_success_rate,
            "best_test": max(self.results, key=lambda x: x["requests_per_second"]),
            "worst_test": min(self.results, key=lambda x: x["success_rate"])
        }


# Global instances
async_executor = AsyncQueryExecutor()
query_optimizer = QueryOptimizer()
load_tester = LoadTestRunner(async_executor)


__all__ = [
    "QueryExecutionResult",
    "AsyncQueryExecutor",
    "QueryOptimizer",
    "LoadTestRunner",
    "async_executor",
    "query_optimizer",
    "load_tester"
]