import { CommonModule } from '@angular/common';
import { Component, Input, OnInit, OnDestroy } from '@angular/core';
import { NgxChartsModule, LegendPosition } from '@swimlane/ngx-charts';
import { HttpClient } from '@angular/common/http';
import { interval, Subscription } from 'rxjs';

interface Environment {
  name: string;
  collisions: number;
  safeRuns: number;
}

interface ChartData {
  name: string;
  value: number;
}

interface BarChartData {
  name: string;
  series: ChartData[];
}

@Component({
  selector: 'app-carla-simulation-dashboard',
  standalone: true,
  imports: [CommonModule, NgxChartsModule],
  templateUrl: './simulations.html',
  styleUrls: ['./simulations.scss'],
})
export class CarlaSimulationDashboardComponent implements OnInit, OnDestroy {
  // No default data - only show real simulation data
  environments: Environment[] = [];
  private apiUrl = 'http://localhost:4000/api/simulations';
  private refreshSubscription?: Subscription;

  // Chart data
  barChartData: BarChartData[] = [];
  pieChartData: ChartData[] = [];
  gaugeChartData: ChartData[] = [];

  // Summary statistics
  totalSimulations: number = 0;
  totalCollisions: number = 0;
  totalSafeRuns: number = 0;
  overallSafetyRate: number = 0;

  // Chart options
  showXAxis = true;
  showYAxis = true;
  gradient = false;
  showLegend = true;
  showXAxisLabel = true;
  xAxisLabel = 'Environment';
  showYAxisLabel = true;
  yAxisLabel = 'Count';
  animations = true;
  
  // Pie chart specific options
  legendPosition: LegendPosition = LegendPosition.Below; // Position legend below chart to prevent overflow

  // Color schemes
  colorScheme: any = {
    domain: ['#ff4444', '#44ff44'],
  };

  pieColorScheme: any = {
    domain: ['#ff4444', '#44ff44'],
  };

  gaugeColorScheme = {
    domain: ['#ff4444', '#ffaa00', '#44ff44'],
  };

  constructor(private http: HttpClient) {
    // Start with empty array - will be populated from API
    // Default data only shown if API is unavailable or no real data exists
    this.environments = [];
  }

  ngOnInit(): void {
    this.loadSimulations();
    // Refresh every 2 seconds to show real-time updates
    this.refreshSubscription = interval(2000).subscribe(() => {
      this.loadSimulations();
    });
  }

  ngOnDestroy(): void {
    if (this.refreshSubscription) {
      this.refreshSubscription.unsubscribe();
    }
  }

  loadSimulations(): void {
    this.http.get<Environment[]>(this.apiUrl).subscribe({
      next: (data) => {
        console.log('[Dashboard] Received data from API:', data);
        
        if (data && data.length > 0) {
          // Aggregate data by name (in case of duplicates)
          // Use the latest entry for each simulation name
          const aggregatedData = new Map<string, Environment>();
          
          // Process all entries and keep the latest for each name
          data.forEach((sim) => {
            // Validate data structure
            if (sim && sim.name && typeof sim.collisions === 'number' && typeof sim.safeRuns === 'number') {
              aggregatedData.set(sim.name, { ...sim });
            } else {
              console.warn('[Dashboard] Invalid data structure:', sim);
            }
          });
          
          // Convert map to array
          const uniqueSims = Array.from(aggregatedData.values());
          console.log('[Dashboard] Aggregated unique simulations:', uniqueSims);
          
          // Use only real simulation data from CARLA (no example data)
          this.environments = uniqueSims;
          console.log('[Dashboard] Using only real simulation data:', uniqueSims);
        } else {
          // No data from API - show empty state
          console.log('[Dashboard] No data from API, showing empty state');
          this.environments = [];
        }
        
        console.log('[Dashboard] Final environments:', this.environments);
        this.prepareChartData();
        this.calculateStatistics();
      },
      error: (error) => {
        console.error('[Dashboard] Failed to load simulations from API:', error);
        console.warn('[Dashboard] API unavailable - showing empty state');
        // No default data - only show real simulation data
        this.environments = [];
        this.prepareChartData();
        this.calculateStatistics();
      }
    });
  }

