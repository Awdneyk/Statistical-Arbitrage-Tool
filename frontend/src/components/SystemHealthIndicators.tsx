import React from 'react';
import type { SystemMetrics } from '../types';

interface SystemHealthIndicatorsProps {
  metrics: SystemMetrics | null;
}

interface MetricCardProps {
  title: string;
  value: string | number;
  unit?: string;
  status: 'good' | 'warning' | 'critical';
  icon: string;
}

const MetricCard: React.FC<MetricCardProps> = ({ title, value, unit, status, icon }) => {
  const statusColors = {
    good: '#10b981',
    warning: '#f59e0b',
    critical: '#ef4444'
  };
  
  const statusBgColors = {
    good: '#d1fae5',
    warning: '#fef3c7',
    critical: '#fee2e2'
  };
  
  return (
    <div style={{
      background: statusBgColors[status],
      border: `2px solid ${statusColors[status]}`,
      borderRadius: '8px',
      padding: '16px',
      minWidth: '200px',
      display: 'flex',
      alignItems: 'center',
      gap: '12px'
    }}>
      <div style={{
        fontSize: '24px',
        width: '40px',
        height: '40px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: statusColors[status],
        borderRadius: '50%',
        color: 'white'
      }}>
        {icon}
      </div>
      <div>
        <div style={{ fontSize: '14px', color: '#6b7280', marginBottom: '4px' }}>
          {title}
        </div>
        <div style={{ fontSize: '24px', fontWeight: 'bold', color: statusColors[status] }}>
          {value}{unit && <span style={{ fontSize: '16px' }}>{unit}</span>}
        </div>
      </div>
    </div>
  );
};

export const SystemHealthIndicators: React.FC<SystemHealthIndicatorsProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className="system-health">
        <h3 style={{ textAlign: 'center', margin: '0 0 20px 0' }}>
          System Health
        </h3>
        <div style={{ textAlign: 'center', color: '#6b7280' }}>
          Waiting for metrics...
        </div>
      </div>
    );
  }
  
  // Determine status based on thresholds
  const getCpuStatus = (usage: number): 'good' | 'warning' | 'critical' => {
    if (usage > 80) return 'critical';
    if (usage > 60) return 'warning';
    return 'good';
  };
  
  const getMemoryStatus = (bytes: number): 'good' | 'warning' | 'critical' => {
    const mb = bytes / (1024 * 1024);
    if (mb > 1000) return 'critical';
    if (mb > 500) return 'warning';
    return 'good';
  };
  
  const getLatencyStatus = (ns: number): 'good' | 'warning' | 'critical' => {
    const us = ns / 1000;
    if (us > 1000) return 'critical';
    if (us > 500) return 'warning';
    return 'good';
  };
  
  const formatBytes = (bytes: number): string => {
    if (bytes >= 1024 * 1024 * 1024) {
      return (bytes / (1024 * 1024 * 1024)).toFixed(2);
    } else if (bytes >= 1024 * 1024) {
      return (bytes / (1024 * 1024)).toFixed(1);
    } else if (bytes >= 1024) {
      return (bytes / 1024).toFixed(1);
    }
    return bytes.toString();
  };
  
  const getBytesUnit = (bytes: number): string => {
    if (bytes >= 1024 * 1024 * 1024) return 'GB';
    if (bytes >= 1024 * 1024) return 'MB';
    if (bytes >= 1024) return 'KB';
    return 'B';
  };
  
  const formatLatency = (ns: number): string => {
    if (ns >= 1000000) {
      return (ns / 1000000).toFixed(2);
    } else if (ns >= 1000) {
      return (ns / 1000).toFixed(1);
    }
    return ns.toString();
  };
  
  const getLatencyUnit = (ns: number): string => {
    if (ns >= 1000000) return 'ms';
    if (ns >= 1000) return 'μs';
    return 'ns';
  };
  
  return (
    <div className="system-health">
      <h3 style={{ textAlign: 'center', margin: '0 0 20px 0' }}>
        System Health
      </h3>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '20px'
      }}>
        <MetricCard
          title="CPU Usage"
          value={metrics.cpu_usage.toFixed(1)}
          unit="%"
          status={getCpuStatus(metrics.cpu_usage)}
          icon="⚡"
        />
        
        <MetricCard
          title="Memory Usage"
          value={formatBytes(metrics.memory_usage)}
          unit={getBytesUnit(metrics.memory_usage)}
          status={getMemoryStatus(metrics.memory_usage)}
          icon="🧠"
        />
        
        <MetricCard
          title="Avg Latency"
          value={formatLatency(metrics.avg_latency_ns)}
          unit={getLatencyUnit(metrics.avg_latency_ns)}
          status={getLatencyStatus(metrics.avg_latency_ns)}
          icon="⏱️"
        />
      </div>
      
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '20px'
      }}>
        <MetricCard
          title="Orders Processed"
          value={metrics.orders_processed.toLocaleString()}
          status="good"
          icon="📋"
        />
        
        <MetricCard
          title="Trades Executed"
          value={metrics.trades_executed.toLocaleString()}
          status="good"
          icon="💱"
        />
        
        <MetricCard
          title="Network Sent"
          value={formatBytes(metrics.network_sent)}
          unit={getBytesUnit(metrics.network_sent)}
          status="good"
          icon="📤"
        />
      </div>
      
      {/* Latency Summary */}
      <div style={{
        background: '#f9fafb',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
        padding: '16px',
        marginTop: '16px'
      }}>
        <h4 style={{ margin: '0 0 12px 0', color: '#374151' }}>Latency Summary</h4>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '16px',
          fontSize: '14px'
        }}>
          <div>
            <div style={{ color: '#6b7280', marginBottom: '4px' }}>Minimum</div>
            <div style={{ fontWeight: 'bold', color: '#10b981' }}>
              {formatLatency(metrics.min_latency_ns)}{getLatencyUnit(metrics.min_latency_ns)}
            </div>
          </div>
          <div>
            <div style={{ color: '#6b7280', marginBottom: '4px' }}>Average</div>
            <div style={{ fontWeight: 'bold', color: '#3b82f6' }}>
              {formatLatency(metrics.avg_latency_ns)}{getLatencyUnit(metrics.avg_latency_ns)}
            </div>
          </div>
          <div>
            <div style={{ color: '#6b7280', marginBottom: '4px' }}>Maximum</div>
            <div style={{ fontWeight: 'bold', color: '#ef4444' }}>
              {formatLatency(metrics.max_latency_ns)}{getLatencyUnit(metrics.max_latency_ns)}
            </div>
          </div>
        </div>
      </div>
      
      {/* Last Updated */}
      <div style={{
        textAlign: 'center',
        fontSize: '12px',
        color: '#9ca3af',
        marginTop: '16px'
      }}>
        Last updated: {new Date(metrics.timestamp / 1000000).toLocaleTimeString()}
      </div>
    </div>
  );
};