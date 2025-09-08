import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { CarlaSimulationDashboardComponent } from './components/simulations/simulations';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, CarlaSimulationDashboardComponent, NgxChartsModule, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly title = signal('vision-transformer-dashboard');
}
