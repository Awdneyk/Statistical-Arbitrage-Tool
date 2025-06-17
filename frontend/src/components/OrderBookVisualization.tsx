import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import type { OrderBookData } from '../types';

interface OrderBookVisualizationProps {
  data: OrderBookData | null;
  width?: number;
  height?: number;
}

export const OrderBookVisualization: React.FC<OrderBookVisualizationProps> = ({
  data,
  width = 600,
  height = 400
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  
  useEffect(() => {
    if (!data || !svgRef.current) return;
    
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // Prepare data
    const bids = data.bids.map(([price, quantity]) => ({ price, quantity, side: 'bid' }));
    const asks = data.asks.map(([price, quantity]) => ({ price, quantity, side: 'ask' }));
    const allData = [...bids, ...asks];
    
    if (allData.length === 0) return;
    
    // Scales
    const xScale = d3.scaleLinear()
      .domain(d3.extent(allData, d => d.price) as [number, number])
      .range([0, innerWidth]);
    
    const yScale = d3.scaleLinear()
      .domain([0, d3.max(allData, d => d.quantity) || 0])
      .range([innerHeight, 0]);
    
    // Create container
    const container = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Add axes
    container.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(d3.axisBottom(xScale).tickFormat(d => `$${d.toFixed(2)}`));
    
    container.append('g')
      .call(d3.axisLeft(yScale));
    
    // Add axis labels
    container.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (innerHeight / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text('Quantity');
    
    container.append('text')
      .attr('transform', `translate(${innerWidth / 2}, ${innerHeight + margin.bottom})`)
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text('Price ($)');
    
    // Create bars for bids (green)
    container.selectAll('.bid-bar')
      .data(bids)
      .enter()
      .append('rect')
      .attr('class', 'bid-bar')
      .attr('x', d => xScale(d.price))
      .attr('y', d => yScale(d.quantity))
      .attr('width', innerWidth / (bids.length + asks.length) * 0.8)
      .attr('height', d => innerHeight - yScale(d.quantity))
      .attr('fill', '#4ade80')
      .attr('fill-opacity', 0.7)
      .on('mouseover', function(event, d) {
        d3.select(this).attr('fill-opacity', 1);
        
        // Tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'tooltip')
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.8)')
          .style('color', 'white')
          .style('padding', '8px')
          .style('border-radius', '4px')
          .style('font-size', '12px')
          .style('pointer-events', 'none')
          .style('z-index', '1000');
        
        tooltip.html(`
          <div>Price: $${d.price.toFixed(2)}</div>
          <div>Quantity: ${d.quantity}</div>
          <div>Side: BID</div>
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function() {
        d3.select(this).attr('fill-opacity', 0.7);
        d3.selectAll('.tooltip').remove();
      });
    
    // Create bars for asks (red)
    container.selectAll('.ask-bar')
      .data(asks)
      .enter()
      .append('rect')
      .attr('class', 'ask-bar')
      .attr('x', d => xScale(d.price))
      .attr('y', d => yScale(d.quantity))
      .attr('width', innerWidth / (bids.length + asks.length) * 0.8)
      .attr('height', d => innerHeight - yScale(d.quantity))
      .attr('fill', '#ef4444')
      .attr('fill-opacity', 0.7)
      .on('mouseover', function(event, d) {
        d3.select(this).attr('fill-opacity', 1);
        
        // Tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'tooltip')
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.8)')
          .style('color', 'white')
          .style('padding', '8px')
          .style('border-radius', '4px')
          .style('font-size', '12px')
          .style('pointer-events', 'none')
          .style('z-index', '1000');
        
        tooltip.html(`
          <div>Price: $${d.price.toFixed(2)}</div>
          <div>Quantity: ${d.quantity}</div>
          <div>Side: ASK</div>
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function() {
        d3.select(this).attr('fill-opacity', 0.7);
        d3.selectAll('.tooltip').remove();
      });
    
    // Add mid price line if both bids and asks exist
    if (bids.length > 0 && asks.length > 0) {
      const bestBid = Math.max(...bids.map(d => d.price));
      const bestAsk = Math.min(...asks.map(d => d.price));
      const midPrice = (bestBid + bestAsk) / 2;
      
      container.append('line')
        .attr('x1', xScale(midPrice))
        .attr('x2', xScale(midPrice))
        .attr('y1', 0)
        .attr('y2', innerHeight)
        .attr('stroke', '#f59e0b')
        .attr('stroke-width', 2)
        .attr('stroke-dasharray', '5,5');
      
      container.append('text')
        .attr('x', xScale(midPrice))
        .attr('y', -5)
        .attr('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('font-weight', 'bold')
        .style('fill', '#f59e0b')
        .text(`Mid: $${midPrice.toFixed(2)}`);
    }
    
  }, [data, width, height]);
  
  return (
    <div className="order-book-visualization">
      <h3 style={{ textAlign: 'center', margin: '0 0 10px 0' }}>
        Order Book - {data?.symbol || 'Loading...'}
      </h3>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ border: '1px solid #ccc', borderRadius: '4px' }}
      />
      {data && (
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: '10px', fontSize: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', marginRight: '20px' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#4ade80', marginRight: '5px' }}></div>
            Bids
          </div>
          <div style={{ display: 'flex', alignItems: 'center' }}>
            <div style={{ width: '12px', height: '12px', backgroundColor: '#ef4444', marginRight: '5px' }}></div>
            Asks
          </div>
        </div>
      )}
    </div>
  );
};