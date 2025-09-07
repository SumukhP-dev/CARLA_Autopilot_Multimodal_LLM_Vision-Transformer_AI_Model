import { Component, signal } from '@angular/core';
import { RouterOutlet } from '@angular/router';
import { SimulationsComponent } from './components/simulations/simulations';
import { Header } from './components/header/header';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, SimulationsComponent, Header],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly title = signal('vision-transformer-dashboard');
}