  // Helper to shorten environment names for display
  private shortenName(name: string, maxLength: number = 15): string {
    if (!name) return 'Unknown';
    // If name contains path separators, extract just the map name
    if (name.includes('/')) {
      const parts = name.split('/');
      const mapName = parts[parts.length - 1];
      if (mapName.length <= maxLength) return mapName;
      return mapName.substring(0, maxLength - 3) + '...';
    }
    // If name is too long, truncate it
    if (name.length <= maxLength) return name;
    return name.substring(0, maxLength - 3) + '...';
  }

  prepareChartData(): void {
    try {
      // Prepare bar chart data
      this.barChartData = this.environments.map((env) => {
        // Ensure valid numbers
        const collisions = Math.max(0, env.collisions || 0);
        const safeRuns = Math.max(0, env.safeRuns || 0);
        
        return {
          name: this.shortenName(env.name || 'Unknown', 15), // Shorten for chart display
          series: [
            {
              name: 'Collisions',
              value: collisions,
            },
            {
              name: 'Safe Runs',
              value: safeRuns,
            },
          ],
        };
      });

      // Calculate totals for pie chart
      const totalCollisions = this.environments.reduce((sum, env) => sum + (env.collisions || 0), 0);
      const totalSafeRuns = this.environments.reduce((sum, env) => sum + (env.safeRuns || 0), 0);

      this.pieChartData = [
        {
          name: 'Collisions',
          value: totalCollisions,
        },
        {
          name: 'Safe Runs',
          value: totalSafeRuns,
        },
      ];

      // Prepare gauge data for each environment
      this.gaugeChartData = this.environments.map((env) => {
        const collisions = Math.max(0, env.collisions || 0);
        const safeRuns = Math.max(0, env.safeRuns || 0);
        const total = collisions + safeRuns;
        const safetyScore = total > 0 ? (safeRuns / total) * 100 : 0;
        
        return {
          name: env.name || 'Unknown',
          value: Math.round(safetyScore),
        };
      });
      
      console.log('[Dashboard] Chart data prepared:', {
        barChart: this.barChartData.length,
        pieChart: this.pieChartData,
        gaugeChart: this.gaugeChartData.length
      });
    } catch (error) {
      console.error('[Dashboard] Error preparing chart data:', error);
    }
  }

  calculateStatistics(): void {
    try {
      this.totalCollisions = this.environments.reduce((sum, env) => sum + (env.collisions || 0), 0);
      this.totalSafeRuns = this.environments.reduce((sum, env) => sum + (env.safeRuns || 0), 0);
      this.totalSimulations = this.totalCollisions + this.totalSafeRuns;
      this.overallSafetyRate = this.totalSimulations > 0 
        ? (this.totalSafeRuns / this.totalSimulations) * 100 
        : 0;
      
      console.log('[Dashboard] Statistics calculated:', {
        totalSimulations: this.totalSimulations,
        totalCollisions: this.totalCollisions,
        totalSafeRuns: this.totalSafeRuns,
        overallSafetyRate: this.overallSafetyRate.toFixed(2) + '%'
      });
    } catch (error) {
      console.error('[Dashboard] Error calculating statistics:', error);
    }
  }

  getSafetyScore(env: Environment): number {
    const collisions = Math.max(0, env.collisions || 0);
    const safeRuns = Math.max(0, env.safeRuns || 0);
    const total = collisions + safeRuns;
    
    if (total === 0) {
      return 0; // Avoid division by zero
    }
    
    return Math.round((safeRuns / total) * 100);
  }

  getSafetyClass(score: number): string {
    if (score >= 90) return 'safety-high';
    if (score >= 70) return 'safety-medium';
    return 'safety-low';
  }

  onSelect(event: any): void {
    console.log('Item clicked', event);
  }
}
