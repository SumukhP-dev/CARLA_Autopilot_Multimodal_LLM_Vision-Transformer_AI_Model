import { CommonModule } from '@angular/common';
import { Component, Input, OnInit } from '@angular/core';
import { NgxChartsModule } from '@swimlane/ngx-charts';

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
export class CarlaSimulationDashboardComponent implements OnInit {
  @Input() environments: Environment[] = [
    { name: 'Urban', collisions: 12, safeRuns: 88 },
    { name: 'Highway', collisions: 5, safeRuns: 95 },
    { name: 'Rural', collisions: 8, safeRuns: 92 },
    { name: 'Parking', collisions: 15, safeRuns: 85 },
    { name: 'Night', collisions: 20, safeRuns: 80 },
  ];

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

  ngOnInit(): void {
    this.prepareChartData();
    this.calculateStatistics();
  }

  prepareChartData(): void {
    // Prepare bar chart data
    this.barChartData = this.environments.map((env) => ({
      name: env.name,
      series: [
        {
          name: 'Collisions',
          value: env.collisions,
        },
        {
          name: 'Safe Runs',
          value: env.safeRuns,
        },
      ],
    }));

    // Calculate totals for pie chart
    const totalCollisions = this.environments.reduce((sum, env) => sum + env.collisions, 0);
    const totalSafeRuns = this.environments.reduce((sum, env) => sum + env.safeRuns, 0);

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
      const total = env.collisions + env.safeRuns;
      const safetyScore = (env.safeRuns / total) * 100;
      return {
        name: env.name,
        value: Math.round(safetyScore),
      };
    });
  }

  calculateStatistics(): void {
    this.totalCollisions = this.environments.reduce((sum, env) => sum + env.collisions, 0);
    this.totalSafeRuns = this.environments.reduce((sum, env) => sum + env.safeRuns, 0);
    this.totalSimulations = this.totalCollisions + this.totalSafeRuns;
    this.overallSafetyRate = (this.totalSafeRuns / this.totalSimulations) * 100;
  }

  getSafetyScore(env: Environment): number {
    const total = env.collisions + env.safeRuns;
    return Math.round((env.safeRuns / total) * 100);
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
