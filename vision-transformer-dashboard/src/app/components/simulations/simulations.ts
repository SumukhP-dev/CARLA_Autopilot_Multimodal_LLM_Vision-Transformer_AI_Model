import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { NgxChartsModule, Color, ScaleType } from '@swimlane/ngx-charts';

@Component({
  selector: 'app-carla-simulation-dashboard',
  standalone: true, // ✅ tells Angular this component is self-contained
  imports: [CommonModule, NgxChartsModule],
  templateUrl: './simulations.html',
  styleUrls: ['./simulations.scss'],
})
export class CarlaSimulationDashboardComponent implements OnInit, OnDestroy {
  private refreshInterval: any;
  environments: any[] = [];
  pieColorScheme: Color = {
    name: 'pieColorScheme',
    selectable: true,
    group: ScaleType.Ordinal,
    domain: ['#ef4444', '#34d399'],
  };
  // ✅ Chart color schemes
  greenScheme: Color = {
    name: 'greenScheme',
    selectable: true,
    group: ScaleType.Ordinal,
    domain: ['#34d399'],
  };

  blueScheme: Color = {
    name: 'blueScheme',
    selectable: true,
    group: ScaleType.Ordinal,
    domain: ['#60a5fa'],
  };

  yellowScheme: Color = {
    name: 'yellowScheme',
    selectable: true,
    group: ScaleType.Ordinal,
    domain: ['#fbbf24'],
  };

  redScheme: Color = {
    name: 'redScheme',
    selectable: true,
    group: ScaleType.Ordinal,
    domain: ['#ef4444', '#f97316', '#eab308', '#3b82f6'],
  };

  purpleScheme: Color = {
    name: 'purpleScheme',
    selectable: true,
    group: ScaleType.Ordinal,
    domain: ['#8b5cf6'],
  };

  // Additional color schemes for advanced statistics
  multiColorScheme: Color = {
    name: 'multiColorScheme',
    selectable: true,
    group: ScaleType.Ordinal,
    domain: ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6'],
  };

  greenSingleScheme: Color = {
    name: 'greenSingleScheme',
    selectable: true,
    group: ScaleType.Ordinal,
    domain: ['#22c55e'],
  };

  // ✅ Chart Data (examples)
  totalSimulations = 0;
  totalCollisions = 0;
  totalSafeRuns = 0;
  overallSafetyRate = 0;

  barChartData: any[] = [];
  envStackedData: any[] = [];
  envSafetyScoreData: any[] = [];
  envTotalRunsData: any[] = [];
  gradeLevelData: any[] = [];
  overallGradeLevel = 'N/A';

  // Advanced statistics (graduate CS level)
  avgSpeedData: any[] = [];
  processingTimeData: any[] = [];
  speedVarianceData: any[] = [];
  steeringVarianceData: any[] = [];
  fpsData: any[] = [];
  
  // Overall advanced statistics
  overallSpeedStats: any = {};
  overallSteeringStats: any = {};
  overallProcessingStats: any = {};
  overallFPS = 0;
  overallSpeedCV = 0;
  overallSteeringCV = 0;

  collisionTypeData: any[] = [];

  weatherSafetyData = [
    { name: 'Clear', value: 95 },
    { name: 'Rain', value: 82 },
    { name: 'Fog', value: 78 },
    { name: 'Night', value: 88 },
  ];

  // ✅ Chart layout options
  gradient = false;
  showXAxis = true;
  showYAxis = true;
  animations = true;
  colorScheme = this.blueScheme;
  barView: [number, number] = [700, 300];
  envStackView: [number, number] = [400, 200];
  envSafetyView: [number, number] = [400, 200];
  envTotalView: [number, number] = [400, 200];
  // Compact view sizes for single-screen layout - reduced for better fit
  compactBarView: [number, number] = [280, 140];
  compactView: [number, number] = [250, 120];
  compactPieView: [number, number] = [250, 120];
  
