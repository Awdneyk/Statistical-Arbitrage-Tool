import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { SystemMetrics } from '../types';

interface LatencyHistogramProps {
  metrics: SystemMetrics | null;
  width?: number;
  height?: number;
}

interface HistogramData {
  latency: number;
  count: number;
}

export const LatencyHistogram: React.FC<LatencyHistogramProps> = ({
  metrics,
  width = 500,
  height = 300
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const [histogramData, setHistogramData] = useState<HistogramData[]>([]);
  const intervalRef = useRef<NodeJS.Timeout>();
  
  // Simulate histogram data generation (in real implementation, this would come from metrics)
  useEffect(() => {
    if (!metrics) return;
    
    // Generate histogram data based on metrics
    const generateHistogramData = () => {
      const buckets = 20;
      const maxLatency = Math.max(metrics.max_latency_ns / 1000, 1000); // Convert to microseconds
      const data: HistogramData[] = [];
      
      for (let i = 0; i < buckets; i++) {
        const latency = (maxLatency / buckets) * i;
        // Simulate distribution with peak around average latency
        const avgLatencyUs = metrics.avg_latency_ns / 1000;
        const distance = Math.abs(latency - avgLatencyUs);
        const count = Math.max(0, 100 * Math.exp(-distance / (avgLatencyUs * 0.5)) + Math.random() * 20);
        data.push({ latency, count: Math.floor(count) });
      }
      
      return data;
    };
    
    // Update histogram every 100ms
    const updateHistogram = () => {
      setHistogramData(generateHistogramData());
    };
    
    updateHistogram();
    intervalRef.current = setInterval(updateHistogram, 100);
    
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [metrics]);
  
  useEffect(() => {
    if (!histogramData.length || !svgRef.current) return;
    
    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();
    
    const margin = { top: 20, right: 30, bottom: 60, left: 50 };
    const innerWidth = width - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    // Scales
    const xScale = d3.scaleBand()
      .domain(histogramData.map((_, i) => i.toString()))
      .range([0, innerWidth])
      .padding(0.1);
    
    const yScale = d3.scaleLinear()
      .domain([0, d3.max(histogramData, d => d.count) || 0])
      .range([innerHeight, 0]);
    
    // Create container
    const container = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);
    
    // Add bars with animation
    const bars = container.selectAll('.bar')
      .data(histogramData)
      .enter()
      .append('rect')
      .attr('class', 'bar')
      .attr('x', (_, i) => xScale(i.toString()) || 0)
      .attr('width', xScale.bandwidth())
      .attr('y', innerHeight)
      .attr('height', 0)
      .attr('fill', '#3b82f6')
      .attr('fill-opacity', 0.7);
    
    // Animate bars
    bars.transition()
      .duration(200)
      .ease(d3.easeQuadOut)
      .attr('y', d => yScale(d.count))
      .attr('height', d => innerHeight - yScale(d.count));
    
    // Add hover effects
    bars.on('mouseover', function(event, d) {
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
          <div>Latency: ${d.latency.toFixed(1)}μs</div>
          <div>Count: ${d.count}</div>
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function() {
        d3.select(this).attr('fill-opacity', 0.7);
        d3.selectAll('.tooltip').remove();
      });
    
    // Add axes
    const xAxis = d3.axisBottom(xScale)
      .tickFormat((d, i) => {
        const latency = histogramData[parseInt(d)]?.latency || 0;
        return `${latency.toFixed(0)}`;
      });
    
    container.append('g')
      .attr('transform', `translate(0,${innerHeight})`)
      .call(xAxis)
      .selectAll('text')
      .style('font-size', '10px');
    
    container.append('g')
      .call(d3.axisLeft(yScale).ticks(5))
      .selectAll('text')
      .style('font-size', '10px');
    
    // Add axis labels
    container.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 0 - margin.left)
      .attr('x', 0 - (innerHeight / 2))
      .attr('dy', '1em')
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text('Count');
    
    container.append('text')
      .attr('transform', `translate(${innerWidth / 2}, ${innerHeight + margin.bottom - 10})`)
      .style('text-anchor', 'middle')
      .style('font-size', '12px')
      .text('Latency (μs)');
    
    // Add statistics text
    if (metrics) {
      const statsContainer = container.append('g')
        .attr('transform', `translate(${innerWidth - 120}, 20)`);
      
      const stats = [
        `Avg: ${(metrics.avg_latency_ns / 1000).toFixed(1)}μs`,
        `Min: ${(metrics.min_latency_ns / 1000).toFixed(1)}μs`,
        `Max: ${(metrics.max_latency_ns / 1000).toFixed(1)}μs`
      ];
      
      statsContainer.selectAll('.stat-text')
        .data(stats)
        .enter()
        .append('text')
        .attr('class', 'stat-text')
        .attr('x', 0)
        .attr('y', (_, i) => i * 15)
        .style('font-size', '11px')
        .style('fill', '#374151')
        .text(d => d);
    }
    
  }, [histogramData, width, height, metrics]);
  
  return (
    <div className="latency-histogram">
      <h3 style={{ textAlign: 'center', margin: '0 0 10px 0' }}>
        Latency Distribution
      </h3>
      <svg
        ref={svgRef}
        width={width}
        height={height}
        style={{ border: '1px solid #ccc', borderRadius: '4px' }}
      />
      {metrics && (
        <div style={{ textAlign: 'center', marginTop: '10px', fontSize: '12px', color: '#666' }}>
          Updated every 100ms
        </div>
      )}
    </div>
  );
};