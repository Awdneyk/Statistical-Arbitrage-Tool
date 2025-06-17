export interface OrderBookLevel {
  price: number;
  quantity: number;
  orderCount: number;
}

export interface OrderBookData {
  type: 'orderbook';
  symbol: string;
  timestamp: number;
  bids: [number, number, number][];
  asks: [number, number, number][];
}

export interface SystemMetrics {
  type: 'metrics';
  timestamp: number;
  cpu_usage: number;
  memory_usage: number;
  network_sent: number;
  network_recv: number;
  orders_processed: number;
  trades_executed: number;
  avg_latency_ns: number;
  min_latency_ns: number;
  max_latency_ns: number;
}

export interface Trade {
  type: 'trade';
  symbol: string;
  price: number;
  quantity: number;
  timestamp: number;
  buy_order_id: number;
  sell_order_id: number;
}

export interface LatencyHistogram {
  buckets: number[];
  counts: number[];
}

export type WebSocketMessage = OrderBookData | SystemMetrics | Trade;