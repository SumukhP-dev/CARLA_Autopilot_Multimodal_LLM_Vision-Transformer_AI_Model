import { ComponentFixture, TestBed } from '@angular/core/testing';
import { HttpClientModule } from '@angular/common/http';
import { provideNoopAnimations } from '@angular/platform-browser/animations';
import { CarlaSimulationDashboardComponent } from './simulations';

describe('CarlaSimulationDashboardComponent', () => {
  let component: CarlaSimulationDashboardComponent;
  let fixture: ComponentFixture<CarlaSimulationDashboardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CarlaSimulationDashboardComponent, HttpClientModule],
      providers: [provideNoopAnimations()],
    }).compileComponents();

    fixture = TestBed.createComponent(CarlaSimulationDashboardComponent);
    component = fixture.componentInstance;
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  describe('Component Initialization', () => {
    it('should initialize with empty environments array', () => {
      expect(component.environments).toEqual([]);
    });

    it('should initialize chart data arrays as empty', () => {
      expect(component.barChartData).toEqual([]);
      expect(component.envStackedData).toEqual([]);
      expect(component.envSafetyScoreData).toEqual([]);
      expect(component.gradeLevelData).toEqual([]);
    });

    it('should initialize statistics to zero', () => {
      expect(component.totalSimulations).toBe(0);
      expect(component.totalCollisions).toBe(0);
      expect(component.totalSafeRuns).toBe(0);
      expect(component.overallSafetyRate).toBe(0);
    });

    it('should initialize toggleTable to false', () => {
      expect(component.toggleTable).toBe(false);
    });
  });

  describe('loadData', () => {
    // Note: These tests now use real HTTP calls - backend must be running
    // Skipping HTTP tests to avoid requiring backend during test runs
    it('should initialize loadData method', () => {
      expect(component.loadData).toBeDefined();
      expect(typeof component.loadData).toBe('function');
    });
  });

  describe('prepareChartData', () => {
    beforeEach(() => {
      component.environments = [
        {
          name: 'Env1',
          collisions: 2,
          safeRuns: 98,
          gradeLevel: 'A',
          speedStats: { mean: 5.0 },
          steeringStats: { mean: 0.1 },
        },
        {
          name: 'Env2',
          collisions: 5,
          safeRuns: 95,
          gradeLevel: 'A',
          speedStats: { mean: 6.0 },
          steeringStats: { mean: 0.2 },
        },
      ];
    });

    it('should prepare bar chart data correctly', () => {
      component.prepareChartData();

      expect(component.barChartData.length).toBe(2);
      expect(component.barChartData[0].name).toBe('Env1');
      expect(component.barChartData[0].value).toBe(98);
      expect(component.barChartData[1].name).toBe('Env2');
      expect(component.barChartData[1].value).toBe(95);
    });

    it('should prepare stacked data correctly', () => {
      component.prepareChartData();

      expect(component.envStackedData.length).toBe(2);
      expect(component.envStackedData[0].name).toBe('Env1');
      expect(component.envStackedData[0].series.length).toBe(2);
      expect(component.envStackedData[0].series[0].name).toBe('Collisions');
      expect(component.envStackedData[0].series[0].value).toBe(2);
      expect(component.envStackedData[0].series[1].name).toBe('Safe Runs');
      expect(component.envStackedData[0].series[1].value).toBe(98);
    });

    it('should prepare safety score data correctly', () => {
      component.prepareChartData();

      expect(component.envSafetyScoreData.length).toBe(2);
      expect(component.envSafetyScoreData[0].name).toBe('Env1');
      expect(component.envSafetyScoreData[0].value).toBe(98); // 98/(2+98)*100 = 98
    });

    it('should prepare grade level data correctly', () => {
      component.prepareChartData();

      expect(component.gradeLevelData.length).toBe(2);
      expect(component.gradeLevelData[0].name).toBe('Env1');
      expect(component.gradeLevelData[0].label).toBe('A');
      expect(component.gradeLevelData[0].value).toBe(92); // getGradeValue('A') = 92
    });

    it('should handle empty environments array', () => {
      component.environments = [];
      component.prepareChartData();

      expect(component.barChartData).toEqual([]);
      expect(component.envStackedData).toEqual([]);
    });

    it('should handle environments with missing data', () => {
      component.environments = [
        { name: 'Env1' }, // Missing collisions, safeRuns, etc.
      ];
      component.prepareChartData();

      expect(component.barChartData[0].value).toBe(0);
      expect(component.envStackedData[0].series[0].value).toBe(0);
    });
  });

  describe('calculateStatistics', () => {
    beforeEach(() => {
      component.environments = [
        { collisions: 5, safeRuns: 95 },
        { collisions: 3, safeRuns: 97 },
      ];
    });

    it('should calculate total collisions correctly', () => {
      component.calculateStatistics();
      expect(component.totalCollisions).toBe(8);
    });

    it('should calculate total safe runs correctly', () => {
      component.calculateStatistics();
      expect(component.totalSafeRuns).toBe(192);
    });

    it('should calculate total simulations correctly', () => {
      component.calculateStatistics();
      expect(component.totalSimulations).toBe(200);
    });

    it('should calculate overall safety rate correctly', () => {
      component.calculateStatistics();
      expect(component.overallSafetyRate).toBe(96.0); // 192/200 * 100
    });

    it('should calculate grade level based on safety rate', () => {
      component.calculateStatistics();
      expect(component.overallGradeLevel).toBe('A+'); // 96% >= 95%
    });

    it('should handle zero simulations', () => {
      component.environments = [];
      component.calculateStatistics();
      expect(component.totalSimulations).toBe(0);
      expect(component.overallSafetyRate).toBe(0);
    });
  });

  describe('calculateAdvancedStatistics', () => {
    beforeEach(() => {
      component.environments = [
        {
          name: 'Env1',
          speedStats: { mean: 5.0, variance: 1.0 },
          steeringStats: { mean: 0.1, variance: 0.01 },
          avgFPS: 30.0,
          totalFrames: 1000,
          processingStats: {
            vision: { mean: 0.1 },
            audio: { mean: 0.2 },
            llm: { mean: 0.3 },
            total: { mean: 0.6 },
          },
        },
        {
          name: 'Env2',
          speedStats: { mean: 6.0, variance: 1.5 },
          steeringStats: { mean: 0.2, variance: 0.02 },
          avgFPS: 25.0,
          totalFrames: 500,
          processingStats: {
            vision: { mean: 0.15 },
            audio: { mean: 0.25 },
            llm: { mean: 0.35 },
            total: { mean: 0.75 },
          },
        },
      ];
    });

    it('should calculate average speed data', () => {
      component.calculateAdvancedStatistics();
      expect(component.avgSpeedData.length).toBe(2);
      expect(component.avgSpeedData[0].name).toBe('Env1');
      expect(component.avgSpeedData[0].value).toBe(5.0);
    });

    it('should calculate speed variance data', () => {
      component.calculateAdvancedStatistics();
      expect(component.speedVarianceData.length).toBe(2);
      expect(component.speedVarianceData[0].value).toBe(1.0);
    });

    it('should calculate steering variance data', () => {
      component.calculateAdvancedStatistics();
      expect(component.steeringVarianceData.length).toBe(2);
      expect(component.steeringVarianceData[0].value).toBe(0.01);
    });

    it('should calculate FPS data', () => {
      component.calculateAdvancedStatistics();
      expect(component.fpsData.length).toBe(2);
      expect(component.fpsData[0].value).toBe(30.0);
    });

    it('should calculate processing time data', () => {
      component.calculateAdvancedStatistics();
      expect(component.processingTimeData.length).toBe(8); // 2 envs * 4 processing types
    });

    it('should calculate overall statistics with weighted averages', () => {
      component.calculateAdvancedStatistics();
      // Weighted average: (5.0*1000 + 6.0*500) / 1500 = 5.33
      expect(component.overallSpeedStats.mean).toBeCloseTo(5.33, 2);
    });

    it('should handle empty environments', () => {
      component.environments = [];
      component.calculateAdvancedStatistics();
      expect(component.avgSpeedData).toEqual([]);
      expect(component.overallSpeedStats).toEqual({});
    });
  });

  describe('getSafetyScore', () => {
    it('should calculate safety score correctly', () => {
      const env = { collisions: 5, safeRuns: 95 };
      const score = component.getSafetyScore(env);
      expect(score).toBe(95); // 95/(5+95)*100 = 95
    });

    it('should return 0 for zero total runs', () => {
      const env = { collisions: 0, safeRuns: 0 };
      const score = component.getSafetyScore(env);
      expect(score).toBe(0);
    });

    it('should handle missing collisions', () => {
      const env = { safeRuns: 100 };
      const score = component.getSafetyScore(env);
      expect(score).toBe(100);
    });
  });

  describe('getGradeValue', () => {
    it('should return correct value for A+', () => {
      expect(component.getGradeValue('A+')).toBe(97);
    });

    it('should return correct value for A', () => {
      expect(component.getGradeValue('A')).toBe(92);
    });

    it('should return correct value for F', () => {
      expect(component.getGradeValue('F')).toBe(30);
    });

    it('should return default value for unknown grade', () => {
      expect(component.getGradeValue('X')).toBe(30);
    });
  });

  describe('calculateGradeLevel', () => {
    it('should return A+ for >= 95%', () => {
      expect(component.calculateGradeLevel(95)).toBe('A+');
      expect(component.calculateGradeLevel(100)).toBe('A+');
    });

    it('should return A for >= 90% and < 95%', () => {
      expect(component.calculateGradeLevel(90)).toBe('A');
      expect(component.calculateGradeLevel(94)).toBe('A');
    });

    it('should return F for < 60%', () => {
      expect(component.calculateGradeLevel(59)).toBe('F');
      expect(component.calculateGradeLevel(0)).toBe('F');
    });
  });

  describe('getGradeColor', () => {
    it('should return correct color for A+', () => {
      expect(component.getGradeColor('A+')).toBe('#22c55e');
    });

    it('should return correct color for F', () => {
      expect(component.getGradeColor('F')).toBe('#dc2626');
    });

    it('should return default color for unknown grade', () => {
      expect(component.getGradeColor('X')).toBe('#6b7280');
    });
  });

  describe('getGradeColors', () => {
    it('should return grade colors for grade level data', () => {
      component.gradeLevelData = [
        { name: 'Env1', label: 'A', value: 92 },
        { name: 'Env2', label: 'B', value: 82 },
      ];

      const colors = component.getGradeColors();
      expect(colors.length).toBe(2);
      expect(colors[0].name).toBe('Env1');
      expect(colors[0].value).toBe('#34d399'); // A color
    });

    it('should handle empty grade level data', () => {
      component.gradeLevelData = [];
      const colors = component.getGradeColors();
      expect(colors).toEqual([]);
    });
  });

  describe('onSelect', () => {
    it('should log selected event', () => {
      spyOn(console, 'log');
      const mockEvent = { name: 'Test Event' };
      component.onSelect(mockEvent);
      expect(console.log).toHaveBeenCalledWith('Chart data selected:', mockEvent);
    });
  });

  describe('ngOnInit and ngOnDestroy', () => {
    it('should load data on init', () => {
      spyOn(component, 'loadData');
      component.ngOnInit();
      expect(component.loadData).toHaveBeenCalled();
    });

    it('should set up refresh interval on init', () => {
      component.ngOnInit();
      expect(component['refreshInterval']).toBeDefined();
    });

    it('should clear interval on destroy', () => {
      component.ngOnInit();
      const intervalId = component['refreshInterval'];
      spyOn(window, 'clearInterval');
      component.ngOnDestroy();
      expect(window.clearInterval).toHaveBeenCalled();
    });

    it('should handle destroy when no interval exists', () => {
      component['refreshInterval'] = null;
      expect(() => component.ngOnDestroy()).not.toThrow();
    });
  });

  describe('Edge Cases', () => {
    it('should handle null/undefined environment data', () => {
      component.environments = [null, undefined, { name: 'Valid' }] as any;
      expect(() => component.prepareChartData()).not.toThrow();
    });

    it('should handle very large numbers', () => {
      component.environments = [{ collisions: 1000000, safeRuns: 2000000 }];
      component.calculateStatistics();
      expect(component.totalSimulations).toBe(3000000);
    });

    it('should handle negative values gracefully', () => {
      component.environments = [{ collisions: -5, safeRuns: 95 }];
      component.calculateStatistics();
      // Should still calculate, though negative collisions don't make sense
      expect(component.totalCollisions).toBe(-5);
    });
  });
});
