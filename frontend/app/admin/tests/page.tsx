'use client';

import { useState } from 'react';

interface TestResult {
  service: string;
  status: 'idle' | 'running' | 'passed' | 'failed';
  totalTests: number;
  passedTests: number;
  failedTests: number;
  duration: number;
  output: string;
}

// Mock data for demonstration
const mockTestResults: TestResult[] = [
  {
    service: 'api-gateway',
    status: 'passed',
    totalTests: 52,
    passedTests: 52,
    failedTests: 0,
    duration: 173,
    output: 'Found 52 test(s).\nCreating test database...\nSystem check identified no issues.\n........................\nRan 52 tests in 0.173s\nOK'
  },
  {
    service: 'product-service',
    status: 'passed',
    totalTests: 24,
    passedTests: 24,
    failedTests: 0,
    duration: 122,
    output: 'Found 24 test(s).\nCreating test database...\nSystem check identified no issues.\n........................\nRan 24 tests in 0.122s\nOK'
  },
  {
    service: 'user-service',
    status: 'passed',
    totalTests: 23,
    passedTests: 23,
    failedTests: 0,
    duration: 144,
    output: 'Found 23 test(s).\nCreating test database...\nSystem check identified no issues.\n.......................\nRan 23 tests in 0.144s\nOK'
  },
  {
    service: 'inventory-service',
    status: 'passed',
    totalTests: 23,
    passedTests: 23,
    failedTests: 0,
    duration: 94,
    output: 'Found 23 test(s).\nCreating test database...\nSystem check identified no issues.\n.......................\nRan 23 tests in 0.094s\nOK'
  },
  {
    service: 'order-service',
    status: 'passed',
    totalTests: 23,
    passedTests: 23,
    failedTests: 0,
    duration: 84,
    output: 'Found 23 test(s).\nCreating test database...\nSystem check identified no issues.\n.......................\nRan 23 tests in 0.084s\nOK'
  },
  {
    service: 'payment-service',
    status: 'passed',
    totalTests: 27,
    passedTests: 27,
    failedTests: 0,
    duration: 110,
    output: 'Found 27 test(s).\nCreating test database...\nSystem check identified no issues.\n...........................\nRan 27 tests in 0.110s\nOK'
  },
];

const services = [
  { name: 'api-gateway', displayName: 'API Gateway', port: 8000, endpoint: 'gateway/tests' },
  { name: 'product-service', displayName: 'Product Service', port: 8001, endpoint: 'api/products/tests' },
  { name: 'user-service', displayName: 'User Service', port: 8002, endpoint: 'api/users/tests' },
  { name: 'inventory-service', displayName: 'Inventory Service', port: 8003, endpoint: 'api/inventory/tests' },
  { name: 'order-service', displayName: 'Order Service', port: 8004, endpoint: 'api/orders/tests' },
  { name: 'payment-service', displayName: 'Payment Service', port: 8005, endpoint: 'api/payments/tests' },
];

const UnitTestsPage = () => {
  const [testResults, setTestResults] = useState(mockTestResults);
  const [isRunningAll, setIsRunningAll] = useState(false);
  const [overallStats, setOverallStats] = useState({
    total: 172,
    passed: 172,
    failed: 0,
    running: 0,
  });

  const runAllTests = async () => {
    setIsRunningAll(true);
    setOverallStats({ total: 0, passed: 0, failed: 0, running: services.length });

    // Simulate running tests
    const results = [...mockTestResults];
    setTestResults(results.map(result => ({ ...result, status: 'running' as const })));

    // Simulate test execution with delays
    for (let i = 0; i < results.length; i++) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      results[i].status = 'passed';
      setTestResults([...results]);
    }

    setIsRunningAll(false);
    setOverallStats({ total: 172, passed: 172, failed: 0, running: 0 });
  };

  const runSingleTest = async (serviceName: string) => {
    const results = [...testResults];
    const index = results.findIndex(r => r.service === serviceName);
    if (index !== -1) {
      results[index].status = 'running';
      setTestResults([...results]);

      // Simulate test execution
      await new Promise(resolve => setTimeout(resolve, 1500));
      results[index].status = 'passed';
      setTestResults([...results]);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'passed': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'running': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'passed': return '✅';
      case 'failed': return '❌';
      case 'running': return '⏳';
      default: return '⏸️';
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Unit Test Dashboard</h1>
        <p className="text-gray-600">Run and monitor unit tests for all microservices</p>
        <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-blue-800">
            <strong>Note:</strong> This is a demonstration interface showing mock test results.
            In a production environment, this would connect to actual test endpoints in each microservice.
          </p>
        </div>
      </div>

      {/* Overall Statistics */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold mb-4">Overall Statistics</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{overallStats.total}</div>
            <div className="text-sm text-gray-600">Total Tests</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{overallStats.passed}</div>
            <div className="text-sm text-gray-600">Passed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">{overallStats.failed}</div>
            <div className="text-sm text-gray-600">Failed</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{overallStats.running}</div>
            <div className="text-sm text-gray-600">Running</div>
          </div>
        </div>
      </div>

      {/* Run All Tests Button */}
      <div className="mb-8">
        <button
          onClick={runAllTests}
          disabled={isRunningAll}
          className={`px-6 py-3 rounded-lg font-semibold text-white ${
            isRunningAll
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-blue-600 hover:bg-blue-700'
          } transition-colors`}
        >
          {isRunningAll ? 'Running All Tests...' : 'Run All Tests'}
        </button>
      </div>

      {/* Service Test Results */}
      <div className="grid gap-6">
        {services.map((service) => {
          const result = testResults.find(r => r.service === service.name);

          return (
            <div key={service.name} className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-center mb-4">
                <div>
                  <h3 className="text-xl font-semibold">{service.displayName}</h3>
                  <p className="text-gray-600">Port: {service.port}</p>
                </div>
                <div className="flex items-center space-x-4">
                  <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(result?.status || 'idle')}`}>
                    {getStatusIcon(result?.status || 'idle')} {result?.status || 'idle'}
                  </div>
                  <button
                    onClick={() => runSingleTest(service.name)}
                    disabled={result?.status === 'running'}
                    className={`px-4 py-2 rounded-lg text-sm font-medium ${
                      result?.status === 'running'
                        ? 'bg-gray-400 cursor-not-allowed text-white'
                        : 'bg-green-600 hover:bg-green-700 text-white'
                    } transition-colors`}
                  >
                    {result?.status === 'running' ? 'Running...' : 'Run Tests'}
                  </button>
                </div>
              </div>

              {result && (
                <div className="space-y-4">
                  {result.duration && (
                    <div className="text-sm text-gray-600">
                      Duration: {(result.duration / 1000).toFixed(2)}s
                    </div>
                  )}

                  {result.totalTests !== undefined && (
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div className="text-center">
                        <div className="font-semibold text-blue-600">{result.totalTests}</div>
                        <div className="text-gray-600">Total</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-green-600">{result.passedTests || 0}</div>
                        <div className="text-gray-600">Passed</div>
                      </div>
                      <div className="text-center">
                        <div className="font-semibold text-red-600">{result.failedTests || 0}</div>
                        <div className="text-gray-600">Failed</div>
                      </div>
                    </div>
                  )}

                  {result.output && (
                    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-800 mb-2">Test Output</h4>
                      <pre className="text-gray-700 text-sm whitespace-pre-wrap max-h-60 overflow-y-auto">{result.output}</pre>
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default UnitTestsPage;