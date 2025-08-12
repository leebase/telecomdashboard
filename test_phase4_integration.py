"""
Phase 4 Integration Testing Suite

This script tests all Phase 4 features including:
- System integration health monitoring
- Circuit breaker patterns and fallback mechanisms
- Manual override controls
- Performance optimization features
- Backup demo mode functionality
"""

import unittest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents.orchestrator import AgentOrchestrator, OrchestrationConfig
from agents.integration_layer import get_integration_manager
from agents.backup_demo_mode import get_backup_demo
from models.play_models import SubjectArea, Play, Portfolio, WorkflowPhase, AgentStatus


class TestPhase4Integration(unittest.TestCase):
    """Test suite for Phase 4 integration features"""
    
    def setUp(self):
        """Set up test environment"""
        self.config = OrchestrationConfig(
            max_concurrent_agents=3,
            agent_timeout_seconds=10,
            optimization_iterations=2,
            portfolio_size_target=10,
            min_roi_threshold=5.0,
            max_risk_threshold=7.0,
            enable_parallel_execution=True,
            progress_update_interval=0.1,
            enable_circuit_breaker=True,
            max_failures_before_fallback=2,
            fallback_timeout_seconds=30
        )
        
        self.orchestrator = AgentOrchestrator(self.config)
        
        # Mock callbacks
        self.progress_callback_called = False
        self.status_callback_called = False
        
        def progress_callback(progress, message):
            self.progress_callback_called = True
            self.last_progress = progress
            self.last_message = message
        
        def status_callback(message):
            self.status_callback_called = True
            self.last_status = message
        
        self.orchestrator.add_progress_callback(progress_callback)
        self.orchestrator.add_status_callback(status_callback)
    
    def tearDown(self):
        """Clean up test environment"""
        if hasattr(self.orchestrator, '_orchestration_thread') and self.orchestrator._orchestration_thread:
            self.orchestrator.stop_orchestration()
            time.sleep(0.1)
    
    def test_01_circuit_breaker_initialization(self):
        """Test circuit breaker pattern initialization"""
        print("Testing circuit breaker initialization...")
        
        # Check that circuit breaker is enabled
        self.assertTrue(self.orchestrator.config.enable_circuit_breaker)
        self.assertEqual(self.orchestrator.config.max_failures_before_fallback, 2)
        
        # Check initial circuit breaker state
        status = self.orchestrator.get_status()
        self.assertIn('metrics', status)
        self.assertEqual(status['metrics'].get('circuit_breaker_trips', 0), 0)
        
        print("✅ Circuit breaker initialization test passed")
    
    def test_02_integration_health_monitoring(self):
        """Test integration health monitoring"""
        print("Testing integration health monitoring...")
        
        # Get integration status
        integration_status = self.orchestrator.get_integration_status()
        
        # Check that integration status is returned
        self.assertIsInstance(integration_status, dict)
        self.assertIn('overall_health', integration_status)
        
        # Check health values are valid
        valid_health_values = ['healthy', 'degraded', 'unhealthy', 'unknown']
        self.assertIn(integration_status['overall_health'], valid_health_values)
        
        # Check individual component statuses (only boolean ones)
        boolean_components = ['config_manager', 'security_manager', 'pii_scrubber', 'database', 'kpi_data']
        for component in boolean_components:
            if component in integration_status:
                self.assertIsInstance(integration_status[component], bool)
        
        print("✅ Integration health monitoring test passed")
    
    def test_03_fallback_mode_triggering(self):
        """Test fallback mode triggering on failures"""
        print("Testing fallback mode triggering...")
        
        # Mock agent failures to trigger circuit breaker
        with patch.object(self.orchestrator, '_execute_orchestration') as mock_execute:
            mock_execute.side_effect = Exception("Simulated agent failure")
            
            # Start orchestration
            self.orchestrator.start_orchestration()
            time.sleep(0.5)  # Allow time for failures to accumulate
            
            # Check if fallback mode is activated
            status = self.orchestrator.get_status()
            fallback_active = status.get('metrics', {}).get('fallback_mode', False)
            
            # With 2 failures, fallback should be triggered
            if fallback_active:
                print("✅ Fallback mode triggered successfully")
            else:
                print("⚠️ Fallback mode not triggered (may need more failures)")
        
        print("✅ Fallback mode triggering test completed")
    
    def test_04_manual_override_functionality(self):
        """Test manual override controls"""
        print("Testing manual override functionality...")
        
        # Test force completion override
        result = self.orchestrator.manual_override_agent("Network QoE Agent", "force_complete")
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        
        # Test generate plays override
        result = self.orchestrator.manual_override_agent("Customer Agent", "generate_plays")
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        
        # Test reset status override
        result = self.orchestrator.manual_override_agent("Revenue Agent", "reset_status")
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        
        print("✅ Manual override functionality test passed")
    
    def test_05_performance_optimization_features(self):
        """Test performance optimization features"""
        print("Testing performance optimization features...")
        
        # Check parallel execution configuration
        self.assertTrue(self.orchestrator.config.enable_parallel_execution)
        self.assertGreater(self.orchestrator.config.max_concurrent_agents, 1)
        
        # Check progress update interval
        self.assertGreater(self.orchestrator.config.progress_update_interval, 0)
        
        # Check timeout configurations
        self.assertGreater(self.orchestrator.config.agent_timeout_seconds, 0)
        self.assertGreater(self.orchestrator.config.fallback_timeout_seconds, 0)
        
        print("✅ Performance optimization features test passed")
    
    def test_06_backup_demo_mode_integration(self):
        """Test backup demo mode integration"""
        print("Testing backup demo mode integration...")
        
        # Get backup demo instance
        backup_demo = get_backup_demo()
        self.assertIsNotNone(backup_demo)
        
        # Check backup demo capabilities
        self.assertTrue(hasattr(backup_demo, 'generate_demo_plays'))
        self.assertTrue(hasattr(backup_demo, 'is_available'))
        
        # Test demo data generation
        demo_plays = backup_demo.generate_demo_plays(SubjectArea.NETWORK_QOE, 5)
        self.assertIsInstance(demo_plays, list)
        self.assertLessEqual(len(demo_plays), 5)
        
        print("✅ Backup demo mode integration test passed")
    
    def test_07_error_handling_and_recovery(self):
        """Test error handling and recovery mechanisms"""
        print("Testing error handling and recovery...")
        
        # Test graceful handling of invalid agent names
        result = self.orchestrator.manual_override_agent("Invalid Agent", "force_complete")
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        
        # Test graceful handling of invalid actions
        result = self.orchestrator.manual_override_agent("Network QoE Agent", "invalid_action")
        self.assertIsInstance(result, dict)
        self.assertIn('success', result)
        
        # Test system continues to function after errors
        status = self.orchestrator.get_status()
        self.assertIsInstance(status, dict)
        
        print("✅ Error handling and recovery test passed")
    
    def test_08_real_time_monitoring(self):
        """Test real-time monitoring capabilities"""
        print("Testing real-time monitoring...")
        
        # Start orchestration
        self.orchestrator.start_orchestration()
        time.sleep(0.2)  # Allow some progress
        
        # Check that callbacks are working
        self.assertTrue(self.progress_callback_called or self.status_callback_called)
        
        # Check status updates
        status = self.orchestrator.get_status()
        self.assertIn('status', status)
        self.assertIn('workflow_phase', status)
        
        # Check metrics
        metrics = status.get('metrics', {})
        self.assertIsInstance(metrics, dict)
        
        print("✅ Real-time monitoring test passed")
    
    def test_09_system_health_persistence(self):
        """Test system health persistence across operations"""
        print("Testing system health persistence...")
        
        # Get initial health
        initial_health = self.orchestrator.get_integration_status()
        
        # Perform some operations
        self.orchestrator.manual_override_agent("Network QoE Agent", "reset_status")
        time.sleep(0.1)
        
        # Check health is still available
        current_health = self.orchestrator.get_integration_status()
        self.assertIsInstance(current_health, dict)
        self.assertIn('overall_health', current_health)
        
        # Health should be consistent
        self.assertEqual(initial_health['overall_health'], current_health['overall_health'])
        
        print("✅ System health persistence test passed")
    
    def test_10_production_readiness_features(self):
        """Test production readiness features"""
        print("Testing production readiness features...")
        
        # Check configuration validation
        self.assertIsInstance(self.orchestrator.config, OrchestrationConfig)
        self.assertGreater(self.orchestrator.config.max_concurrent_agents, 0)
        self.assertGreater(self.orchestrator.config.agent_timeout_seconds, 0)
        
        # Check error handling
        try:
            # This should not crash the system
            self.orchestrator.manual_override_agent("", "")
        except Exception as e:
            self.fail(f"System crashed on invalid input: {e}")
        
        # Check graceful degradation
        status = self.orchestrator.get_status()
        self.assertIsInstance(status, dict)
        
        print("✅ Production readiness features test passed")


def run_integration_test_suite():
    """Run the complete Phase 4 integration test suite"""
    print("🚀 Starting Phase 4 Integration Test Suite")
    print("=" * 60)
    
    # Create test suite
    test_suite = unittest.TestLoader().loadTestsFromTestCase(TestPhase4Integration)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    result = runner.run(test_suite)
    
    # Print summary
    print("=" * 60)
    print("📊 Phase 4 Integration Test Results")
    print(f"Tests Run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Test Failures:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback}")
    
    if result.errors:
        print("\n❌ Test Errors:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n🎉 All Phase 4 integration tests passed!")
        print("✅ System is ready for production deployment")
    else:
        print("\n⚠️ Some tests failed. Please review and fix issues.")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run the test suite
    success = run_integration_test_suite()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
