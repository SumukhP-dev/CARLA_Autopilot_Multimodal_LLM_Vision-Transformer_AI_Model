import { ComponentFixture, TestBed } from '@angular/core/testing';
import { CarlaSimulationDashboardComponent } from './simulations';
import { provideNoopAnimations } from '@angular/platform-browser/animations';

beforeEach(async () => {
  await TestBed.configureTestingModule({
    imports: [CarlaSimulationDashboardComponent],
    providers: [provideNoopAnimations()], // ✅ disables animations, no errors
  }).compileComponents();
});
describe('CarlaSimulationDashboardComponent', () => {
  let component: CarlaSimulationDashboardComponent;
  let fixture: ComponentFixture<CarlaSimulationDashboardComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CarlaSimulationDashboardComponent], // since standalone
    }).compileComponents();

    fixture = TestBed.createComponent(CarlaSimulationDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create the component', () => {
    expect(component).toBeTruthy();
  });

  describe('prepareChartData', () => {
    it('should populate barChartData correctly', () => {
      component.prepareChartData();

      expect(component.barChartData.length).toBe(component.environments.length);
      expect(component.barChartData[0].series.length).toBe(2);

      const firstEnv = component.environments[0];
      expect(component.barChartData[0].name).toBe(firstEnv.name);
      expect(component.barChartData[0].series[0].value).toBe(firstEnv.collisions);
      expect(component.barChartData[0].series[1].value).toBe(firstEnv.safeRuns);
    });

    it('should calculate pie chart data correctly', () => {
      component.prepareChartData();
      const collisionsTotal = component.environments.reduce(
        (s: any, e: { collisions: any }) => s + e.collisions,
        0
      );
      const safeRunsTotal = component.environments.reduce(
        (s: any, e: { safeRuns: any }) => s + e.safeRuns,
        0
      );

      expect(
        component.pieChartData.find((d: { name: string }) => d.name === 'Collisions')?.value
      ).toBe(collisionsTotal);
      expect(
        component.pieChartData.find((d: { name: string }) => d.name === 'Safe Runs')?.value
      ).toBe(safeRunsTotal);
    });

    it('should calculate gauge chart data (safety scores)', () => {
      component.prepareChartData();
      const firstEnv = component.environments[0];
      const expectedSafetyScore = Math.round(
        (firstEnv.safeRuns / (firstEnv.collisions + firstEnv.safeRuns)) * 100
      );

      expect(component.gaugeChartData[0].name).toBe(firstEnv.name);
      expect(component.gaugeChartData[0].value).toBe(expectedSafetyScore);
    });
  });

  describe('calculateStatistics', () => {
    it('should calculate totals and overall safety rate', () => {
      component.calculateStatistics();

      const totalCollisions = component.environments.reduce(
        (s: any, e: { collisions: any }) => s + e.collisions,
        0
      );
      const totalSafeRuns = component.environments.reduce(
        (s: any, e: { safeRuns: any }) => s + e.safeRuns,
        0
      );
      const totalSimulations = totalCollisions + totalSafeRuns;
      const expectedSafetyRate = (totalSafeRuns / totalSimulations) * 100;

      expect(component.totalCollisions).toBe(totalCollisions);
      expect(component.totalSafeRuns).toBe(totalSafeRuns);
      expect(component.totalSimulations).toBe(totalSimulations);
      expect(component.overallSafetyRate).toBeCloseTo(expectedSafetyRate, 5);
    });
  });

  describe('getSafetyScore', () => {
    it('should return correct safety score percentage', () => {
      const env = { name: 'Test', collisions: 10, safeRuns: 90 };
      const score = component.getSafetyScore(env);
      expect(score).toBe(90);
    });
  });

  describe('getSafetyClass', () => {
    it('should return "safety-high" for >= 90%', () => {
      expect(component.getSafetyClass(95)).toBe('safety-high');
    });

    it('should return "safety-medium" for >= 70% and < 90%', () => {
      expect(component.getSafetyClass(75)).toBe('safety-medium');
    });

    it('should return "safety-low" for < 70%', () => {
      expect(component.getSafetyClass(60)).toBe('safety-low');
    });
  });

  describe('onSelect', () => {
    it('should log event when onSelect is called', () => {
      spyOn(console, 'log');
      const mockEvent = { name: 'Test' };
      component.onSelect(mockEvent);
      expect(console.log).toHaveBeenCalledWith('Item clicked', mockEvent);
    });
  });
});