  // Toggle for collapsible table
  toggleTable = false;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadData();
    // Refresh data every 2 seconds
    this.refreshInterval = setInterval(() => {
      this.loadData();
    }, 2000);
  }

  ngOnDestroy(): void {
    if (this.refreshInterval) {
      clearInterval(this.refreshInterval);
    }
  }

  loadData(): void {
    this.http.get<any[]>('http://localhost:4000/api/simulations').subscribe({
      next: (data) => {
        this.environments = data || [];
        this.prepareChartData();
        this.calculateStatistics();
      },
      error: (error) => {
        console.error('Error loading simulation data:', error);
        this.environments = [];
        this.prepareChartData();
        this.calculateStatistics();
      },
    });
  }

  prepareChartData(): void {
    // Ensure environments is always an array
    const envs = this.environments || [];
    
    // Bar chart data - shows safe runs per environment
    this.barChartData = envs.map((env) => ({
      name: env.name || 'Unknown',
      value: env.safeRuns || 0,
    }));
    console.log('barChartData (Safe Runs):', this.barChartData);

    // Stacked data - ensure series is always an array
    this.envStackedData = envs.map((env) => ({
      name: env.name || 'Unknown',
      series: [
        { name: 'Collisions', value: env.collisions || 0 },
        { name: 'Safe Runs', value: env.safeRuns || 0 },
      ],
    }));

    // Safety score data - removed (redundant with summary cards)

    // Total runs data
    this.envTotalRunsData = envs.map((env) => ({
      name: env.name || 'Unknown',
      value: (env.collisions || 0) + (env.safeRuns || 0),
    }));

    // Grade level data
    this.gradeLevelData = envs.map((env) => ({
      name: env.name || 'Unknown',
      value: this.getGradeValue(env.gradeLevel || 'F'),
      label: env.gradeLevel || 'F',
    }));

    // Collision type data - removed (chart no longer displayed)
  }

  calculateStatistics(): void {
    const envs = this.environments || [];
    this.totalCollisions = envs.reduce(
      (sum, env) => sum + (env.collisions || 0),
      0
    );
    this.totalSafeRuns = envs.reduce(
      (sum, env) => sum + (env.safeRuns || 0),
      0
    );
    this.totalSimulations = this.totalCollisions + this.totalSafeRuns;
    this.overallSafetyRate =
      this.totalSimulations > 0
        ? (this.totalSafeRuns / this.totalSimulations) * 100
        : 0;
    
    // Calculate overall grade level
    this.overallGradeLevel = this.calculateGradeLevel(this.overallSafetyRate);
    
    // Calculate advanced statistics
    this.calculateAdvancedStatistics();
  }

  calculateAdvancedStatistics(): void {
    // Ensure environments is always an array
    const envs = this.environments || [];
    
    // Speed statistics
    this.avgSpeedData = envs.map((env) => ({
      name: env.name || 'Unknown',
      value: env.speedStats?.mean || 0,
    }));

    this.speedVarianceData = envs.map((env) => {
      const variance = env.speedStats?.variance || 0;
      return {
        name: env.name || 'Unknown',
        value: variance,
      };
    });
    console.log('speedVarianceData (Speed Variance):', this.speedVarianceData);

    // Steering statistics
    this.steeringVarianceData = envs.map((env) => {
      const variance = env.steeringStats?.variance || 0;
      return {
        name: env.name || 'Unknown',
        value: variance,
      };
    });
    console.log('steeringVarianceData (Steering Variance):', this.steeringVarianceData);

    // Processing time statistics
    this.processingTimeData = envs.flatMap((env) => {
      const procStats = env.processingStats || {};
      const envName = env.name || 'Unknown';
      return [
        { name: `${envName} - Vision`, value: procStats.vision?.mean || 0 },
        { name: `${envName} - Audio`, value: procStats.audio?.mean || 0 },
        { name: `${envName} - LLM`, value: procStats.llm?.mean || 0 },
        { name: `${envName} - Total`, value: procStats.total?.mean || 0 },
      ];
    }).filter(item => item.value > 0); // Only show non-zero values

    // FPS statistics
    this.fpsData = envs.map((env) => {
      const fps = env.avgFPS || 0;
      return {
        name: env.name || 'Unknown',
        value: fps,
      };
    });
    console.log('fpsData (FPS by Environment):', this.fpsData);

    // Calculate overall statistics (weighted averages)
    const totalFrames = envs.reduce(
      (sum, env) => sum + (env.totalFrames || 0),
      0
    );

    if (totalFrames > 0) {
      // Weighted average speed
      const weightedSpeedSum = envs.reduce(
        (sum, env) => sum + (env.speedStats?.mean || 0) * (env.totalFrames || 0),
        0
      );
      const overallSpeedMean = weightedSpeedSum / totalFrames;

      // Weighted average steering
      const weightedSteeringSum = envs.reduce(
        (sum, env) => sum + (env.steeringStats?.mean || 0) * (env.totalFrames || 0),
        0
      );
      const overallSteeringMean = weightedSteeringSum / totalFrames;

      // Calculate overall variance (pooled variance)
      let pooledSpeedVariance = 0;
      let pooledSteeringVariance = 0;
      envs.forEach((env) => {
        const weight = (env.totalFrames || 0) / totalFrames;
        pooledSpeedVariance +=
          weight * ((env.speedStats?.variance || 0) + Math.pow((env.speedStats?.mean || 0) - overallSpeedMean, 2));
        pooledSteeringVariance +=
          weight * ((env.steeringStats?.variance || 0) + Math.pow((env.steeringStats?.mean || 0) - overallSteeringMean, 2));
      });

      this.overallSpeedStats = {
        mean: overallSpeedMean,
        std: Math.sqrt(pooledSpeedVariance),
        variance: pooledSpeedVariance,
      };

      this.overallSteeringStats = {
        mean: overallSteeringMean,
        std: Math.sqrt(pooledSteeringVariance),
        variance: pooledSteeringVariance,
      };

      // Overall FPS (weighted average)
      const weightedFPSSum = envs.reduce(
        (sum, env) => sum + (env.avgFPS || 0) * (env.totalFrames || 0),
        0
      );
      this.overallFPS = weightedFPSSum / totalFrames;

      // Overall processing stats (weighted average)
      const processingKeys = ['vision', 'audio', 'llm', 'total'];
      this.overallProcessingStats = {};
      processingKeys.forEach((key) => {
        const weightedSum = envs.reduce(
          (sum, env) =>
            sum + ((env.processingStats?.[key]?.mean || 0) * (env.totalFrames || 0)),
          0
        );
        this.overallProcessingStats[key] = {
          mean: weightedSum / totalFrames,
        };
      });

      // Coefficient of variation
      this.overallSpeedCV =
        this.overallSpeedStats.mean > 0
          ? (this.overallSpeedStats.std / this.overallSpeedStats.mean) * 100
          : 0;
      this.overallSteeringCV =
        Math.abs(this.overallSteeringStats.mean) > 0
          ? (this.overallSteeringStats.std / Math.abs(this.overallSteeringStats.mean)) * 100
          : 0;
    }
  }

  getSafetyScore(env: any): number {
    const total = (env.collisions || 0) + (env.safeRuns || 0);
    return total > 0 ? Math.round((env.safeRuns / total) * 100) : 0;
  }

  getGradeValue(grade: string): number {
    const gradeMap: { [key: string]: number } = {
      'A+': 97,
      'A': 92,
      'B+': 87,
      'B': 82,
      'C+': 77,
      'C': 72,
      'D+': 67,
      'D': 62,
      'F': 30,
    };
    return gradeMap[grade] || 30;
  }

  calculateGradeLevel(safetyRate: number): string {
    if (safetyRate >= 95) return 'A+';
    if (safetyRate >= 90) return 'A';
    if (safetyRate >= 85) return 'B+';
    if (safetyRate >= 80) return 'B';
    if (safetyRate >= 75) return 'C+';
    if (safetyRate >= 70) return 'C';
    if (safetyRate >= 65) return 'D+';
    if (safetyRate >= 60) return 'D';
    return 'F';
  }

  getGradeColor(grade: string): string {
    const colorMap: { [key: string]: string } = {
      'A+': '#22c55e',
      'A': '#34d399',
      'B+': '#60a5fa',
      'B': '#3b82f6',
      'C+': '#fbbf24',
      'C': '#f59e0b',
      'D+': '#f97316',
      'D': '#ef4444',
      'F': '#dc2626',
    };
    return colorMap[grade] || '#6b7280';
  }

  getGradeColors(): any[] {
    return this.gradeLevelData.map((item) => ({
      name: item.name,
      value: this.getGradeColor(item.label),
    }));
  }

  onSelect(event: any): void {
    console.log('Chart data selected:', event);
  }
}
