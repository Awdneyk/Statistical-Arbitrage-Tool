import React from 'react';
import { useWebSocket } from './hooks/useWebSocket';
import { OrderBookVisualization } from './components/OrderBookVisualization';
import { LatencyHistogram } from './components/LatencyHistogram';
import { SystemHealthIndicators } from './components/SystemHealthIndicators';
import { TickChart } from './components/TickChart';

const App: React.FC = () => {
  const { orderBook, metrics, trades, connectionStatus } = useWebSocket('ws://localhost:8080');
  
  const connectionStatusColor = {
    connecting: '#f59e0b',
    connected: '#10b981',
    disconnected: '#ef4444'
  };
  
  return (
    <div style={{
      fontFamily: 'system-ui, -apple-system, sans-serif',
      background: '#f8fafc',
      minHeight: '100vh',
      padding: '20px'
    }}>
      {/* Header */}
      <header style={{
        background: 'white',
        padding: '16px 24px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        marginBottom: '24px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}>
        <h1 style={{ margin: 0, color: '#1f2937', fontSize: '24px' }}>
          HFT Trading Dashboard
        </h1>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px'
        }}>
          <div
            style={{
              width: '10px',
              height: '10px',
              borderRadius: '50%',
              backgroundColor: connectionStatusColor[connectionStatus]
            }}
          />
          <span style={{ fontSize: '14px', color: '#6b7280' }}>
            {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
          </span>
        </div>
      </header>
      
      {/* Main Dashboard */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '1fr 1fr',
        gap: '24px',
        marginBottom: '24px'
      }}>
        {/* Order Book */}
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <OrderBookVisualization data={orderBook} width={550} height={400} />
        </div>
        
        {/* Latency Histogram */}
        <div style={{
          background: 'white',
          padding: '20px',
          borderRadius: '8px',
          boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)'
        }}>
          <LatencyHistogram metrics={metrics} width={450} height={300} />
        </div>
      </div>
      
      {/* System Health */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        marginBottom: '24px'
      }}>
        <SystemHealthIndicators metrics={metrics} />
      </div>
      
      {/* 3D Tick Chart */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        display: 'flex',
        justifyContent: 'center'
      }}>
        <TickChart trades={trades} width={800} height={400} />
      </div>
      
      {/* Trade Feed */}
      <div style={{
        background: 'white',
        padding: '20px',
        borderRadius: '8px',
        boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
        marginTop: '24px'
      }}>
        <h3 style={{ margin: '0 0 16px 0' }}>Recent Trades</h3>
        <div style={{
          maxHeight: '200px',
          overflowY: 'auto',
          border: '1px solid #e5e7eb',
          borderRadius: '4px'
        }}>
          {trades.length === 0 ? (
            <div style={{ padding: '20px', textAlign: 'center', color: '#6b7280' }}>
              No trades yet...
            </div>
          ) : (
            <table style={{ width: '100%', fontSize: '12px' }}>
              <thead style={{ background: '#f9fafb', position: 'sticky', top: 0 }}>
                <tr>
                  <th style={{ padding: '8px', textAlign: 'left', borderBottom: '1px solid #e5e7eb' }}>Time</th>
                  <th style={{ padding: '8px', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>Symbol</th>
                  <th style={{ padding: '8px', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>Price</th>
                  <th style={{ padding: '8px', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>Quantity</th>
                  <th style={{ padding: '8px', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>Buy ID</th>
                  <th style={{ padding: '8px', textAlign: 'right', borderBottom: '1px solid #e5e7eb' }}>Sell ID</th>
                </tr>
              </thead>
              <tbody>
                {trades.slice(0, 20).map((trade, index) => (
                  <tr key={`${trade.buy_order_id}-${trade.sell_order_id}-${index}`}>
                    <td style={{ padding: '6px 8px', borderBottom: '1px solid #f3f4f6' }}>
                      {new Date(trade.timestamp / 1000000).toLocaleTimeString()}
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', borderBottom: '1px solid #f3f4f6' }}>
                      {trade.symbol}
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', borderBottom: '1px solid #f3f4f6', fontWeight: 'bold' }}>
                      ${trade.price.toFixed(2)}
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', borderBottom: '1px solid #f3f4f6' }}>
                      {trade.quantity}
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', borderBottom: '1px solid #f3f4f6', fontSize: '10px', color: '#6b7280' }}>
                      {trade.buy_order_id}
                    </td>
                    <td style={{ padding: '6px 8px', textAlign: 'right', borderBottom: '1px solid #f3f4f6', fontSize: '10px', color: '#6b7280' }}>
                      {trade.sell_order_id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
      
      {connectionStatus === 'disconnected' && (
        <div style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          background: '#fee2e2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          padding: '12px 16px',
          boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
          color: '#991b1b'
        }}>
          Connection lost. Attempting to reconnect...
        </div>
      )}
    </div>
  );
};

export default App;