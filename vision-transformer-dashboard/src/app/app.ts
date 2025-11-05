import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { NgxChartsModule } from '@swimlane/ngx-charts';
import { CommonModule } from '@angular/common';
import { CarlaSimulationDashboardComponent } from './components/simulations/simulations';

@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet,
    CarlaSimulationDashboardComponent,
    NgxChartsModule,
    CommonModule,
  ],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly title = signal('vision-transformer-dashboard');
}
